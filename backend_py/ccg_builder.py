import os
import ast
import networkx as nx

try:
    from tree_sitter import Parser
    from tree_sitter_languages import get_language
    HAVE_TREESITTER = True
except Exception:
    HAVE_TREESITTER = False

SUPPORTED_CODE_EXT = {".py", ".jac"} 


def _is_code_file(path: str) -> bool:
    _, ext = os.path.splitext(path)
    return ext in SUPPORTED_CODE_EXT


def _collect_python_info(file_path: str):
    """
    Parse a Python file using ast.
    Extract:
      - classes and base classes
      - top-level functions
      - methods and their calls
      - module imports
    Returns dict:
    {
        "classes": [
            {"name":"Session","bases":["object","HTTPAdapter"],"methods":["request","get",...]},
            ...
        ],
        "functions": [
            {"name":"send_request","calls":["do_send","log"]},
            ...
        ],
        "imports": ["requests.adapters","http.client", ...],
        "calls": [("Session.request","dispatch.send"), ...]
    }
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        src = f.read()
    try:
        tree = ast.parse(src, filename=file_path)
    except Exception:
        return {
            "classes": [],
            "functions": [],
            "imports": [],
            "calls": [],
        }

    classes = []
    functions = []
    imports = []
    calls = []

    class CallVisitor(ast.NodeVisitor):
        def __init__(self):
            self.calls = []

        def visit_Call(self, node: ast.Call):
            callee = None
            if isinstance(node.func, ast.Name):
                callee = node.func.id  # foo()
            elif isinstance(node.func, ast.Attribute):
                # obj.method
                callee = node.func.attr
            if callee:
                self.calls.append(callee)
            self.generic_visit(node)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)  
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            imports.append(mod)

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            base_names = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    base_names.append(base.id)
                elif isinstance(base, ast.Attribute):
                    base_names.append(base.attr)
                else:
                    base_names.append("<expr>")
            method_names = []
            for sub in node.body:
                if isinstance(sub, ast.FunctionDef):
                    method_names.append(sub.name)
                    cv = CallVisitor()
                    cv.visit(sub)
                    for c in cv.calls:
                        calls.append((f"{node.name}.{sub.name}", c))
            classes.append({
                "name": node.name,
                "bases": base_names,
                "methods": method_names,
            })

        elif isinstance(node, ast.FunctionDef):
            cv = CallVisitor()
            cv.visit(node)
            functions.append({
                "name": node.name,
                "calls": list(cv.calls),
            })
            for c in cv.calls:
                calls.append((node.name, c))

    return {
        "classes": classes,
        "functions": functions,
        "imports": list(sorted(set(imports))),
        "calls": calls,
    }


def _collect_jac_info(file_path: str):
    """
    Very light Jac parsing for now.
    In final work you'd run Tree-sitter with a Jac grammar or write a mini parser.
    We'll just scan for 'walker NAME' and 'node NAME' patterns to extract symbols.
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    walkers = []
    nodes = []

    for line in lines:
        line_strip = line.strip()
        if line_strip.startswith("walker "):
            parts = line_strip.split()
            if len(parts) >= 2:
                walkers.append(parts[1])
        if line_strip.startswith("node "):
            parts = line_strip.split()
            if len(parts) >= 2:
                nodes.append(parts[1])

    return {
        "jac_walkers": walkers,
        "jac_nodes": nodes,
    }


def analyze_repo(repo_root: str, repo_name: str) -> dict:
    """
    Walk the cloned repo and build:
    - CCG stats
    - call graph edges
    - inheritance edges
    - module dependency edges
    - plus some diagrams in Mermaid format
    """
    G_calls = nx.DiGraph()       
    G_inherit = nx.DiGraph()      
    G_module = nx.DiGraph()       

    symbol_count = 0
    rel_count = 0
    files_scanned = 0

    per_file_info = []

    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in {"__pycache__", ".git", "node_modules", ".venv", "venv"}]

        for f in files:
            if f.startswith("."):
                continue

            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, repo_root)

            if not _is_code_file(full_path):
                continue

            files_scanned += 1

            if full_path.endswith(".py"):
                info = _collect_python_info(full_path)

                module_name = rel_path.replace(os.sep, ".")
                for imported in info["imports"]:
                    if imported:
                        G_module.add_edge(module_name, imported)

                for cls in info["classes"]:
                    symbol_count += 1
                    class_name = cls["name"]
                    if class_name not in G_inherit:
                        G_inherit.add_node(class_name)
                    for base in cls["bases"]:
                        if base:
                            G_inherit.add_node(base)
                            G_inherit.add_edge(base, class_name)
                            rel_count += 1

                    for meth in cls["methods"]:
                        G_calls.add_node(f"{class_name}.{meth}")
                        symbol_count += 1

                for fn in info["functions"]:
                    symbol_count += 1
                    G_calls.add_node(fn["name"])

                for caller, callee in info["calls"]:
                    if caller not in G_calls:
                        G_calls.add_node(caller)
                    if callee not in G_calls:
                        G_calls.add_node(callee)
                    G_calls.add_edge(caller, callee)
                    rel_count += 1

                per_file_info.append({
                    "path": rel_path,
                    "lang": "python",
                    "classes": info["classes"],
                    "functions": info["functions"],
                    "imports": info["imports"],
                })

            elif full_path.endswith(".jac"):
                info = _collect_jac_info(full_path)
                for w in info["jac_walkers"]:
                    symbol_count += 1
                    G_calls.add_node(w)
                for n in info["jac_nodes"]:
                    symbol_count += 1
                    G_calls.add_node(n)

                per_file_info.append({
                    "path": rel_path,
                    "lang": "jac",
                    "jac_walkers": info["jac_walkers"],
                    "jac_nodes": info["jac_nodes"],
                })

    mermaid_module_graph = _to_mermaid_module_graph(G_module)
    mermaid_inherit_graph = _to_mermaid_inherit_graph(G_inherit)
    mermaid_request_flow = _to_mermaid_request_flow(G_calls)

    return {
        "ok": True,
        "ccg_stats": {
            "files_scanned": files_scanned,
            "symbols_found": symbol_count,
            "relations_found": rel_count,
        },
        "per_file_info": per_file_info,
        "diagrams": {
            "module_dependency": mermaid_module_graph,
            "class_inheritance": mermaid_inherit_graph,
            "request_flow": mermaid_request_flow,
        },
    }


def _to_mermaid_module_graph(G_module: nx.DiGraph) -> str:
    """
    Mermaid graph of module dependencies:
    module_a --> module_b  if a imports b
    """
    lines = ["```mermaid", "graph LR;"]
    for src, dst in G_module.edges():
        lines.append(f'  "{src}" --> "{dst}";')
    lines.append("```")
    return "\n".join(lines)

def _to_mermaid_inherit_graph(G_inherit: nx.DiGraph) -> str:
    """
    Mermaid inheritance graph:
    Base --> Derived
    """
    lines = ["```mermaid", "graph TD;"]
    for base, child in G_inherit.edges():
        lines.append(f'  "{base}" --> "{child}";')
    lines.append("```")
    return "\n".join(lines)

def _to_mermaid_request_flow(G_calls: nx.DiGraph) -> str:
    """
    Mermaid call graph rooted around 'request' / 'Session' style flows.
    We try to show the main HTTP request pipeline.
    """
    lines = ["```mermaid", "graph TD;"]
    for caller, callee in G_calls.edges():
        if "request" in caller.lower() or "session" in caller.lower():
            lines.append(f'  "{caller}" --> "{callee}";')
    lines.append("```")
    return "\n".join(lines)


def run_code_analyzer(repo_root: str, repo_name: str) -> dict:
    """
    High-level Code Analyzer pipeline step.
    Uses analyze_repo() to build the CCG and produce diagrams.
    """
    try:
        analysis = analyze_repo(repo_root, repo_name)
        analysis["repo_name"] = repo_name
        return analysis
    except Exception as e:
        return {
            "ok": False,
            "error": f"analyze_repo failed: {e}",
            "stage": "code_analyzer",
        }
