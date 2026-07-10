import frappe
from frappe.utils import flt


def onload(self, method=None):
	"""Copy multi-year license renewal data when the Sales Invoice is loaded (newly mapped document)."""
	if self.is_new():
		copy_multi_year_data_from_sales_order(self)


def before_insert(self, method=None):
	"""Copy multi-year license renewal data from the source Sales Order when a Sales Invoice is created."""
	copy_multi_year_data_from_sales_order(self)


def before_save(self, method=None):
	"""
	Copy multi-year license renewal data on first save of a new Sales Invoice.
	This is the reliable hook — all sales_order links on items are guaranteed to be
	resolved by the time before_save fires, unlike before_insert.
	Guarded so it only runs when the doc is new and the totals are not yet populated,
	preventing redundant re-copy on subsequent saves of an existing Sales Invoice.
	"""
	if self.is_new() and not flt(self.custom_grand_total_year_2) and not flt(self.custom_grand_total_year_3):
		copy_multi_year_data_from_sales_order(self)


def copy_multi_year_data_from_sales_order(self):
	"""
	When a Sales Invoice is created from a Sales Order that originated from a License Renewal Quotation,
	carry forward all multi-year data:
	  - custom_quotation_type
	  - custom_license_renewal_items (full child table)
	  - Year 2 and Year 3 totals, taxes, and grand totals
	"""
	# Identify the source Sales Order via the items' sales_order link
	sales_order_name = None
	for item in self.items:
		if getattr(item, "sales_order", None):
			sales_order_name = item.sales_order
			break

	if not sales_order_name:
		return

	try:
		sales_order = frappe.get_doc("Sales Order", sales_order_name)
	except frappe.DoesNotExistError:
		return

	# Only carry forward if this is a License Renewal
	if getattr(sales_order, "custom_quotation_type", None) != "License Renewal":
		return

	# --- Header Fields ---
	self.custom_quotation_type = sales_order.custom_quotation_type
	self.custom_total_year_2 = flt(sales_order.custom_total_year_2)
	self.custom_total_year_3 = flt(sales_order.custom_total_year_3)
	self.custom_total_taxes_and_charges_year_2 = flt(sales_order.custom_total_taxes_and_charges_year_2)
	self.custom_total_taxes_and_charges_year_3 = flt(sales_order.custom_total_taxes_and_charges_year_3)
	self.custom_grand_total_year_2 = flt(sales_order.custom_grand_total_year_2)
	self.custom_grand_total_year_3 = flt(sales_order.custom_grand_total_year_3)


	# --- Year 2 taxes child table ---
	self.set("custom_sales_taxes_and_charges_year_2", [])
	for tax in sales_order.custom_sales_taxes_and_charges_year_2:
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
	for tax in sales_order.custom_sales_taxes_and_charges_year_3:
		self.append("custom_sales_taxes_and_charges_year_3", {
			"charge_type": tax.charge_type,
			"row_id": tax.row_id,
			"description": tax.description,
			"account_head": tax.account_head,
			"rate": flt(tax.rate),
			"tax_amount": flt(tax.tax_amount),
			"total": flt(tax.total),
		})
