import ast
import re
from pathlib import Path
import networkx as nx

SUPPORTED_EXTS = [".py", ".jac", ".js", ".ts"]

def list_source_files(root_dir: str):
    paths = []
    for p in Path(root_dir).rglob("*"):
        if p.is_file() and p.suffix in SUPPORTED_EXTS:
            if any(seg in [".git","node_modules","__pycache__","venv",".venv"] for seg in p.parts):
                continue
            paths.append(p)
    return paths


class PyVisitor(ast.NodeVisitor):
    def __init__(self, file_path):
        self.file_path = str(file_path)
        self.funcs = []
        self.classes = []
        self.calls = []
        self.current = "module"

    def visit_FunctionDef(self, node):
        sid = f"{node.name}@{node.lineno}"
        self.funcs.append({
            "id": sid,
            "name": node.name,
            "lineno": node.lineno,
            "doc": ast.get_docstring(node) or "",
            "file": self.file_path,
            "type": "function"
        })
        prev = self.current
        self.current = sid
        self.generic_visit(node)
        self.current = prev

    def visit_AsyncFunctionDef(self, node):
        return self.visit_FunctionDef(node)

    def visit_ClassDef(self, node):
        bases = []
        for b in node.bases:
            try:
                bases.append(ast.unparse(b))
            except Exception:
                bases.append(getattr(b, "id", str(b)))
        sid = f"class:{node.name}@{node.lineno}"
        self.classes.append({
            "id": sid,
            "name": node.name,
            "lineno": node.lineno,
            "bases": bases,
            "doc": ast.get_docstring(node) or "",
            "file": self.file_path,
            "type": "class"
        })
        prev = self.current
        self.current = sid
        self.generic_visit(node)
        self.current = prev

    def visit_Call(self, node):
        callee = None
        if hasattr(node.func, "attr"):
            callee = node.func.attr
        elif hasattr(node.func, "id"):
            callee = node.func.id
        if callee:
            self.calls.append({
                "caller": self.current,
                "callee": callee,
                "lineno": node.lineno
            })
        self.generic_visit(node)

def analyze_python(file_path: Path):
    try:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(text)
    except Exception:
        return {"nodes": [], "edges": []}
    v = PyVisitor(file_path)
    v.visit(tree)

    nodes = v.funcs + v.classes
    edges = []
    name_to_id = {n["name"]: n["id"] for n in nodes}
    for c in v.calls:
        if c["callee"] in name_to_id:
            edges.append({
                "source": c["caller"],
                "target": name_to_id[c["callee"]],
                "type": "calls",
                "lineno": c["lineno"]
            })
    return {"nodes": nodes, "edges": edges}

def analyze_jac_or_js(file_path: Path):
    """
    Regex fallback for Jac and JS/TS:
    - walker <name>(...)  (Jac)
    - node <Name> {...}   (Jac)
    - function <name>(...) (JS/TS)
    """
    try:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return {"nodes": [], "edges": []}

    nodes = []
    edges = []

    # Jac walker
    for m in re.finditer(r"walker\s+([A-Za-z0-9_]+)\s*\(", text):
        nm = m.group(1)
        sid = f"walker:{nm}@{m.start()}"
        nodes.append({
            "id": sid,
            "name": nm,
            "lineno": 0,
            "doc": "",
            "file": str(file_path),
            "type": "walker"
        })

    for m in re.finditer(r"node\s+([A-Za-z0-9_]+)\s*{", text):
        nm = m.group(1)
        sid = f"node:{nm}@{m.start()}"
        nodes.append({
            "id": sid,
            "name": nm,
            "lineno": 0,
            "doc": "",
            "file": str(file_path),
            "type": "node"
        })

    for m in re.finditer(r"function\s+([A-Za-z0-9_]+)\s*\(", text):
        nm = m.group(1)
        sid = f"function:{nm}@{m.start()}"
        nodes.append({
            "id": sid,
            "name": nm,
            "lineno": 0,
            "doc": "",
            "file": str(file_path),
            "type": "function"
        })

    return {"nodes": nodes, "edges": edges}

def build_ccg_graph(local_path: str):
    """
    Walk all source files, merge them into one call graph.
    """
    files = list_source_files(local_path)
    G = nx.DiGraph()

    for f in files:
        if f.suffix == ".py":
            info = analyze_python(f)
        else:
            info = analyze_jac_or_js(f)

        for n in info["nodes"]:
            G.add_node(n["id"], **n)
        for e in info["edges"]:
            G.add_edge(e["source"], e["target"], **e)

    nodes_out = []
    edges_out = []

    for nid, data in G.nodes(data=True):
        record = {"id": nid}
        record.update(data)
        nodes_out.append(record)

    for src, dst, data in G.edges(data=True):
        rel = {"source": src, "target": dst}
        rel.update(data)
        edges_out.append(rel)

    stats = {
        "files_scanned": len(files),
        "symbols_found": len(nodes_out),
        "relations_found": len(edges_out),
    }

    return {
        "graph": {"nodes": nodes_out, "edges": edges_out},
        "stats": stats
    }
