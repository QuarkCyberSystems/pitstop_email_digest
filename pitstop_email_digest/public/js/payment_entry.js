
frappe.ui.form.on('Payment Entry', {
	refresh: function(frm) {
        frm.trigger("check_reference_no_auotmation");
	},
    onload: function(frm) {
        frm.trigger("check_reference_no_auotmation");
    },
    setup: function(frm) {
        frm.trigger("check_reference_no_auotmation");
    },
    payment_type: function(frm) {
        frm.trigger("check_reference_no_auotmation");
    },
    mode_of_payment: function(frm) {
        frm.trigger("check_reference_no_auotmation");
    },
    check_reference_no_auotmation: function(frm) {
        if(frm.doc.payment_type && frm.doc.mode_of_payment) {
            frappe.call({
                method: "pitstop_email_digest.utils.payment_entry.check_payment_reference_no_automation",
                args: {
                    payment_type: frm.doc.payment_type,
                    mode_of_payment: frm.doc.mode_of_payment
                },
                freeze: 1,
                freeze_message: __("Fetching.."),
                callback: (r) => {
                    if(r && r.message && r.message.length>0) {
                        frm.toggle_reqd("reference_no", false);
                        frm.toggle_reqd("reference_date", false);
                    }
                    else {
                        if ((frm.doc.payment_type === "Receive") && (frm.doc.account_paid_to_type === "Bank")) {
                            frm.toggle_reqd("reference_no", true);
                            frm.toggle_reqd("reference_date", true);
                        } else if(((frm.doc.payment_type === "Pay") || (frm.doc.payment_type === "Internal Transfer")) && (frm.doc.account_paid_from_type === "Bank")) {   
                            frm.toggle_reqd("reference_no", true);
                            frm.toggle_reqd("reference_date", true);
                        }
                        else {
                            frm.toggle_reqd("reference_no", false);
                            frm.toggle_reqd("reference_date", false);
                        }
                    }
                }
            });
        }
    }
});