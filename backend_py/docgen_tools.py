import os
from textwrap import indent

def generate_docs(repo_name: str,
                  readme_summary: str,
                  file_tree: list[str],
                  ccg_stats: dict,
                  diagrams: dict,
                  project_root: str = "agentic_codebase_genius") -> dict:
    """
    Build docs.md content and save it under outputs/<repo_name>/docs.md.
    Returns { ok, docs_path, preview }.
    """

    base_out = os.path.join(
        os.path.expanduser("~"),
        project_root,
        "outputs",
        repo_name,
    )
    os.makedirs(base_out, exist_ok=True)

    docs_path = os.path.join(base_out, "docs.md")

    file_tree_block = "\n".join(f"- `{p}`" for p in file_tree[:60])  # truncate long trees

    md_lines = []

    md_lines.append(f"# {repo_name} — Codebase Genius documentation\n")
    md_lines.append("## 1. Project Overview\n")
    md_lines.append(readme_summary.strip() or "No README summary available.")
    md_lines.append("\n")

    md_lines.append("## 2. Repository Structure\n")
    md_lines.append("The following file tree shows the key files in this project:\n")
    md_lines.append(file_tree_block)
    md_lines.append("\n")

    md_lines.append("## 3. Code Context Graph (CCG) Stats\n")
    md_lines.append(f"- Files scanned: {ccg_stats.get('files_scanned','-')}")
    md_lines.append(f"- Symbols found: {ccg_stats.get('symbols_found','-')}")
    md_lines.append(f"- Relationships found: {ccg_stats.get('relations_found','-')}")
    md_lines.append("\n")

    md_lines.append("## 4. Architecture Diagrams\n")
    md_lines.append("### 4.1 Module Dependency Graph\n")
    md_lines.append(diagrams.get("module_dependency",""))
    md_lines.append("\n")

    md_lines.append("### 4.2 Class Inheritance Graph\n")
    md_lines.append(diagrams.get("class_inheritance",""))
    md_lines.append("\n")

    md_lines.append("### 4.3 Request / Call Flow\n")
    md_lines.append("This flow highlights how request-handling methods call downstream helpers:\n")
    md_lines.append(diagrams.get("request_flow",""))
    md_lines.append("\n")

    md_lines.append("## 5. How to Use\n")
    md_lines.append("- Install requirements\n- Import the module\n- Call its public APIs\n")
    md_lines.append("\n")

    md_lines.append("## 6. API Reference (high-level)\n")
    md_lines.append("This section would list major classes and functions discovered in analysis.\n")
    md_lines.append("(Future work: auto-expand from `per_file_info`.)\n")

    preview_text = "\n".join(md_lines)

    with open(docs_path, "w", encoding="utf-8") as f:
        f.write(preview_text)

    return {
        "ok": True,
        "docs_path": docs_path,
        "preview": preview_text,
    }


def run_docgen(repo_name: str,
               readme_summary: str,
               file_tree: list[str],
               analysis: dict,
               project_root: str = "agentic_codebase_genius") -> dict:
    """
    High-level DocGenie step.
    Takes RepoMapper & CodeAnalyzer outputs and produces docs.md.
    """
    if not analysis.get("ok", True):
        return {
            "ok": False,
            "stage": "docgenie",
            "error": analysis.get("error","missing analysis"),
        }

    return generate_docs(
        repo_name=repo_name,
        readme_summary=readme_summary,
        file_tree=file_tree,
        ccg_stats=analysis["ccg_stats"],
        diagrams=analysis["diagrams"],
        project_root=project_root,
    )
