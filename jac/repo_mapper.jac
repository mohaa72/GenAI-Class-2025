# repo_mapper.jac
include graph_types;

walker repo_mapper_init {
    has repo_url: str;

    # this walker can be called as an entrypoint
    can run with `root entry;
}

impl repo_mapper_init.run {
    try {
        # ask Python layer to clone + map the repo
        clone_info = py.repo_tools.run_repo_mapper(self.repo_url);

        if not clone_info["ok"] {
            report {
                "ok": False,
                "stage": "repo_mapper.clone",
                "error": clone_info["error"],
            };
        } else {
            # Create a RepoNode in the Jac graph
            r = RepoNode();
            r.repo_name      = clone_info["repo_name"];
            r.repo_url       = self.repo_url;
            r.local_path     = clone_info["repo_root"];
            r.readme_summary = clone_info["readme_summary"];
            r.docs_path      = "";
            r.status         = "mapped";

            # serialize file tree list for DocGenie / UI
            r.file_tree_json = py.json.dumps(clone_info["file_tree"]);

            # (future enhancement)
            # here you could create FileNode objects and connect() them
            # to this RepoNode via ContainsEdge(rel_type="repo-contains")

            report {
                "ok": True,
                "repo_name": r.repo_name,
                "repo_root": r.local_path,
                "file_tree": clone_info["file_tree"],
                "readme_summary": r.readme_summary,
            };
        }
    } except Exception as err {
        # record an error state node for debug
        rfail = RepoNode();
        rfail.repo_name      = "unknown";
        rfail.repo_url       = self.repo_url;
        rfail.local_path     = "";
        rfail.readme_summary = "";
        rfail.docs_path      = "";
        rfail.status         = "error:" + str(err);
        rfail.file_tree_json = "";

        report {
            "ok": False,
            "stage": "repo_mapper",
            "error": "RepoMapper failed: " + str(err),
        };
    }
}
