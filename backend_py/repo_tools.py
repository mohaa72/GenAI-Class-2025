import os
import shutil
from git import Repo  
from pathlib import Path

IGNORE_DIRS = {}


def safe_repo_name_from_url(repo_url: str) -> str:
    # e.g. "https://github.com/psf/requests" -> "requests"
    tail = repo_url.rstrip("/").split("/")[-1]
    if tail.endswith(".git"):
        tail = tail[:-4]
    return tail or "repo"


def clone_repo(repo_url: str, base_output_dir: str) -> dict:
    try:
        repo_name = safe_repo_name_from_url(repo_url)

        repo_root = os.path.join(
            os.path.expanduser("~"),
            base_output_dir,
            "outputs",
            repo_name,
            "repo_clone",
        )

        if os.path.isdir(repo_root):
            shutil.rmtree(repo_root)

        os.makedirs(repo_root, exist_ok=True)

        Repo.clone_from(repo_url, repo_root, depth=1)

        return {
            "ok": True,
            "repo_name": repo_name,
            "repo_root": repo_root,
        }

    except Exception as e:
        return {
            "ok": False,
            "error": f"clone_repo failed: {e}",
        }


def build_file_tree(repo_root: str) -> list[str]:
    """
    Walk repo_root and build a simple file tree listing.
    Skip junk/hidden dirs.
    Returns a flat list of relative paths like:
      ["app.py", "core/", "core/db.py", ...]
    """
    tree_list = []
    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [
            d
            for d in dirs
            if d not in IGNORE_DIRS and not d.startswith(".")
        ]

        rel_root = os.path.relpath(root, repo_root)
        if rel_root == ".":
            rel_root = ""  
        for d in dirs:
            path_repr = os.path.join(rel_root, d) if rel_root else d
            tree_list.append(path_repr + "/")

        for f in files:
            if f.startswith("."):
                continue
            f_rel = os.path.join(rel_root, f) if rel_root else f
            tree_list.append(f_rel)

    tree_list_sorted = sorted(set(tree_list))
    return tree_list_sorted


def summarize_readme(repo_root: str, max_lines: int = 12) -> str:
    """
    Grab README.* and return first N non-empty lines.
    """
    candidates = [
        "README.md",
        "readme.md",
        "README.rst",
        "README.txt",
    ]

    for cand in candidates:
        full = os.path.join(repo_root, cand)
        if os.path.isfile(full):
            try:
                with open(full, "r", encoding="utf-8", errors="ignore") as f:
                    lines = [ln.strip() for ln in f.readlines()]
                non_empty = [ln for ln in lines if ln.strip()]
                head = non_empty[:max_lines]
                return "\n".join(head)
            except Exception:
                continue

    return "No README summary available."


def detect_entrypoints(repo_root: str) -> list[str]:
    """
    Heuristics for likely 'main app' entrypoints.
    We only look shallow (top level and 1 dir down) so UI doesn't spam.
    """
    interesting_names = {
        "main.py",
        "app.py",
        "server.py",
        "run.py",
        "manage.py",
        "__main__.py",
    }

    results = []
    root_path = Path(repo_root)

    for p in root_path.rglob("*.py"):
        rel = p.relative_to(root_path)
        depth = len(rel.parts)
        if depth <= 2:
            if p.name in interesting_names:
                results.append(str(rel))

    if not results:
        results.append("[no obvious entrypoint found]")
    return sorted(dict.fromkeys(results))  # de-dupe while keeping order


def summarize_repo_overview(repo_root: str) -> str:
    """
    High-level directory summary:
    - list top-level dirs and guess their roles (api, service, models, utils, tests, etc.)
    - also mention interesting top-level files
    """
    parts = []
    for item in sorted(Path(repo_root).iterdir(), key=lambda x: x.name.lower()):
        # skip ignored stuff
        if item.name in IGNORE_DIRS:
            continue
        if item.name.startswith("."):
            continue

        if item.is_dir():
            guess = ""
            low = item.name.lower()
            if "api" in low or "endpoint" in low or "route" in low:
                guess = " (API / routes)"
            elif "service" in low or "svc" in low:
                guess = " (business logic / services)"
            elif "model" in low or "schema" in low or "entity" in low:
                guess = " (data models / schemas)"
            elif "util" in low or "helper" in low or "common" in low:
                guess = " (utilities / helpers)"
            elif "test" in low:
                guess = " (tests)"
            elif "doc" in low:
                guess = " (docs / specs)"
            parts.append(f"- {item.name}/ {guess}")
        else:
            # show interesting individual files like docker-compose, pyproject, etc.
            if item.suffix in [".py", ".md", ".toml", ".yaml", ".yml", ".json"]:
                parts.append(f"- {item.name}")

    if not parts:
        return "[Could not summarise repo layout]"
    return "\n".join(parts)


def run_repo_mapper(repo_url: str, project_root: str = "agentic_codebase_genius") -> dict:
    """
    High-level Repo Mapper pipeline step.
    1. clone
    2. build file tree
    3. summarize readme
    4. detect entrypoints
    5. summarize repo layout
    """
    clone_res = clone_repo(repo_url, project_root)
    if not clone_res["ok"]:
        return {
            "ok": False,
            "error": clone_res["error"],
            "stage": "repo_mapper.clone",
        }

    repo_name = clone_res["repo_name"]
    repo_root = clone_res["repo_root"]

    file_tree = build_file_tree(repo_root)
    readme_summary = summarize_readme(repo_root)
    entrypoints = detect_entrypoints(repo_root)
    repo_overview = summarize_repo_overview(repo_root)

    return {
        "ok": True,
        "repo_name": repo_name,
        "repo_root": repo_root,
        "file_tree": file_tree,
        "readme_summary": readme_summary,
        "entrypoint_candidates": entrypoints,
        "repo_overview": repo_overview,
    }
