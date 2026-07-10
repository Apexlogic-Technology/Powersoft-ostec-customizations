import frappe
from frappe.utils import flt


def before_insert(self, method=None):
	"""Copy multi-year license renewal data from the source Quotation when a Sales Order is created."""
	frappe.throw("before_insert is running!")
	copy_multi_year_data_from_quotation(self)


def _find_source_quotation(self):
	"""
	Robustly detect the source Quotation name from a newly created Sales Order.
	Tries multiple field names to remain compatible across ERPNext versions.
	Returns the Quotation name (string) or None if not found.
	"""
	# Common field names used across ERPNext versions to link SO Items back to their source Quotation
	candidate_fields = [
		# v13/v14/v15 standard: prevdoc_docname set when doctype is Quotation
		("prevdoc_doctype", "prevdoc_docname"),
	]

	for doctype_field, name_field in candidate_fields:
		for item in self.items:
			doctype_val = getattr(item, doctype_field, None)
			name_val = getattr(item, name_field, None)
			if doctype_val == "Quotation" and name_val:
				if frappe.db.exists("Quotation", name_val):
					return name_val

	# Fallback: check any field on the SO item that directly holds a Quotation name
	fallback_fields = ["quotation", "against_quotation", "quotation_name"]
	for item in self.items:
		for field in fallback_fields:
			val = getattr(item, field, None)
			if val and frappe.db.exists("Quotation", val):
				return val

	return None


def copy_multi_year_data_from_quotation(self):
	"""
	When a Sales Order is created from a License Renewal Quotation, carry forward:
	  - custom_quotation_type
	  - custom_license_renewal_items (full child table)
	  - Year 2 and Year 3 totals, taxes, and grand totals
	"""
	quotation_name = _find_source_quotation(self)

	if not quotation_name:
		return

	try:
		quotation = frappe.get_doc("Quotation", quotation_name)
	except frappe.DoesNotExistError:
		return

	# Only carry forward if this is a License Renewal quotation
	if getattr(quotation, "custom_quotation_type", None) != "License Renewal":
		return

	# --- Header Fields ---
	self.custom_quotation_type = quotation.custom_quotation_type
	self.custom_total_year_2 = flt(quotation.custom_total_year_2)
	self.custom_total_year_3 = flt(quotation.custom_total_year_3)
	self.custom_total_taxes_and_charges_year_2 = flt(quotation.custom_total_taxes_and_charges_year_2)
	self.custom_total_taxes_and_charges_year_3 = flt(quotation.custom_total_taxes_and_charges_year_3)
	self.custom_grand_total_year_2 = flt(quotation.custom_grand_total_year_2)
	self.custom_grand_total_year_3 = flt(quotation.custom_grand_total_year_3)

	# --- License Renewal Items child table ---
	self.set("custom_license_renewal_items", [])
	for row in quotation.custom_license_renewal_items:
		self.append("custom_license_renewal_items", {
			"main_item_code": row.main_item_code,
			"item_name": row.item_name,
			"qty": row.qty,
			"uom": row.uom,
			"part_number": row.part_number,
			"custom_serial_no": row.custom_serial_no,
			"description": row.description,
			"shipping": flt(row.shipping),
			"fx": flt(row.fx),
			"markup": flt(row.markup),
			"clearing": flt(row.clearing),
			"disti_quote": flt(row.disti_quote),
			"disti_quote_total": flt(row.disti_quote_total),
			"multiplier": flt(row.multiplier),
			"rate": flt(row.rate),
			"amount": flt(row.amount),
			"year_total_2": flt(row.year_total_2),
			"year_total_3": flt(row.year_total_3),
		})

	# --- Year 2 taxes child table ---
	self.set("custom_sales_taxes_and_charges_year_2", [])
	for tax in quotation.custom_sales_taxes_and_charges_year_2:
		self.append("custom_sales_taxes_and_charges_year_2", {
			"charge_type": tax.charge_type,
			"row_id": tax.row_id,
			"description": tax.description,
			"account_head": tax.account_head,
			"rate": flt(tax.rate),
			"tax_amount": flt(tax.tax_amount),
			"total": flt(tax.total),
		})

	# --- Year 3 taxes child table ---
	self.set("custom_sales_taxes_and_charges_year_3", [])
	for tax in quotation.custom_sales_taxes_and_charges_year_3:
		self.append("custom_sales_taxes_and_charges_year_3", {
			"charge_type": tax.charge_type,
			"row_id": tax.row_id,
			"description": tax.description,
			"account_head": tax.account_head,
			"rate": flt(tax.rate),
			"tax_amount": flt(tax.tax_amount),
			"total": flt(tax.total),
		})
