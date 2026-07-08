import frappe
from frappe.utils import flt

def validate(self, method=None):
    copy_all_rates(self)

def on_submit(self, method=None):
	copy_all_rates(self)

def copy_all_rates(self):
    for row in self.items:
        row.custom_disti_quote = flt(row.rate)