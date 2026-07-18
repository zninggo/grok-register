#!/usr/bin/env python3
"""无头模式批量注册入口，用于 Docker / 服务器环境。"""
import json
import os
import signal
import sys
import time

# 确保模块可导入
sys.path.insert(0, os.path.dirname(__file__))


def load_config(path=None):
    candidates = [
        path,
        os.environ.get("CONFIG_PATH"),
        os.path.join(os.path.dirname(__file__), "config.json"),
        os.path.join(os.path.dirname(__file__), "data", "config.json"),
    ]
    for p in candidates:
        if p and os.path.isfile(p):
            with open(p) as f:
                return json.load(f)
    print("[!] 未找到配置文件，使用默认配置")
    return {}


def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else None
    config = load_config(config_path)

    count = int(config.get("register_count", 1))
    proxy = config.get("proxy", "")
    enable_nsfw = config.get("enable_nsfw", True)
    cleanup_interval = int(config.get("cleanup_interval", 5))

    print(f"[*] 配置加载完成: count={count} proxy={proxy or '(无)'} nsfw={enable_nsfw}")
    print(f"[*] email_provider={config.get('email_provider', 'yyds')}")

    # 初始化浏览器和邮件服务
    import browser_runtime
    import mail_service
    import registration_browser

    browser_runtime.configure_runtime(config, os.path.dirname(__file__))
    mail_service.bind_runtime({
        "config": config,
        "http_get": browser_runtime.http_get,
        "http_post": browser_runtime.http_post,
        "http_delete": browser_runtime.http_delete,
        "get_user_agent": browser_runtime.get_user_agent if hasattr(browser_runtime, "get_user_agent") else lambda: "",
        "get_email_provider": mail_service.get_email_provider,
        "get_yyds_api_key": mail_service.get_yyds_api_key,
        "get_yyds_jwt": mail_service.get_yyds_jwt,
        "get_cloudflare_api_key": mail_service.get_cloudflare_api_key,
        "get_cloudflare_api_base": mail_service.get_cloudflare_api_base,
        "get_cloudflare_auth_mode": mail_service.get_cloudflare_auth_mode,
        "get_cloudflare_path": mail_service.get_cloudflare_path,
        "get_cloudmail_api_base": mail_service.get_cloudmail_api_base,
        "get_cloudmail_path": mail_service.get_cloudmail_path,
        "get_cloudmail_public_token": mail_service.get_cloudmail_public_token,
        "generate_username": mail_service.generate_username,
        "pick_domain": mail_service.pick_domain,
        "get_domains": mail_service.get_domains,
        "get_token": mail_service.get_token,
        "get_messages": mail_service.get_messages,
        "get_message_detail": mail_service.get_message_detail,
        "get_oai_code": mail_service.get_oai_code,
        "extract_verification_code": mail_service.extract_verification_code,
        "create_account": mail_service.create_account,
        "get_email_and_token": mail_service.get_email_and_token,
        "cloudflare_create_account": mail_service.cloudflare_create_account,
        "cloudflare_create_temp_address": mail_service.cloudflare_create_temp_address,
        "cloudflare_get_domains": mail_service.cloudflare_get_domains,
        "cloudflare_get_messages": mail_service.cloudflare_get_messages,
        "cloudflare_get_message_detail": mail_service.cloudflare_get_message_detail,
        "cloudflare_get_oai_code": mail_service.cloudflare_get_oai_code,
        "cloudflare_get_token": mail_service.cloudflare_get_token,
        "cloudflare_apply_auth_params": mail_service.cloudflare_apply_auth_params,
        "cloudflare_build_headers": mail_service.cloudflare_build_headers,
        "cloudflare_is_admin_create_path": mail_service.cloudflare_is_admin_create_path,
        "cloudflare_next_default_domain": mail_service.cloudflare_next_default_domain,
        "get_cloudflare_api_base": mail_service.get_cloudflare_api_base,
        "get_cloudflare_api_key": mail_service.get_cloudflare_api_key,
        "get_cloudflare_auth_mode": mail_service.get_cloudflare_auth_mode,
        "get_cloudflare_path": mail_service.get_cloudflare_path,
        "cloudmail_get_email_and_token": mail_service.cloudmail_get_email_and_token,
        "cloudmail_get_messages": mail_service.cloudmail_get_messages,
        "cloudmail_get_oai_code": mail_service.cloudmail_get_oai_code,
        "cloudmail_next_domain": mail_service.cloudmail_next_domain,
        "duckmail_get_oai_code": mail_service.duckmail_get_oai_code,
        "get_duckmail_api_key": mail_service.get_duckmail_api_key,
        "yyds_create_account": mail_service.yyds_create_account,
        "yyds_generate_username": mail_service.yyds_generate_username,
        "yyds_get_domains": mail_service.yyds_get_domains,
        "yyds_get_email_and_token": mail_service.yyds_get_email_and_token,
        "yyds_get_message_detail": mail_service.yyds_get_message_detail,
        "yyds_get_messages": mail_service.yyds_get_messages,
        "yyds_get_oai_code": mail_service.yyds_get_oai_code,
        "yyds_get_token": mail_service.yyds_get_token,
        "yyds_pick_domain": mail_service.yyds_pick_domain,
        "yyds_cleanup_inbox": mail_service.yyds_cleanup_inbox,
        "yyds_delete_account": mail_service.yyds_delete_account,
        "delete_mailbox": mail_service.delete_mailbox,
        "delete_mailbox_by_address": mail_service.delete_mailbox_by_address,
        "_pick_list_payload": mail_service._pick_list_payload,
    })

    # 构建 ops
    from registration_flow import (
        RegistrationCallbacks,
        RegistrationOperations,
        run_batch,
    )

    cancelled = False

    def cancel_callback():
        return cancelled

    def log_callback(msg):
        ts = time.strftime("%H:%M:%S")
        print(f"[{ts}] {msg}", flush=True)

    def handle_signal(sig, frame):
        nonlocal cancelled
        cancelled = True
        log_callback("[!] 收到停止信号，等待当前账号完成...")

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    # 持久化路径
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    accounts_file = os.path.join(data_dir, "accounts.txt")

    from account_outputs import save_mail_credential, append_account_line

    operations = RegistrationOperations(
        start_browser=lambda: registration_browser.start_browser(log_callback=log_callback),
        restart_browser=lambda: registration_browser.restart_browser(log_callback=log_callback),
        browser_missing=lambda: registration_browser.browser is None,
        open_signup_page=lambda: registration_browser.open_signup_page(log_callback=log_callback, cancel_callback=cancel_callback),
        fill_email_and_submit=lambda: registration_browser.fill_email_and_submit(log_callback=log_callback, cancel_callback=cancel_callback),
        save_mail_credential=lambda email, token: save_mail_credential(data_dir, email, token),
        fill_code_and_submit=lambda email, token: registration_browser.fill_code_and_submit(email, token, log_callback=log_callback, cancel_callback=cancel_callback),
        fill_profile_and_submit=lambda: registration_browser.fill_profile_and_submit(log_callback=log_callback, cancel_callback=cancel_callback),
        wait_for_sso_cookie=lambda: registration_browser.wait_for_sso_cookie(log_callback=log_callback, cancel_callback=cancel_callback),
        enable_nsfw=lambda sso: registration_browser.enable_nsfw_for_token(sso, log_callback=log_callback),
        persist_account_line=lambda email, password, sso: append_account_line(accounts_file, email, password, sso),
        queue_unsaved_result=lambda payload, error: False,
        add_tokens=lambda sso, email: _push_to_grok2api(config, sso, email, log_callback),
        export_cpa=lambda email, password, sso: {"skipped": True},
        cleanup=lambda reason: registration_browser.cleanup_runtime_memory(log_callback=log_callback, reason=reason),
        sleep=lambda seconds: time.sleep(seconds),
        cancelled_exception=KeyboardInterrupt,
        retry_exception=Exception,
        delete_mailbox=lambda address: _delete_mailbox(address, log_callback),
        cleanup_inbox=lambda address: _cleanup_inbox(address, log_callback),
    )

    callbacks = RegistrationCallbacks(log=log_callback, cancelled=cancel_callback)

    log_callback(f"[*] 开始注册 {count} 个账号...")

    result = run_batch(
        count=count,
        callbacks=callbacks,
        observer=None,
        ops=operations,
        enable_nsfw=enable_nsfw,
        cleanup_interval=cleanup_interval,
        max_slot_retry=3,
        max_mail_retry=3,
    )

    log_callback(f"[=] 注册完成: 成功={result.success_count} 失败={result.fail_count} 取消={result.cancelled}")
    return 0 if result.success_count > 0 else 1


def _push_to_grok2api(config, sso, email, log_callback):
    """推送 token 到 grok2api"""
    results = {}
    # 本地文件入池
    if config.get("grok2api_auto_add_local"):
        try:
            from account_outputs import add_token_to_grok2api_local_pool
            ok = add_token_to_grok2api_local_pool(config, sso, email=email)
            results["local"] = {"enabled": True, "ok": ok}
            if ok:
                log_callback(f"[+] grok2api 本地入池成功: {email}")
        except Exception as e:
            results["local"] = {"enabled": True, "ok": False, "error": str(e)}
            log_callback(f"[!] grok2api 本地入池失败: {e}")
    # 远端入池
    if config.get("grok2api_auto_add_remote"):
        try:
            from account_outputs import add_token_to_grok2api_remote_pool
            ok = add_token_to_grok2api_remote_pool(config, sso, email=email)
            results["remote"] = {"enabled": True, "ok": ok}
            if ok:
                log_callback(f"[+] grok2api 远端入池成功: {email}")
        except Exception as e:
            results["remote"] = {"enabled": True, "ok": False, "error": str(e)}
            log_callback(f"[!] grok2api 远端入池失败: {e}")
    if not results:
        results["skipped"] = True
    return results


def _delete_mailbox(address, log_callback):
    try:
        from mail_service import delete_mailbox_by_address
        ok = delete_mailbox_by_address(address)
        if ok:
            log_callback(f"[+] 临时邮箱已清理: {address}")
        return ok
    except Exception as e:
        log_callback(f"[!] 删除邮箱失败: {e}")
        return False


def _cleanup_inbox(address, log_callback):
    try:
        from mail_service import yyds_cleanup_inbox
        n = yyds_cleanup_inbox(address)
        if n > 0:
            log_callback(f"[*] 清理了 {n} 封残留邮件")
        return n
    except Exception as e:
        log_callback(f"[!] 清空收件箱失败: {e}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
