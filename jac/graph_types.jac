node RepoNode {
    has repo_name: str;
    has repo_url: str;
    has local_path: str;
    has readme_summary: str;
    has docs_path: str;
    has status: str;
    has file_tree_json: str;
}

node FileNode {
    has path: str;
    has name: str;
    has is_dir: bool;
    has size_bytes: int;
}

node SymbolNode {
    has sym_id: str;
    has sym_name: str;
    has sym_type: str;      # "class", "function", "method", etc.
    has file_path: str;
    has lineno: int;
    has docstring: str;
}

edge ContainsEdge {
    has rel_type: str;      
}

edge CallsEdge {
    has call_type: str;     
    has lineno: int;
}
