from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import shutil
import os

from backend_py.repo_tools import run_repo_mapper
from backend_py.ccg_builder import run_code_analyzer
from backend_py.docgen_tools import run_docgen


PROJECT_ROOT_NAME = "agentic_codebase_genius"

app = FastAPI()


@app.post("/walker/api_generate_docs")
async def api_generate_docs(request: Request):
    """
    Request body:
        { "repo_url": "https://github.com/org/repo" }

    Response:
        {
          "status": 200,
          "reports": [
             {
               "ok": true,
               "repo_name": "...",
               "docs_path": ".../outputs/<repo>/docs.md",
               "preview": "... full markdown ...",
               "file_tree": [...],
               "entrypoint_candidates": [...],
               "repo_overview": "...",
               "ccg_stats": {...},
               "diagrams": {...}
             }
          ]
        }

    This matches what your Streamlit UI expects and what we talked about.
    """
    body = await request.json()
    repo_url = (body.get("repo_url") or "").strip()

    if not repo_url:
        return JSONResponse(
            status_code=400,
            content={
                "status": 400,
                "reports": [
                    {"ok": False, "error": "No repo_url provided"}
                ],
            },
        )

    # 1. Repo Mapper step
    repo_map = run_repo_mapper(repo_url, project_root=PROJECT_ROOT_NAME)
    if not repo_map.get("ok"):
        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "reports": [
                    {
                        "ok": False,
                        "stage": repo_map.get("stage", "repo_mapper"),
                        "error": repo_map.get("error", "repo mapper failed"),
                    }
                ],
            },
        )

    repo_name = repo_map["repo_name"]
    repo_root = repo_map["repo_root"]
    file_tree = repo_map["file_tree"]
    readme_summary = repo_map["readme_summary"]
    entrypoints = repo_map["entrypoint_candidates"]
    repo_overview = repo_map["repo_overview"]

    
    analysis = run_code_analyzer(repo_root, repo_name)
    if not analysis.get("ok"):
        
        resp_payload = {
            "ok": False,
            "repo_name": repo_name,
            "error": analysis.get("error", "analysis failed"),
            "stage": analysis.get("stage", "code_analyzer"),
        }
        return JSONResponse(
            status_code=500,
            content={"status": 500, "reports": [resp_payload]},
        )

    ccg_stats = analysis["ccg_stats"]
    diagrams = analysis["diagrams"]

    docgen_res = run_docgen(
        repo_name=repo_name,
        readme_summary=readme_summary,
        file_tree=file_tree,
        analysis=analysis,
        project_root=PROJECT_ROOT_NAME,
    )

    if not docgen_res.get("ok"):
        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "reports": [
                    {
                        "ok": False,
                        "repo_name": repo_name,
                        "stage": docgen_res.get("stage", "docgenie"),
                        "error": docgen_res.get("error", "docgen failed"),
                    }
                ],
            },
        )

    docs_path = docgen_res["docs_path"]
    preview_text = docgen_res["preview"]

    
    try:
        clone_parent = os.path.dirname(repo_root)
        shutil.rmtree(clone_parent, ignore_errors=True)
    except Exception:
        pass

    
    response_payload = {
        "ok": True,
        "repo_name": repo_name,
        "docs_path": docs_path,
        "preview": preview_text,
        "file_tree": file_tree,
        "entrypoint_candidates": entrypoints,
        "repo_overview": repo_overview,
        "ccg_stats": ccg_stats,
        "diagrams": diagrams,
    }

    return JSONResponse(
        status_code=200,
        content={
            "status": 200,
            "reports": [response_payload],
        },
    )
