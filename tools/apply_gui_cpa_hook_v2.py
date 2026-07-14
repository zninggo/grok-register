#!/usr/bin/env python3
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "grok_register_ttk.py"

app = APP_PATH.read_text(encoding="utf-8-sig")
old = '                    add_token_to_grok2api_pools(sso, email=email, log_callback=self.log)\n                    self.success_count += 1'
new = '''                    add_token_to_grok2api_pools(sso, email=email, log_callback=self.log)
                    maybe_export_cpa_xai_after_success(
                        email=email,
                        password=profile.get("password", ""),
                        sso=sso,
                        log_callback=self.log,
                        cancel_callback=self.should_stop,
                    )
                    self.success_count += 1'''
if old in app:
    app = app.replace(old, new, 1)
elif new not in app:
    raise RuntimeError("GUI CPA hook anchor not found")
ast.parse(app)
APP_PATH.write_text(app, encoding="utf-8-sig")
print("GUI CPA hook applied.")
