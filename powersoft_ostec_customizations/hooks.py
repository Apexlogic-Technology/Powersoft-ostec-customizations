app_name = "powersoft_ostec_customizations"
app_title = "Powersoft Ostec Customizations"
app_publisher = "SaifUdDinSalman"
app_description = "Powersoft Ostec Customizations"
app_email = "saifuddinsalman.dev@gmail.com"
app_license = "mit"
# required_apps = []

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/powersoft_ostec_customizations/css/powersoft_ostec_customizations.css"
# app_include_js = "/assets/powersoft_ostec_customizations/js/powersoft_ostec_customizations.js"

# include js, css files in header of web template
# web_include_css = "/assets/powersoft_ostec_customizations/css/powersoft_ostec_customizations.css"
# web_include_js = "/assets/powersoft_ostec_customizations/js/powersoft_ostec_customizations.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "powersoft_ostec_customizations/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Quotation": "public/js/quotation_custom.js",
    "Supplier Quotation": "public/js/supplier_quotation_custom.js",
    "Payment Entry": "public/js/payment_entry_custom.js",
    "Sales Order": "public/js/sales_order_custom.js",
    "Sales Invoice": "public/js/sales_invoice_custom.js",
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "powersoft_ostec_customizations/public/icons.svg"

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
# 	"methods": "powersoft_ostec_customizations.utils.jinja_methods",
# 	"filters": "powersoft_ostec_customizations.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "powersoft_ostec_customizations.install.before_install"
# after_install = "powersoft_ostec_customizations.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "powersoft_ostec_customizations.uninstall.before_uninstall"
# after_uninstall = "powersoft_ostec_customizations.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "powersoft_ostec_customizations.utils.before_app_install"
# after_app_install = "powersoft_ostec_customizations.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "powersoft_ostec_customizations.utils.before_app_uninstall"
# after_app_uninstall = "powersoft_ostec_customizations.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "powersoft_ostec_customizations.notifications.get_notification_config"

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

doc_events = {
    "Supplier Quotation": {
        "validate": "powersoft_ostec_customizations.doctype_changes.supplier_quotation_custom.validate",
        "on_submit": "powersoft_ostec_customizations.doctype_changes.supplier_quotation_custom.on_submit",
    },
    "Quotation": {
        "onload": "powersoft_ostec_customizations.doctype_changes.quotation_custom.onload",
        "before_save": "powersoft_ostec_customizations.doctype_changes.quotation_custom.before_save",
        "validate": "powersoft_ostec_customizations.doctype_changes.quotation_custom.validate",
        "before_submit": "powersoft_ostec_customizations.doctype_changes.quotation_custom.before_submit",
        "on_submit": "powersoft_ostec_customizations.doctype_changes.quotation_custom.on_submit",
    },
    # Copy multi-year license renewal data from the Quotation into the Sales Order on creation
    "Sales Order": {
        "onload": "powersoft_ostec_customizations.doctype_changes.sales_order_custom.onload",
        "before_insert": "powersoft_ostec_customizations.doctype_changes.sales_order_custom.before_insert",
        "before_save": "powersoft_ostec_customizations.doctype_changes.sales_order_custom.before_save",
        "after_save": "powersoft_ostec_customizations.doctype_changes.sales_order_custom.after_save",
    },
    # Copy multi-year license renewal data from the Sales Order into the Sales Invoice on creation
    "Sales Invoice": {
        "onload": "powersoft_ostec_customizations.doctype_changes.sales_invoice_custom.onload",
        "before_insert": "powersoft_ostec_customizations.doctype_changes.sales_invoice_custom.before_insert",
        "before_save": "powersoft_ostec_customizations.doctype_changes.sales_invoice_custom.before_save",
    },
    # Copy multi-year data from reference Sales Invoice when creating/saving a Payment Entry
    "Payment Entry": {
        "onload": "powersoft_ostec_customizations.doctype_changes.payment_entry_custom.onload",
        "before_insert": "powersoft_ostec_customizations.doctype_changes.payment_entry_custom.before_insert",
        "before_save": "powersoft_ostec_customizations.doctype_changes.payment_entry_custom.before_save",
    },
}


# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"powersoft_ostec_customizations.tasks.all"
# 	],
# 	"daily": [
# 		"powersoft_ostec_customizations.tasks.daily"
# 	],
# 	"hourly": [
# 		"powersoft_ostec_customizations.tasks.hourly"
# 	],
# 	"weekly": [
# 		"powersoft_ostec_customizations.tasks.weekly"
# 	],
# 	"monthly": [
# 		"powersoft_ostec_customizations.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "powersoft_ostec_customizations.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "powersoft_ostec_customizations.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "powersoft_ostec_customizations.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["powersoft_ostec_customizations.utils.before_request"]
# after_request = ["powersoft_ostec_customizations.utils.after_request"]

# Job Events
# ----------
# before_job = ["powersoft_ostec_customizations.utils.before_job"]
# after_job = ["powersoft_ostec_customizations.utils.after_job"]

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
# 	"powersoft_ostec_customizations.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

fixtures = [
    {
        "dt": "Custom Field",
        "filters": {
            "module": "Powersoft Ostec Customizations",
        },
    },
    {
        "dt": "Property Setter",
        "filters": {
            "module": "Powersoft Ostec Customizations",
        },
	},
    # {
    #     "dt": "Item",
    #     "filters": {
    #         "name": "Item Code",
    #     },
	# },
]
