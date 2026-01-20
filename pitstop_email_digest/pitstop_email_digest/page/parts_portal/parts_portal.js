/* file: <your_app>/<module>/page/parts_portal/parts_portal.js */

frappe.pages["parts-portal"].on_page_load = function (wrapper) {
  // 1️⃣  Build the desk page skeleton
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: __("Parts Portal"),
    single_column: true, // hides the left sidebar column
  });

  // 2️⃣  Add the iframe
  $(page.body).html(`
        <div style="height:100%;width:100%;overflow:hidden">
            <iframe
                src="https://parts.quarkcs.com/"
                style="border:none;width:100%;height:calc(100vh - 120px);">
            </iframe>
        </div>
    `);

  // (Optional) now `page.set_title(...)` works too
  // page.set_title(__('Parts Portal'));
};
