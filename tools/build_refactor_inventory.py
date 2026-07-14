#!/usr/bin/env python3
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = [
    ROOT / "grok_register_ttk.py",
    ROOT / "registration_flow.py",
    ROOT / "cpa_xai" / "browser_confirm.py",
    ROOT / "cpa_export.py",
    ROOT / "cf_mail_debug.py",
    ROOT / "cpa_xai" / "oauth_device.py",
    ROOT / "cpa_xai" / "proxyutil.py",
]


def free_names(node):
    assigned = set()
    loaded = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            if isinstance(child.ctx, (ast.Store, ast.Param)):
                assigned.add(child.id)
            elif isinstance(child.ctx, ast.Load):
                loaded.add(child.id)
        elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and child is not node:
            assigned.add(child.name)
    return sorted(loaded - assigned)

out = {}
for path in TARGETS:
    if not path.exists():
        continue
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(path))
    entries = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            entries.append({
                "kind": type(node).__name__,
                "name": node.name,
                "start": node.lineno,
                "end": getattr(node, "end_lineno", node.lineno),
                "free_names": free_names(node),
            })
    out[str(path.relative_to(ROOT))] = {
        "lines": len(text.splitlines()),
        "definitions": entries,
    }

(ROOT / "refactor_inventory.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print("inventory written")
