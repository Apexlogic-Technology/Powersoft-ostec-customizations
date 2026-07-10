import frappe

def execute():
	"""Delete custom_license_renewal_section and custom_license_renewal_items from SO and SI."""
	fields_to_delete = [
		"Sales Order-custom_license_renewal_section",
		"Sales Order-custom_license_renewal_items",
		"Sales Invoice-custom_license_renewal_section",
		"Sales Invoice-custom_license_renewal_items"
	]
	for field in fields_to_delete:
		if frappe.db.exists("Custom Field", field):
			frappe.delete_doc("Custom Field", field)
