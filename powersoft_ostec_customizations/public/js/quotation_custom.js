frappe.ui.form.on("Quotation", {
	refresh(frm) {
        frm.set_df_property("custom_sales_taxes_and_charges_year_2", "cannot_delete_rows", true);
		frm.set_df_property("custom_sales_taxes_and_charges_year_2", "cannot_add_rows", true);
        frm.set_df_property("custom_sales_taxes_and_charges_year_3", "cannot_delete_rows", true);
		frm.set_df_property("custom_sales_taxes_and_charges_year_3", "cannot_add_rows", true);
        if(frm.doc.__islocal && frm.doc.docstatus == 0){
            let ch_tab_name = get_items_table_name(frm)
            if((frm.doc[ch_tab_name] || []).length == 0){
                get_n_set_items(frm);
            }
        }
	},
    currency(frm) {
        let ch_tab_name = get_items_table_name(frm)
        if((frm.doc[ch_tab_name] || []).length != 0){
            frm.set_value("items", []);
        }
    },
    custom_quotation_type(frm) {
        get_n_set_items(frm);
    },
	// Parent-level add/remove events for Standard Quotation Items
	custom_standard_quotation_items_add(frm) {
		calcs(frm);
	},
	custom_standard_quotation_items_remove(frm) {
		calcs(frm);
	},
	// Parent-level add/remove events for License Renewal Items
	custom_license_renewal_items_add(frm) {
		calcs(frm);
	},
	custom_license_renewal_items_remove(frm) {
		calcs(frm);
	},
	validate(frm) {
		calcs(frm);
	},
	on_submit(frm) {
		calcs(frm);
	},
});

frappe.ui.form.on("Standard Quotation Items", {
    qty(frm) {
        calcs(frm);
    },
    disti_quote(frm) {
        calcs(frm);
    },
    markup(frm) {
        calcs(frm);
    },
    clearing(frm) {
        calcs(frm);
    },
    fx(frm) {
        calcs(frm);
    },
    shipping(frm) {
        calcs(frm);
    },
    before_remove(frm) {
        // Use frappe.after_ajax to run calcs after Frappe completes the row removal
        frappe.after_ajax(() => calcs(frm));
    }
});
frappe.ui.form.on("License Renewal Items", {
	qty(frm) {
		calcs(frm);
	},
	disti_quote(frm) {
		calcs(frm);
	},
	markup(frm) {
		calcs(frm);
	},
	clearing(frm) {
		calcs(frm);
	},
	fx(frm) {
		calcs(frm);
	},
	shipping(frm) {
		calcs(frm);
	},
	before_remove(frm) {
		// Use frappe.after_ajax to run calcs after Frappe completes the row removal
		frappe.after_ajax(() => calcs(frm));
	}
});

function get_n_set_items(frm) {
    check_n_validate_child_tables(frm);
    let ch_tab_name = get_items_table_name(frm)
    if(ch_tab_name){
        frm.set_value(ch_tab_name, [])
        for (let row of frm.doc.items){
            let new_row = {}
            new_row.main_item_code = cstr(row.item_code)
            new_row.item_name = cstr(row.item_name)
            new_row.part_number = cstr(row.custom_part_number)
            new_row.custom_serial_no = cstr(row.custom_serial_no)
            new_row.description = frappe.utils.html2text(cstr(row.description))
            new_row.qty = flt(row.qty)
            new_row.disti_quote = flt(row.custom_disti_quote)
            new_row.disti_quote_total = flt(row.custom_disti_quote_total)
            new_row.multiplier = flt(row.custom_multiplier)
            new_row.shipping = flt(row.custom_shipping)
            new_row.markup = flt(row.custom_markup)
            new_row.fx = flt(row.custom_fx)
            new_row.clearing = flt(row.custom_clearing)
            new_row.rate = flt(row.rate)
            new_row.amount = flt(row.amount)
            frm.add_child(ch_tab_name, new_row);
        }
        frm.refresh_field(ch_tab_name);
    }
    calcs(frm);
}

function calcs(frm) {
    // Read the system currency precision (falls back to 2 if not set)
    const curr_precision = cint(frappe.boot.sysdefaults.currency_precision) || 2;
    frm.set_value("items", [])
    let ch_tab_name = get_items_table_name(frm)
    if(ch_tab_name){
        for (let row of frm.doc[ch_tab_name]) {
            row.description = frappe.utils.html2text(cstr(row.description)) || row.item_name
            // Guard against zero qty and fx to prevent divide-by-zero or zero rates
            row.qty = flt(row.qty) > 0 ? flt(row.qty) : 1
            row.fx = flt(row.fx) > 0 ? flt(row.fx) : 1
            row.disti_quote = flt(row.disti_quote)
            row.shipping = flt(row.shipping)
            row.markup = flt(row.markup)
            row.clearing = flt(row.clearing)
            let markup = row.markup / 100;
            let clearing = row.clearing / 100;
            let multiplier = (1 + markup) * row.fx;
            row.multiplier = multiplier;
            // Round all monetary results to currency precision to prevent float drift accumulation
            row.disti_quote_total = flt((row.disti_quote + row.shipping) * row.qty, curr_precision);
            row.rate = flt(
                row.disti_quote * multiplier * (1 + clearing)
                + row.shipping * multiplier * (1 + clearing),
                curr_precision
            );
            row.amount = flt(row.rate * row.qty, curr_precision);
            frm.add_child("items",{
                "item_code" : row.main_item_code,
                "item_name" : row.item_name,
                "custom_part_number" : row.part_number,
                "custom_serial_no" : row.custom_serial_no,
                "description" : row.description,
                "qty" : row.qty,
                "custom_disti_quote" : row.disti_quote,
                "custom_disti_quote_total" : row.disti_quote_total,
                "custom_multiplier" : row.multiplier,
                "custom_shipping" : row.shipping,
                "custom_markup" : row.markup,
                "custom_fx" : row.fx,
                "custom_clearing" : row.clearing,
                "rate" : row.rate,
                "amount" : row.amount,
                "uom" : row.uom || "Nos",
            })
        }
        frm.refresh_field(ch_tab_name);
        frm.refresh_field("items");
    }
    frm.trigger("calculate_taxes_and_totals")
    check_n_validate_child_tables(frm)
}

function check_n_validate_child_tables(frm) {
    let ch_tab_name = get_items_table_name(frm)
    for (let t of ["custom_standard_quotation_items", "custom_license_renewal_items"]){
        if (t != ch_tab_name){
            frm.set_value(t, [])
        }
    }
}

function get_items_table_name(frm) {
    let ch_tab_name = undefined;
    if (frm.doc.custom_quotation_type == "Standard Quotation"){ch_tab_name = "custom_standard_quotation_items"}
    if (frm.doc.custom_quotation_type == "License Renewal"){ch_tab_name = "custom_license_renewal_items"}
    return ch_tab_name
}
