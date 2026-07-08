frappe.ui.form.on('Supplier Quotation', {
	validate(frm) {
		copy_all_rates(frm)
	},
	on_submit(frm) {
		copy_all_rates(frm)
	},
})

frappe.ui.form.on('Supplier Quotation Item', {
	rate(frm, cdt, cdn) {
		copy_all_rates(frm)
	}
})


function copy_all_rates(frm){
    for (let row of frm.doc.items){
        row.custom_disti_quote = row.rate
    }
    frm.refresh_field("items")
}
