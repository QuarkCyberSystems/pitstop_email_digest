import frappe


def boot_session(bootinfo):
    bootinfo.environment_banner = frappe.conf.get("environment_banner")


def update_website_context(context):
    """Render the environment banner on web pages (login, portal, etc.).

    Desk uses env_banner.js which reads frappe.boot.environment_banner, but
    web pages populate frappe.boot from get_boot_data() which does not run
    boot_session hooks, so we render the banner server-side via banner_html.
    """
    cfg = frappe.conf.get("environment_banner")
    if not cfg or not cfg.get("text"):
        return

    bg = cfg.get("bg_color") or "#000"
    text_color = cfg.get("text_color") or "#fff"
    text = frappe.utils.escape_html(cfg["text"])

    banner = (
        f'<div class="env-banner" style="'
        f"background:{bg};color:{text_color};"
        "text-align:center;padding:4px 8px;"
        'font-weight:600;font-size:12px;letter-spacing:1px;">'
        f"{text}</div>"
    )

    context.banner_html = banner + (context.get("banner_html") or "")
