import frappe
from frappe.utils import flt


def onload(self, method=None):
	"""Copy multi-year license renewal data when the Sales Order is loaded (newly mapped document)."""
	if self.is_new():
		copy_multi_year_data_from_quotation(self)

	if getattr(self, "custom_quotation_type", None) == "License Renewal":
		self.custom_total_year_1 = flt(self.total)
		self.custom_total_taxes_and_charges_year_1 = flt(self.total_taxes_and_charges)
		self.custom_grand_total_year_1 = flt(self.grand_total)
		self.custom_grand_total_all_years = flt(self.grand_total) + flt(self.custom_grand_total_year_2) + flt(self.custom_grand_total_year_3)


def before_insert(self, method=None):
	"""before_save is the reliable hook; before_insert is kept for completeness but does not run copy."""
	pass


def before_save(self, method=None):
	"""
	Copy multi-year license renewal data on first save of a new Sales Order.
	This is the reliable hook — all prevdoc links on items are guaranteed to be
	resolved by the time before_save fires, unlike before_insert.
	Guarded so it only runs when the doc is new and the totals are not yet populated,
	preventing redundant re-copy on subsequent saves of an existing Sales Order.
	"""
	try:
		# Log to DB for visibility
		msg = f"SO before_save: is_new={self.is_new()}, Year 2 Total={self.custom_grand_total_year_2}, Year 3 Total={self.custom_grand_total_year_3}"
		frappe.log_error(msg, "SO before_save debug")
	except Exception:
		pass

	if self.is_new() and not self.get("custom_sales_taxes_and_charges_year_2"):
		quotation_name = _find_source_quotation(self)
		if quotation_name:
			copy_multi_year_data_from_quotation(self)

	if getattr(self, "custom_quotation_type", None) == "License Renewal":
		self.custom_total_year_1 = flt(self.total)
		self.custom_total_taxes_and_charges_year_1 = flt(self.total_taxes_and_charges)
		self.custom_grand_total_year_1 = flt(self.grand_total)
		self.custom_grand_total_all_years = flt(self.grand_total) + flt(self.custom_grand_total_year_2) + flt(self.custom_grand_total_year_3)


def _find_source_quotation(self):
	"""
	Robustly detect the source Quotation name from a newly created Sales Order.
	ERPNext sets prevdoc_docname on SO items but may leave prevdoc_doctype empty.
	We verify by checking DB existence directly instead of relying on prevdoc_doctype.
	Returns the Quotation name (string) or None if not found.
	"""
	try:
		# Log fields on first item for debugging
		if self.items:
			first = self.items[0]
			fields = {k: v for k, v in first.as_dict().items() if v}
			frappe.log_error(f"First item fields: {fields}", "SO item fields debug")
	except Exception:
		pass

	# Primary: prevdoc_docname — present in all ERPNext versions, verified via DB
	for item in self.items:
		val = getattr(item, "prevdoc_docname", None)
		if val and frappe.db.exists("Quotation", val):
			return val

	# Secondary: explicit prevdoc_doctype + prevdoc_docname pairing
	for item in self.items:
		doctype_val = getattr(item, "prevdoc_doctype", None)
		name_val = getattr(item, "prevdoc_docname", None)
		if doctype_val == "Quotation" and name_val:
			if frappe.db.exists("Quotation", name_val):
				return name_val

	# Tertiary: other field names used in some ERPNext versions
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
	  - Year 2 and Year 3 totals, taxes, and grand totals
	"""
	try:
		quotation_name = _find_source_quotation(self)
		if not quotation_name:
			frappe.log_error("Could not find source quotation", "SO copy: no source")
			return

		try:
			quotation = frappe.get_doc("Quotation", quotation_name)
		except frappe.DoesNotExistError:
			frappe.log_error(f"Quotation {quotation_name} not found in DB", "SO copy: missing doc")
			return

		# Only carry forward if this is a License Renewal quotation
		qtype = getattr(quotation, "custom_quotation_type", None)
		frappe.log_error(f"Source Quotation: {quotation_name}, type={qtype}", "SO copy: quotation type")
		
		if qtype != "License Renewal":
			return

		self.custom_quotation_type = quotation.custom_quotation_type
		self.custom_total_year_2 = flt(quotation.custom_total_year_2)
		self.custom_total_year_3 = flt(quotation.custom_total_year_3)
		self.custom_total_taxes_and_charges_year_2 = flt(quotation.custom_total_taxes_and_charges_year_2)
		self.custom_total_taxes_and_charges_year_3 = flt(quotation.custom_total_taxes_and_charges_year_3)
		self.custom_grand_total_year_2 = flt(quotation.custom_grand_total_year_2)
		self.custom_grand_total_year_3 = flt(quotation.custom_grand_total_year_3)
		self.custom_grand_total_all_years = flt(quotation.custom_grand_total_all_years)

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
		
		frappe.log_error(f"Copy successful! type={self.custom_quotation_type}, Y2 total={self.custom_grand_total_year_2}", "SO copy: success")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Sales Order: multi-year copy from Quotation failed")
