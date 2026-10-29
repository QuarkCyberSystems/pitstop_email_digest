# Copyright (c) 2026, QCS and contributors
# For license information, please see license.txt
"""Export all fields of "GL Entry" to a CSV file, meant to run as a background job.

Run from console (bench --site site_polaris console):

	job = frappe.enqueue(
		"pitstop_email_digest.utils.export_gl_entry.export_gl_entry",
		queue="long",
		timeout=5 * 60 * 60,  # 5 hours
		job_name="Export GL Entry 2026-01-01 to 2026-10-30",
		from_date="2026-01-01",
		to_date="2026-10-30",
	)
	frappe.db.commit()

Output: sites/<site>/private/files/gl_entry_<from>_<to>.csv (also listed in File List)
"""
import csv
import os

import frappe
from frappe.utils import get_files_path


def export_gl_entry(from_date="2026-01-01", to_date="2026-10-30"):
    columns = frappe.db.get_table_columns("GL Entry")
    file_name = "gl_entry_{0}_{1}.csv".format(from_date, to_date)
    path = os.path.join(get_files_path(is_private=1), file_name)
    query = "select {0} from `tabGL Entry` where posting_date between %s and %s order by posting_date, creation".format(
        ", ".join("`{0}`".format(c) for c in columns)
    )

    # unbuffered cursor streams rows from the database, so memory stays flat on large result sets
    count = 0
    with open(
        path, "w", newline="", encoding="utf-8-sig"
    ) as f, frappe.db.unbuffered_cursor():
        writer = csv.writer(f)
        writer.writerow(columns)
        for row in frappe.db.sql(
            query, (from_date, to_date), as_list=True, as_iterator=True
        ):
            writer.writerow(row)
            count += 1
            if count % 100000 == 0:
                print("GL Entry export: {0} rows written".format(count), flush=True)

    # File record so the CSV can be downloaded from File List
    if not frappe.db.exists("File", {"file_url": "/private/files/" + file_name}):
        frappe.get_doc(
            {
                "doctype": "File",
                "file_name": file_name,
                "file_url": "/private/files/" + file_name,
                "is_private": 1,
            }
        ).insert(ignore_permissions=True)

    frappe.db.commit()
    print("GL Entry export done: {0} rows -> {1}".format(count, path))
    return path
