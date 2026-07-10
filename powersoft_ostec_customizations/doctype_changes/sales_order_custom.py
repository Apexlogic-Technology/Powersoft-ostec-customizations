import frappe
from frappe.utils import flt


def onload(self, method=None):
	"""Copy multi-year license renewal data when the Sales Order is loaded (newly mapped document)."""
	if self.is_new():
		copy_multi_year_data_from_quotation(self)


def before_insert(self, method=None):
	"""Copy multi-year license renewal data from the source Quotation when a Sales Order is created."""
	copy_multi_year_data_from_quotation(self)


def before_save(self, method=None):
	"""
	DIAGNOSTIC VERSION — remove after confirming fix works.
	"""
	if self.is_new() or not getattr(self, "custom_quotation_type", None):
		# Collect item link fields for diagnosis
		item_info = []
		for item in self.items[:3]:  # first 3 items only
			item_info.append({
				"prevdoc_doctype": getattr(item, "prevdoc_doctype", "—"),
				"prevdoc_docname": getattr(item, "prevdoc_docname", "—"),
				"against_quotation": getattr(item, "against_quotation", "—"),
				"quotation": getattr(item, "quotation", "—"),
			})
		quotation_name = _find_source_quotation(self)
		# Also peek at the quotation type if found
		q_type = None
		if quotation_name:
			try:
				q_type = frappe.db.get_value("Quotation", quotation_name, "custom_quotation_type")
			except Exception:
				q_type = "ERROR reading type"
		frappe.msgprint(
			f"<b>DIAGNOSTIC — before_save on Sales Order</b><br>"
			f"is_new={self.is_new()}<br>"
			f"so.custom_quotation_type={getattr(self, 'custom_quotation_type', None)!r}<br>"
			f"quotation_found={quotation_name!r}<br>"
			f"quotation.custom_quotation_type={q_type!r}<br>"
			f"item_links={item_info}",
			title="Tax Copy Debug",
			indicator="blue"
		)
		if quotation_name:
			copy_multi_year_data_from_quotation(self)


def after_save(self, method=None):
	"""
	DIAGNOSTIC after_save — query database directly to check if rows exist.
	"""
	# Query child table directly from database
	year_2_db_rows = frappe.db.get_all(
		"Sales Taxes and Charges",
		filters={
			"parent": self.name,
			"parenttype": "Sales Order",
			"parentfield": "custom_sales_taxes_and_charges_year_2"
		},
		fields=["name", "description", "tax_amount"]
	)
	year_3_db_rows = frappe.db.get_all(
		"Sales Taxes and Charges",
		filters={
			"parent": self.name,
			"parenttype": "Sales Order",
			"parentfield": "custom_sales_taxes_and_charges_year_3"
		},
		fields=["name", "description", "tax_amount"]
	)
	item_db_rows = frappe.db.get_all(
		"License Renewal Items",
		filters={
			"parent": self.name,
			"parenttype": "Sales Order",
			"parentfield": "custom_license_renewal_items"
		},
		fields=["name", "item_name", "amount"]
	)
	frappe.msgprint(
		f"<b>DIAGNOSTIC — after_save in database</b><br>"
		f"Sales Order: {self.name}<br>"
		f"DB License Items count: {len(item_db_rows)}<br>"
		f"DB Year 2 Tax count: {len(year_2_db_rows)}<br>"
		f"DB Year 3 Tax count: {len(year_3_db_rows)}<br>"
		f"DB Year 2 Rows: {year_2_db_rows}<br>"
		f"DB Year 3 Rows: {year_3_db_rows}",
		title="Database Save Verification",
		indicator="green"
	)


def _find_source_quotation(self):
	"""
	Robustly detect the source Quotation name from a newly created Sales Order.
	ERPNext sets prevdoc_docname on SO items but may leave prevdoc_doctype empty.
	We verify by checking DB existence directly instead of relying on prevdoc_doctype.
	Returns the Quotation name (string) or None if not found.
	"""
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

	# --- DIAGNOSTIC: show what the quotation actually has ---
	frappe.msgprint(
		f"<b>DIAGNOSTIC — copy_multi_year_data_from_quotation</b><br>"
		f"Quotation: {quotation_name}<br>"
		f"custom_license_renewal_items rows: {len(quotation.custom_license_renewal_items)}<br>"
		f"custom_sales_taxes_year_2 rows: {len(quotation.custom_sales_taxes_and_charges_year_2)}<br>"
		f"custom_sales_taxes_year_3 rows: {len(quotation.custom_sales_taxes_and_charges_year_3)}<br>"
		f"custom_total_year_2: {getattr(quotation, 'custom_total_year_2', 'MISSING')}<br>"
		f"custom_total_year_3: {getattr(quotation, 'custom_total_year_3', 'MISSING')}<br>"
		f"custom_grand_total_year_2: {getattr(quotation, 'custom_grand_total_year_2', 'MISSING')}<br>"
		f"custom_grand_total_year_3: {getattr(quotation, 'custom_grand_total_year_3', 'MISSING')}",
		title="Copy Function Debug",
		indicator="orange"
	)
	# --- END DIAGNOSTIC ---


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
