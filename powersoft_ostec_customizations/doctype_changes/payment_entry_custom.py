import frappe
from frappe.utils import flt


def onload(self, method=None):
	"""Copy multi-year license renewal data when the Payment Entry is loaded (newly mapped document)."""
	if self.is_new():
		copy_multi_year_data_from_sales_invoice(self)


def before_insert(self, method=None):
	"""before_save is the reliable hook; before_insert is kept for completeness but does not run copy."""
	pass


def before_save(self, method=None):
	"""
	Copy multi-year data on first save of a new Payment Entry.
	Guarded so it only runs when the doc is new and the totals are not yet populated,
	preventing redundant re-copy on subsequent saves.
	"""
	if self.is_new() and not flt(self.custom_grand_total_year_2) and not flt(self.custom_grand_total_year_3):
		copy_multi_year_data_from_sales_invoice(self)


def copy_multi_year_data_from_sales_invoice(self):
	"""
	When a Payment Entry is created for a License Renewal Sales Invoice,
	carry forward all multi-year data:
	  - custom_quotation_type
	  - Year 2 and Year 3 totals, taxes, and grand totals
	"""
	try:
		sales_invoice_name = None
		for ref in self.get("references", []):
			if ref.reference_doctype == "Sales Invoice" and ref.reference_name:
				sales_invoice_name = ref.reference_name
				break

		if not sales_invoice_name:
			return

		try:
			sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice_name)
		except frappe.DoesNotExistError:
			frappe.log_error(f"Payment Entry copy: Sales Invoice {sales_invoice_name} not found", "PE Multi-year copy")
			return

		# Only carry forward if this is a License Renewal
		if getattr(sales_invoice, "custom_quotation_type", None) != "License Renewal":
			return

		# --- Header Fields ---
		self.custom_quotation_type = sales_invoice.custom_quotation_type
		self.custom_total_year_2 = flt(sales_invoice.custom_total_year_2)
		self.custom_total_year_3 = flt(sales_invoice.custom_total_year_3)
		self.custom_total_taxes_and_charges_year_2 = flt(sales_invoice.custom_total_taxes_and_charges_year_2)
		self.custom_total_taxes_and_charges_year_3 = flt(sales_invoice.custom_total_taxes_and_charges_year_3)
		self.custom_grand_total_year_2 = flt(sales_invoice.custom_grand_total_year_2)
		self.custom_grand_total_year_3 = flt(sales_invoice.custom_grand_total_year_3)

		# --- Year 2 taxes child table ---
		self.set("custom_sales_taxes_and_charges_year_2", [])
		for tax in sales_invoice.custom_sales_taxes_and_charges_year_2:
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
		for tax in sales_invoice.custom_sales_taxes_and_charges_year_3:
			self.append("custom_sales_taxes_and_charges_year_3", {
				"charge_type": tax.charge_type,
				"row_id": tax.row_id,
				"description": tax.description,
				"account_head": tax.account_head,
				"rate": flt(tax.rate),
				"tax_amount": flt(tax.tax_amount),
				"total": flt(tax.total),
			})
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Payment Entry: multi-year copy from Sales Invoice failed")
