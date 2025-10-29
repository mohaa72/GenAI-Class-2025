from pathlib import Path
import tempfile
import shutil
import json

IGNORED_DIRS = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', '.pytest_cache'}

def make_tempdir(prefix="cbg_repo_"):
    return tempfile.mkdtemp(prefix=prefix)

def safe_rmtree(path: str):
    if not path:
        return
    try:
        shutil.rmtree(path)
    except Exception as e:
        print(f"[safe_rmtree] could not remove {path}: {e}")

def ensure_dir(path: str):
    Path(path).mkdir(parents=True, exist_ok=True)

def build_file_tree(root_dir: str):
    """Return nested {name, path, type, children?, size?} structure."""
    root = Path(root_dir)

    def walk(p: Path):
        node = {
            "name": p.name,
            "path": str(p),
            "type": "dir",
            "children": []
        }
        try:
            for child in sorted(p.iterdir(), key=lambda x: x.name):
                if child.name in IGNORED_DIRS:
                    continue
                if child.is_dir():
                    node["children"].append(walk(child))
                else:
                    node["children"].append({
                        "name": child.name,
                        "path": str(child),
                        "type": "file",
                        "size": child.stat().st_size
                    })
        except PermissionError:
            pass
        return node

    return walk(root)

def serialize_json(obj) -> str:
    return json.dumps(obj, indent=2)
