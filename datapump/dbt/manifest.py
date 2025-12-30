import json
from typing import Dict


def load_compiled_models(manifest_path) -> Dict[str, str]:
    with open(manifest_path, "r", encoding="utf-8") as handle:
        manifest = json.load(handle)

    models = {}
    for node in manifest.get("nodes", {}).values():
        if node.get("resource_type") != "model":
            continue
        compiled_sql = node.get("compiled_sql")
        if not compiled_sql:
            continue
        name = node.get("name")
        if name:
            models[name] = compiled_sql

    return models
