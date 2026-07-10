frappe.ui.form.on("Payment Entry", {
	onload(frm) {
		if (frm.is_new()) {
			copy_multi_year_data_from_invoice(frm);
		}
	},
	refresh(frm) {
		if (frm.is_new()) {
			copy_multi_year_data_from_invoice(frm);
		}
	}
});

function copy_multi_year_data_from_invoice(frm) {
	// Find referenced Sales Invoice
	let sales_invoice = null;
	if (frm.doc.references) {
		for (let ref of frm.doc.references) {
			if (ref.reference_doctype === "Sales Invoice" && ref.reference_name) {
				sales_invoice = ref.reference_name;
				break;
			}
		}
	}

	if (!sales_invoice) return;

	// Fetch Sales Invoice data and copy it
	frappe.db.get_doc("Sales Invoice", sales_invoice).then(invoice => {
		if (invoice.custom_quotation_type === "License Renewal") {
			frm.set_value("custom_quotation_type", invoice.custom_quotation_type);
			frm.set_value("custom_total_year_2", invoice.custom_total_year_2);
			frm.set_value("custom_total_year_3", invoice.custom_total_year_3);
			frm.set_value("custom_total_taxes_and_charges_year_2", invoice.custom_total_taxes_and_charges_year_2);
			frm.set_value("custom_total_taxes_and_charges_year_3", invoice.custom_total_taxes_and_charges_year_3);
			frm.set_value("custom_grand_total_year_2", invoice.custom_grand_total_year_2);
			frm.set_value("custom_grand_total_year_3", invoice.custom_grand_total_year_3);

			// Calculate sum of Year 1 (grand_total), Year 2, and Year 3 grand totals
			let total_all_years = flt(invoice.grand_total) + flt(invoice.custom_grand_total_year_2) + flt(invoice.custom_grand_total_year_3);
			
			frm.set_value("paid_amount", total_all_years);
			frm.set_value("received_amount", total_all_years);

			// Also update the allocated amount on the invoice reference line
			if (frm.doc.references) {
				for (let ref of frm.doc.references) {
					if (ref.reference_doctype === "Sales Invoice" && ref.reference_name === sales_invoice) {
						frappe.model.set_value(ref.doctype, ref.name, "allocated_amount", total_all_years);
						break;
					}
				}
			}

			// Clear and copy Year 2 taxes
			frm.clear_table("custom_sales_taxes_and_charges_year_2");
			if (invoice.custom_sales_taxes_and_charges_year_2) {
				for (let tax of invoice.custom_sales_taxes_and_charges_year_2) {
					let row = frm.add_child("custom_sales_taxes_and_charges_year_2");
					row.charge_type = tax.charge_type;
					row.row_id = tax.row_id;
					row.description = tax.description;
					row.account_head = tax.account_head;
					row.rate = tax.rate;
					row.tax_amount = tax.tax_amount;
					row.total = tax.total;
				}
			}

			// Clear and copy Year 3 taxes
			frm.clear_table("custom_sales_taxes_and_charges_year_3");
			if (invoice.custom_sales_taxes_and_charges_year_3) {
				for (let tax of invoice.custom_sales_taxes_and_charges_year_3) {
					let row = frm.add_child("custom_sales_taxes_and_charges_year_3");
					row.charge_type = tax.charge_type;
					row.row_id = tax.row_id;
					row.description = tax.description;
					row.account_head = tax.account_head;
					row.rate = tax.rate;
					row.tax_amount = tax.tax_amount;
					row.total = tax.total;
				}
			}

			frm.refresh_fields([
				"custom_quotation_type",
				"custom_total_year_2",
				"custom_total_year_3",
				"custom_total_taxes_and_charges_year_2",
				"custom_total_taxes_and_charges_year_3",
				"custom_grand_total_year_2",
				"custom_grand_total_year_3",
				"custom_sales_taxes_and_charges_year_2",
				"custom_sales_taxes_and_charges_year_3"
			]);
		}
	});
}
