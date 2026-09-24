no_cache = 1


def get_context(context):
    context.no_cache = 1
    context.no_header = 1
    context.no_breadcrumbs = 1
    context.no_sidebar = 1
    # Guest can open this page without logging in
    context.requires_login = False
    context.iframe_src = "https://polaris.pitstopauto.ae/"

    return context
