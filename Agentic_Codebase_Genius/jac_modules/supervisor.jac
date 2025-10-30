include graph_types;

walker supervisor_run {
    has repo_url: str;

    obj __specs__ {
        static has methods: list = ["post"];
        static has auth: bool = False;
    }

    can orchestrate with `root entry;
}

impl supervisor_run.orchestrate {
    try {
        clone_info = py.repo_tools.run_repo_mapper(self.repo_url);

        if not clone_info["ok"] {
            report {
                "ok": False,
                "stage": "repo_mapper",
                "error": clone_info["error"],
            };
        } else {
            repo_name  = clone_info["repo_name"];
            repo_root  = clone_info["repo_root"];
            file_tree  = clone_info["file_tree"];
            readme_sum = clone_info["readme_summary"];

            repo_ref = RepoNode();
            repo_ref.repo_name      = repo_name;
            repo_ref.repo_url       = self.repo_url;
            repo_ref.local_path     = repo_root;
            repo_ref.readme_summary = readme_sum;
            repo_ref.docs_path      = "";
            repo_ref.status         = "mapped";
            repo_ref.file_tree_json = py.json.dumps(file_tree);
            analysis_info = py.ccg_builder.run_code_analyzer(repo_root, repo_name);

            if not analysis_info["ok"] {
                repo_ref.status = "error_ccg:" + str(analysis_info["error"]);

                report {
                    "ok": False,
                    "stage": "code_analyzer",
                    "error": analysis_info["error"],
                };
            } else {
                ccg_stats      = analysis_info["ccg_stats"];
                per_file_info  = analysis_info["per_file_info"];
                diagrams       = analysis_info["diagrams"];

                repo_ref.status = "analyzed";
                for fi in per_file_info {
                    if fi["lang"] == "python" {
                        for c in fi["classes"] {
                            sym_cls = SymbolNode();
                            sym_cls.sym_id    = fi["path"] + ":" + c["name"];
                            sym_cls.sym_name  = c["name"];
                            sym_cls.sym_type  = "class";
                            sym_cls.file_path = fi["path"];
                            sym_cls.lineno    = 0;
                            sym_cls.docstring = "";
                            link_cls = ContainsEdge(rel_type="repo-symbol");
                            connect(repo_ref, link_cls, sym_cls);

                            for m in c["methods"] {
                                sym_m = SymbolNode();
                                sym_m.sym_id    = fi["path"] + ":" + c["name"] + "." + m;
                                sym_m.sym_name  = c["name"] + "." + m;
                                sym_m.sym_type  = "method";
                                sym_m.file_path = fi["path"];
                                sym_m.lineno    = 0;
                                sym_m.docstring = "";
                                link_m = ContainsEdge(rel_type="repo-symbol");
                                connect(repo_ref, link_m, sym_m);
                            }
                        }

                        for fn in fi["functions"] {
                            sym_fn = SymbolNode();
                            sym_fn.sym_id    = fi["path"] + ":" + fn["name"];
                            sym_fn.sym_name  = fn["name"];
                            sym_fn.sym_type  = "function";
                            sym_fn.file_path = fi["path"];
                            sym_fn.lineno    = 0;
                            sym_fn.docstring = "";
                            link_fn = ContainsEdge(rel_type="repo-symbol");
                            connect(repo_ref, link_fn, sym_fn);
                        }
                    }

                    if fi["lang"] == "jac" {
                        for w in fi.get("jac_walkers", []) {
                            jw = SymbolNode();
                            jw.sym_id    = fi["path"] + ":" + w;
                            jw.sym_name  = w;
                            jw.sym_type  = "jac_walker";
                            jw.file_path = fi["path"];
                            jw.lineno    = 0;
                            jw.docstring = "";
                            link_jw = ContainsEdge(rel_type="repo-symbol");
                            connect(repo_ref, link_jw, jw);
                        }
                        for nname in fi.get("jac_nodes", []) {
                            jn = SymbolNode();
                            jn.sym_id    = fi["path"] + ":" + nname;
                            jn.sym_name  = nname;
                            jn.sym_type  = "jac_node";
                            jn.file_path = fi["path"];
                            jn.lineno    = 0;
                            jn.docstring = "";
                            link_jn = ContainsEdge(rel_type="repo-symbol");
                            connect(repo_ref, link_jn, jn);
                        }
                    }
                }

                analysis_bundle = {
                    "ok": True,
                    "ccg_stats": ccg_stats,
                    "diagrams": diagrams,
                    "per_file_info": per_file_info,
                };

                doc_out = py.docgen_tools.run_docgen(
                    repo_name,
                    readme_sum,
                    file_tree,
                    analysis_bundle,
                );

                if not doc_out["ok"] {
                    repo_ref.status = "error_doc:" + str(doc_out["error"]);

                    report {
                        "ok": False,
                        "stage": "docgenie",
                        "error": doc_out["error"],
                    };
                } else {
                    repo_ref.docs_path = doc_out["docs_path"];
                    repo_ref.status    = "documented";

                   
                    report {
                        "ok": True,
                        "repo_name": repo_name,
                        "docs_path": doc_out["docs_path"],
                        "preview": doc_out["preview"],
                        "ccg_stats": ccg_stats,
                        "diagrams": diagrams,
                    };
                }
            }
        }

    } except Exception as e {
        report {
            "ok": False,
            "stage": "supervisor",
            "error": "Supervisor crashed: " + str(e),
        };
    }
}
