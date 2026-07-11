import frappe
from frappe.utils import flt, cint


def get_currency_precision():
	"""Return the system currency precision (number of decimal places for currency fields)."""
	precision = cint(frappe.db.get_default("currency_precision"))
	return precision if precision else 2


def onload(self, method=None):
	if getattr(self, "custom_quotation_type", None) == "License Renewal":
		self.custom_total_year_1 = flt(self.total)
		self.custom_total_taxes_and_charges_year_1 = flt(self.total_taxes_and_charges)
		self.custom_grand_total_year_1 = flt(self.grand_total)
		self.custom_grand_total_all_years = flt(self.grand_total) + flt(self.custom_grand_total_year_2) + flt(self.custom_grand_total_year_3)


def before_save(self, method=None):
	calcs(self)
	copy_items_in_main_table(self)
	self.run_method("set_missing_values")
	self.run_method("calculate_taxes_and_totals")
	_apply_totals_safety_net(self)
	calculate_custom_taxes_year_2(self)
	calculate_custom_taxes_year_3(self)
	self.custom_total_year_1 = flt(self.total)
	self.custom_total_taxes_and_charges_year_1 = flt(self.total_taxes_and_charges)
	self.custom_grand_total_year_1 = flt(self.grand_total)
	self.custom_grand_total_year_2 = flt(self.custom_total_year_2) + flt(self.custom_total_taxes_and_charges_year_2)
	self.custom_grand_total_year_3 = flt(self.custom_total_year_3) + flt(self.custom_total_taxes_and_charges_year_3)
	self.custom_grand_total_all_years = flt(self.grand_total) + flt(self.custom_grand_total_year_2) + flt(self.custom_grand_total_year_3)
	# Ensure items have valid conversion_factor and stock_qty regardless of Item master UOM setup
	for item in self.items:
		item.conversion_factor = flt(item.conversion_factor) or 1.0
		item.stock_qty = flt(item.qty) * item.conversion_factor
		item.ordered_qty = flt(item.ordered_qty) or 0.0
		item.billed_amt = flt(item.billed_amt) or 0.0
		item.delivered_qty = flt(item.delivered_qty) or 0.0


def validate(self, method=None):
	"""
	validate() runs on every Save AND on Submit.
	Do NOT rebuild the items table here — that is done in before_save (Save)
	and before_submit (Submit) so that ERPNext's own set_missing_values
	cannot zero-out conversion_factor / stock_qty between our rebuild and
	the mandatory-field check.
	"""
	# --- DIAGNOSTIC: log item state BEFORE our changes ---
	try:
		debug_lines = [f"[VALIDATE] docstatus={self.docstatus} name={self.name}"]
		for i, item in enumerate(self.items):
			debug_lines.append(
				f"  item[{i}] code={item.item_code} qty={item.qty} "
				f"uom={item.uom} cf={item.conversion_factor} stock_qty={item.stock_qty}"
			)
		frappe.logger("quotation_debug").info("\n".join(debug_lines))
	except Exception:
		pass
	# --- END DIAGNOSTIC ---

	_apply_totals_safety_net(self)
	calculate_custom_taxes_year_2(self)
	calculate_custom_taxes_year_3(self)
	self.custom_total_year_1 = flt(self.total)
	self.custom_total_taxes_and_charges_year_1 = flt(self.total_taxes_and_charges)
	self.custom_grand_total_year_1 = flt(self.grand_total)
	self.custom_grand_total_year_2 = flt(self.custom_total_year_2) + flt(self.custom_total_taxes_and_charges_year_2)
	self.custom_grand_total_year_3 = flt(self.custom_total_year_3) + flt(self.custom_total_taxes_and_charges_year_3)
	self.custom_grand_total_all_years = flt(self.grand_total) + flt(self.custom_grand_total_year_2) + flt(self.custom_grand_total_year_3)
	# Enforce correct values — our hook runs AFTER ERPNext's validate which may zero conversion_factor
	for item in self.items:
		item.conversion_factor = flt(item.conversion_factor) or 1.0
		item.stock_qty = flt(item.qty) * item.conversion_factor
		item.ordered_qty = flt(item.ordered_qty) or 0.0
		item.billed_amt = flt(item.billed_amt) or 0.0
		item.delivered_qty = flt(item.delivered_qty) or 0.0

	# --- DIAGNOSTIC: log item state AFTER our changes ---
	try:
		debug_lines2 = [f"[VALIDATE-AFTER] docstatus={self.docstatus}"]
		for i, item in enumerate(self.items):
			debug_lines2.append(
				f"  item[{i}] code={item.item_code} qty={item.qty} "
				f"uom={item.uom} cf={item.conversion_factor} stock_qty={item.stock_qty}"
			)
		frappe.logger("quotation_debug").info("\n".join(debug_lines2))
	except Exception:
		pass
	# --- END DIAGNOSTIC ---


def before_submit(self, method=None):
	"""
	Rebuild the items table (same as before_save does for Save) so that
	conversion_factor and stock_qty are present when ERPNext validates
	mandatory fields on Submit.
	"""
	calcs(self)
	copy_items_in_main_table(self)
	# Unconditionally enforce conversion_factor and stock_qty — do not
	# rely on the Item master having a UOM conversion defined.
	for item in self.items:
		item.conversion_factor = flt(item.conversion_factor) or 1.0
		item.stock_qty = flt(item.qty) * item.conversion_factor
		item.ordered_qty = flt(item.ordered_qty) or 0.0
		item.billed_amt = flt(item.billed_amt) or 0.0
		item.delivered_qty = flt(item.delivered_qty) or 0.0


def on_submit(self, method=None):
	calcs(self)


def calcs(self):
	precision = get_currency_precision()
	ch_tab_name = get_items_table_name(self)
	if ch_tab_name:
		for row in self.get(ch_tab_name, []):
			markup = flt(row.markup) / 100
			clearing = flt(row.clearing) / 100
			# Protect against zero FX or zero qty
			fx = flt(row.fx) if flt(row.fx) > 0 else 1
			qty = flt(row.qty) if flt(row.qty) > 0 else 1
			multiplier = (1 + markup) * fx
			row.multiplier = multiplier
			# Round all monetary results to currency precision to prevent float drift accumulation
			row.disti_quote_total = flt((flt(row.disti_quote) + flt(row.shipping)) * qty, precision)
			row.rate = flt(
				flt(row.disti_quote) * multiplier * (1 + clearing)
				+ flt(row.shipping) * multiplier * (1 + clearing),
				precision
			)
			row.amount = flt(row.rate * qty, precision)


def copy_items_in_main_table(self):
	self.set('items', [])
	ch_tab_name = get_items_table_name(self)
	if ch_tab_name:
		for row in self.get(ch_tab_name, []):
			new_row = {}
			new_row["item_code"] = row.get('main_item_code')
			new_row["item_name"] = row.get('item_name')
			new_row["custom_part_number"] = row.get('part_number')
			new_row["custom_serial_no"] = row.get('custom_serial_no')
			new_row["description"] = row.get('description')
			new_row["qty"] = row.get('qty')
			new_row["custom_disti_quote"] = row.get('disti_quote')
			new_row["custom_disti_quote_total"] = row.get('disti_quote_total')
			new_row["custom_multiplier"] = row.get('multiplier')
			new_row["custom_shipping"] = row.get('shipping')
			new_row["custom_markup"] = row.get('markup')
			new_row["custom_fx"] = row.get('fx')
			new_row["custom_clearing"] = row.get('clearing')
			new_row["rate"] = row.get('rate')
			new_row["amount"] = row.get('amount')
			new_row["uom"] = row.get('uom')
			new_row["conversion_factor"] = flt(row.get('conversion_factor')) or 1.0
			new_row["stock_qty"] = flt(row.get('qty')) or 0.0
			new_row["ordered_qty"] = flt(row.get('ordered_qty')) or 0.0
			new_row["billed_amt"] = flt(row.get('billed_amt')) or 0.0
			new_row["delivered_qty"] = flt(row.get('delivered_qty')) or 0.0
			# Set stock_qty on the object directly so the ORM cannot silently drop it
			appended = self.append("items", new_row)
			appended.stock_qty = flt(row.get('qty')) or 0.0
			appended.conversion_factor = flt(row.get('conversion_factor')) or 1.0
			appended.ordered_qty = flt(row.get('ordered_qty')) or 0.0
			appended.billed_amt = flt(row.get('billed_amt')) or 0.0
			appended.delivered_qty = flt(row.get('delivered_qty')) or 0.0


def get_items_table_name(self):
	ch_tab_name = None
	if (self.custom_quotation_type == "Standard Quotation"):ch_tab_name = "custom_standard_quotation_items"
	if (self.custom_quotation_type == "License Renewal"):ch_tab_name = "custom_license_renewal_items"
	return ch_tab_name


def _apply_totals_safety_net(self):
	"""
	Recalculate and overwrite all ERPNext totals from the custom items table (source of truth).
	Called from validate() so it also runs during on_submit (ERPNext calls validate before submit).
	Also called from before_save after calculate_taxes_and_totals for extra protection.
	"""
	try:
		precision = get_currency_precision()
		# conversion_rate converts document currency -> company base currency (e.g. USD -> GHS)
		conversion_rate = flt(self.conversion_rate) if flt(self.conversion_rate) > 0 else 1.0
		ch_tab_name = get_items_table_name(self)
		if not ch_tab_name:
			return

		# Sum already-rounded amounts — result is exact
		correct_total = flt(sum(flt(row.amount) for row in self.get(ch_tab_name, [])), precision)

		# Document-currency totals
		self.total = correct_total
		self.net_total = correct_total
		# Base-currency totals (company currency) — apply conversion rate
		self.base_total = flt(correct_total * conversion_rate, precision)
		self.base_net_total = flt(correct_total * conversion_rate, precision)

		# Recalculate taxes based on correct total
		total_tax = 0
		total_with_tax = correct_total

		for tax in self.taxes:
			if tax.charge_type == "Actual":
				tax_amount = flt(tax.tax_amount, precision)
			else:
				tax_amount = flt((correct_total * flt(tax.rate)) / 100, precision)

			tax.tax_amount = tax_amount
			tax.base_tax_amount = flt(tax_amount * conversion_rate, precision)
			tax.total = flt(total_with_tax + tax_amount, precision)
			tax.base_total = flt(tax.total * conversion_rate, precision)
			total_tax = flt(total_tax + tax_amount, precision)
			total_with_tax = tax.total

		# Set the correct tax totals
		self.total_taxes_and_charges = total_tax
		self.base_total_taxes_and_charges = flt(total_tax * conversion_rate, precision)

		# Set the correct grand total (document currency)
		grand = flt(correct_total + total_tax, precision)
		self.grand_total = grand
		self.rounded_total = flt(round(grand, 0), 0)
		# Set the correct grand total (base/company currency)
		self.base_grand_total = flt(grand * conversion_rate, precision)
		self.base_rounded_total = flt(round(grand * conversion_rate, 0), 0)

	except Exception:
		frappe.log_error(frappe.get_traceback(), "Quotation: totals safety-net failed")


def calculate_custom_taxes_year_2(self):
	try:
		precision = get_currency_precision()
		total_amount = flt(sum(flt(item.year_total_2) for item in self.custom_license_renewal_items if item.year_total_2), precision)
		total_tax = 0
		total_with_tax = total_amount
		self.custom_total_year_2 = total_amount
		custom_sales_taxes_and_charges_year_2 = []
		for tax in self.taxes:
			if tax.charge_type == "Actual":
				tax_amount = flt(tax.tax_amount, precision)
			else:
				tax_amount = flt((total_amount * flt(tax.rate)) / 100, precision)
			total_tax = flt(total_tax + tax_amount, precision)
			total_with_tax = flt(total_with_tax + tax_amount, precision)
			custom_tax_row = {
				'charge_type': tax.charge_type,
				'row_id': tax.row_id,
				'description': tax.description,
				'account_head': tax.account_head,
				'rate': tax.rate,
				'tax_amount': tax_amount,
				'total': total_with_tax
			}
			custom_sales_taxes_and_charges_year_2.append(custom_tax_row)
		self.set('custom_sales_taxes_and_charges_year_2', [])
		for custom_tax in custom_sales_taxes_and_charges_year_2:
			self.append('custom_sales_taxes_and_charges_year_2', {
				'charge_type': custom_tax['charge_type'],
				'row_id': custom_tax['row_id'],
				'description': custom_tax['description'],
				'account_head': custom_tax['account_head'],
				'rate': custom_tax['rate'],
				'tax_amount': custom_tax['tax_amount'],
				'total': custom_tax['total']
			})
		self.custom_total_taxes_and_charges_year_2 = total_tax
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Quotation: Year 2 tax calculation failed")


def calculate_custom_taxes_year_3(self):
	try:
		precision = get_currency_precision()
		total_amount = flt(sum(flt(item.year_total_3) for item in self.custom_license_renewal_items if item.year_total_3), precision)
		total_tax = 0
		total_with_tax = total_amount
		self.custom_total_year_3 = total_amount
		custom_sales_taxes_and_charges_year_3 = []
		for tax in self.taxes:
			if tax.charge_type == "Actual":
				tax_amount = flt(tax.tax_amount, precision)
			else:
				tax_amount = flt((total_amount * flt(tax.rate)) / 100, precision)
			total_tax = flt(total_tax + tax_amount, precision)
			total_with_tax = flt(total_with_tax + tax_amount, precision)
			custom_tax_row = {
				'charge_type': tax.charge_type,
				'row_id': tax.row_id,
				'description': tax.description,
				'account_head': tax.account_head,
				'rate': tax.rate,
				'tax_amount': tax_amount,
				'total': total_with_tax
			}
			custom_sales_taxes_and_charges_year_3.append(custom_tax_row)
		self.set('custom_sales_taxes_and_charges_year_3', [])
		for custom_tax in custom_sales_taxes_and_charges_year_3:
			self.append('custom_sales_taxes_and_charges_year_3', {
				'charge_type': custom_tax['charge_type'],
				'row_id': custom_tax['row_id'],
				'description': custom_tax['description'],
				'account_head': custom_tax['account_head'],
				'rate': custom_tax['rate'],
				'tax_amount': custom_tax['tax_amount'],
				'total': custom_tax['total']
			})
		self.custom_total_taxes_and_charges_year_3 = total_tax
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Quotation: Year 3 tax calculation failed")
