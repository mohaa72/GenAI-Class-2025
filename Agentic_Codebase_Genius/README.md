# Codebase Genius (Jac Multi-Agent Documentation Generator)

## What it does
- Input: Public GitHub repo URL.
- Pipeline in Jac:
  1. RepoMapper → clone repo, build file tree, summarize README.
  2. CodeAnalyzer → parse code (Python, Jac, JS/TS), build Code Context Graph (CCG).
  3. DocGenie → generate docs.md with project overview, file tree, Mermaid diagram, API reference.
  4. Supervisor → orchestrates all steps.
- Output: `outputs/<repo_name>/docs.md`.

## How it works
- Jac defines nodes/edges (RepoNode, FileNode, SymbolNode, ContainsEdge, CallsEdge).
- Jac walkers build a live graph of the repository.
- Python helpers do:
  - cloning (GitPython),
  - AST/regex parsing,
  - Markdown doc generation.
- `jac serve jac/main.jac` exposes the walker `api_generate_docs` as an HTTP endpoint.
- A Streamlit frontend calls that API and shows animated UI.

---

## Setup and Run
# ------ #
cd agentic_codebase_genius/backend_py
python3 -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\\Scripts\\Activate
pip install --upgrade pip
pip install -r requirements.txt

Allow Jac to import backend_py.* via py.<module>.<function>
export PYTHONPATH=$(pwd):$PYTHONPATH

2️⃣ Start Jac Server (Terminal A)

jac serve jac/main.jac

3️⃣ Frontend Setup (Terminal B)

cd agentic_codebase_genius/frontend
streamlit run app.py

