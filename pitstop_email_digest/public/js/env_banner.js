$(document).ready(function () {
	const cfg = frappe.boot.environment_banner;
	if (!cfg || !cfg.text) return;

	const $banner = $(`
        <div class="env-banner" style="
            background: ${cfg.bg_color};
            color: ${cfg.text_color || "#fff"};
            text-align: center;
            padding: 4px 8px;
            font-weight: 600;
            font-size: 12px;
            letter-spacing: 1px;
        ">${frappe.utils.escape_html(cfg.text)}</div>
    `);

	// Prepend inside .sticky-top so it stays pinned with the navbar
	$(".sticky-top").prepend($banner);
});
