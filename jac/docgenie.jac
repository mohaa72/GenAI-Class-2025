include graph_types;

walker docgenie_generate {
    has repo_name: str;
    has readme_summary: str;
    has file_tree: list;
    has analysis: dict;

    can run with `root entry;
}

impl docgenie_generate.run {
    repo_ref = None;
    for r in RepoNode {
        if r.repo_name == self.repo_name {
            repo_ref = r;
            break;
        }
    }

    if repo_ref == None {
        report {
            "ok": False,
            "stage": "docgenie",
            "error": "DocGenie: repo not found: " + self.repo_name,
        };
    } else {
        if repo_ref.status.startswith("error") {
            report {
                "ok": False,
                "stage": "docgenie",
                "error": "DocGenie: repo invalid status: " + repo_ref.status,
            };
        } else {
            try {
                out = py.docgen_tools.run_docgen(
                    self.repo_name,
                    self.readme_summary,
                    self.file_tree,
                    self.analysis,
                );

                if not out["ok"] {
                    repo_ref.status = "error_doc:" + str(out["error"]);

                    report {
                        "ok": False,
                        "stage": "docgenie",
                        "error": out["error"],
                    };
                } else {
                    # persist docs path onto the RepoNode
                    repo_ref.docs_path = out["docs_path"];
                    repo_ref.status = "documented";

                    report {
                        "ok": True,
                        "docs_path": out["docs_path"],
                        "preview": out["preview"],
                        "ccg_stats": self.analysis["ccg_stats"],
                    };
                }
            } except Exception as e {
                repo_ref.status = "error_doc:" + str(e);

                report {
                    "ok": False,
                    "stage": "docgenie",
                    "error": "DocGenie failed: " + str(e),
                };
            }
        }
    }
}
