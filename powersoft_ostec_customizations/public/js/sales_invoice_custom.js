frappe.ui.form.on("Sales Invoice", {
	onload(frm) {
		toggle_totals(frm);
	},
	refresh(frm) {
		toggle_totals(frm);
	},
	custom_quotation_type(frm) {
		toggle_totals(frm);
	}
});

function toggle_totals(frm) {
	let is_renewal = (frm.doc.custom_quotation_type === "License Renewal");
	
	let standard_fields = [
		"total",
		"grand_total",
		"rounding_adjustment",
		"rounded_total",
		"in_words",
		"disable_rounded_total",
		"total_advance",
		"outstanding_amount",
		"write_off_amount"
	];
	
	for (let f of standard_fields) {
		if (frm.fields_dict[f]) {
			frm.toggle_display(f, !is_renewal);
		}
	}
	
	// Show/hide Year 1 custom fields
	frm.toggle_display("custom_total_year_1", is_renewal);
	frm.toggle_display("custom_total_taxes_and_charges_year_1", is_renewal);
	frm.toggle_display("custom_grand_total_year_1", is_renewal);
}
