include graph_types;

walker code_analyzer_build_ccg {
    has repo_name: str;

    can run with `root entry;
}

impl code_analyzer_build_ccg.run {
    target_repo = None;

    for n in RepoNode {
        if n.repo_name == self.repo_name {
            target_repo = n;
            break;
        }
    }

    if target_repo == None {
        report {
            "ok": False,
            "stage": "code_analyzer",
            "error": "No such repo in graph: " + self.repo_name,
        };
    } else {
        if target_repo.status.startswith("error") {
            report {
                "ok": False,
                "stage": "code_analyzer",
                "error": "Repo not in valid state: " + target_repo.status,
            };
        } else {
            try {
                analysis = py.ccg_builder.run_code_analyzer(
                    target_repo.local_path,
                    target_repo.repo_name,
                );

                if not analysis["ok"] {
                    target_repo.status = "error_ccg:" + str(analysis["error"]);

                    report {
                        "ok": False,
                        "stage": analysis["stage"],
                        "error": analysis["error"],
                    };
                } else {
                    for fileinfo in analysis["per_file_info"] {
                        if fileinfo["lang"] == "python" {
                            for c in fileinfo["classes"] {
                                sym_cls = SymbolNode();
                                sym_cls.sym_id    = fileinfo["path"] + ":" + c["name"];
                                sym_cls.sym_name  = c["name"];
                                sym_cls.sym_type  = "class";
                                sym_cls.file_path = fileinfo["path"];
                                sym_cls.lineno    = 0;
                                sym_cls.docstring = "";
                                link_cls = ContainsEdge(rel_type="repo-symbol");
                                connect(target_repo, link_cls, sym_cls);

                                for m in c["methods"] {
                                    sym_m = SymbolNode();
                                    sym_m.sym_id    = fileinfo["path"] + ":" + c["name"] + "." + m;
                                    sym_m.sym_name  = c["name"] + "." + m;
                                    sym_m.sym_type  = "method";
                                    sym_m.file_path = fileinfo["path"];
                                    sym_m.lineno    = 0;
                                    sym_m.docstring = "";
                                    link_m = ContainsEdge(rel_type="repo-symbol");
                                    connect(target_repo, link_m, sym_m);
                                }
                            }

                            for fn in fileinfo["functions"] {
                                sym_fn = SymbolNode();
                                sym_fn.sym_id    = fileinfo["path"] + ":" + fn["name"];
                                sym_fn.sym_name  = fn["name"];
                                sym_fn.sym_type  = "function";
                                sym_fn.file_path = fileinfo["path"];
                                sym_fn.lineno    = 0;
                                sym_fn.docstring = "";
                                link_fn = ContainsEdge(rel_type="repo-symbol");
                                connect(target_repo, link_fn, sym_fn);
                            }
                        }

                        if fileinfo["lang"] == "jac" {
                            for w in fileinfo.get("jac_walkers", []) {
                                jw = SymbolNode();
                                jw.sym_id    = fileinfo["path"] + ":" + w;
                                jw.sym_name  = w;
                                jw.sym_type  = "jac_walker";
                                jw.file_path = fileinfo["path"];
                                jw.lineno    = 0;
                                jw.docstring = "";
                                link_jw = ContainsEdge(rel_type="repo-symbol");
                                connect(target_repo, link_jw, jw);
                            }
                            for nname in fileinfo.get("jac_nodes", []) {
                                jn = SymbolNode();
                                jn.sym_id    = fileinfo["path"] + ":" + nname;
                                jn.sym_name  = nname;
                                jn.sym_type  = "jac_node";
                                jn.file_path = fileinfo["path"];
                                jn.lineno    = 0;
                                jn.docstring = "";
                                link_jn = ContainsEdge(rel_type="repo-symbol");
                                connect(target_repo, link_jn, jn);
                            }
                        }
                    }

                    target_repo.status = "analyzed";

                    report {
                        "ok": True,
                        "ccg_stats": analysis["ccg_stats"],
                        "diagrams": analysis["diagrams"],
                        "per_file_info": analysis["per_file_info"],
                    };
                }
            } except Exception as e {
                target_repo.status = "error_ccg:" + str(e);

                report {
                    "ok": False,
                    "stage": "code_analyzer",
                    "error": "CodeAnalyzer failed: " + str(e),
                };
            }
        }
    }
}
