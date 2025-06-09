app_name = "pitstop_email_digest"
app_title = "Pitstop Email Digest"
app_publisher = "QCS"
app_description = "Email Digest for Pitstop"
app_email = "info@quarkcs.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "pitstop_email_digest",
# 		"logo": "/assets/pitstop_email_digest/logo.png",
# 		"title": "Pitstop Email Digest",
# 		"route": "/pitstop_email_digest",
# 		"has_permission": "pitstop_email_digest.api.permission.has_app_permission"
# 	}
# ]




scheduler_events = {
    "cron": {
        # every day 23:55 server time
        "55 23 * * *":
            "pitstop_email_digest.pitstop_email_digest.doctype."
            "pitstop_email_digest.pitstop_email_digest.auto_send_daily",

        # every Sunday 23:55  (i.e. 5 minutes before Monday)
        "55 23 * * 0":
            "pitstop_email_digest.pitstop_email_digest.doctype."
            "pitstop_email_digest.pitstop_email_digest.auto_send_weekly",
    }
}


# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/pitstop_email_digest/css/pitstop_email_digest.css"
# app_include_js = "/assets/pitstop_email_digest/js/pitstop_email_digest.js"

# include js, css files in header of web template
# web_include_css = "/assets/pitstop_email_digest/css/pitstop_email_digest.css"
# web_include_js = "/assets/pitstop_email_digest/js/pitstop_email_digest.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "pitstop_email_digest/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "pitstop_email_digest/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "pitstop_email_digest.utils.jinja_methods",
# 	"filters": "pitstop_email_digest.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "pitstop_email_digest.install.before_install"
# after_install = "pitstop_email_digest.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "pitstop_email_digest.uninstall.before_uninstall"
# after_uninstall = "pitstop_email_digest.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "pitstop_email_digest.utils.before_app_install"
# after_app_install = "pitstop_email_digest.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "pitstop_email_digest.utils.before_app_uninstall"
# after_app_uninstall = "pitstop_email_digest.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "pitstop_email_digest.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"pitstop_email_digest.tasks.all"
# 	],
# 	"daily": [
# 		"pitstop_email_digest.tasks.daily"
# 	],
# 	"hourly": [
# 		"pitstop_email_digest.tasks.hourly"
# 	],
# 	"weekly": [
# 		"pitstop_email_digest.tasks.weekly"
# 	],
# 	"monthly": [
# 		"pitstop_email_digest.tasks.monthly"
# 	],
# }


# Testing
# -------

# before_tests = "pitstop_email_digest.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "pitstop_email_digest.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "pitstop_email_digest.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["pitstop_email_digest.utils.before_request"]
# after_request = ["pitstop_email_digest.utils.after_request"]

# Job Events
# ----------
# before_job = ["pitstop_email_digest.utils.before_job"]
# after_job = ["pitstop_email_digest.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"pitstop_email_digest.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

