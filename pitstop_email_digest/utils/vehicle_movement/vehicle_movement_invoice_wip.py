
import frappe
from frappe.utils import getdate

def fetch_revenue_others_group_based_on_ro_wip(from_date, to_date, cost_center, customer_group_list, vehicle_group_list):
    if customer_group_list:
        customer_group_condition = " AND IFNULL(tp.bill_to_customer_group, tp.customer_group) NOT IN ({})".format(
            ", ".join("'{}'".format(cg) for cg in customer_group_list)
        )
    else:
        customer_group_condition = ""

    if vehicle_group_list:
        vehicle_group_condition = " AND ti.brand NOT IN ({})".format(
            ", ".join("'{}'".format(vg) for vg in vehicle_group_list)
        )
    else:
        vehicle_group_condition = ""

    others_details = frappe.db.sql("""
        SELECT 
            "Others" AS customer_group,
            COUNT(DISTINCT tp.name) AS ro_count,
            SUM(tp.total_sales_amount) AS revenue,
            tp.branch as branch
        FROM 
            `tabProject` tp
        JOIN 
            `tabVehicle` tv
        ON 
            tv.name = tp.applies_to_vehicle
        JOIN 
            `tabItem` ti
        ON
            ti.name = tv.variant_of
        WHERE (
                tp.project_status in ('Awaiting LPO', 'Not Invoiced', 'Ready for Collection', 'Tasks Completed') AND
                tp.project_date >= '{from_date}' AND 
                tp.project_date <= '{to_date}'  AND 
                tp.cost_center = '{cost_center}'
                {vehicle_group_condition} {customer_group_condition}
            )
        GROUP BY 
            tp.branch
    """.format(
        from_date=from_date, to_date=to_date, 
        cost_center=cost_center, vehicle_group_condition=vehicle_group_condition,
        customer_group_condition=customer_group_condition), as_dict=True)
 
    return others_details


def fetch_revenue_vehicle_group_based_on_ro_wip(from_date, to_date, cost_center, vehicle_variant, customer_group_list=None):
    
    if customer_group_list:
        customer_group_condition = " AND IFNULL(tp.bill_to_customer_group, tp.customer_group) NOT IN ({})".format(
            ", ".join("'{}'".format(cg) for cg in customer_group_list)
        )
    else:
        customer_group_condition = ""
    vehicle_group_condition = ""
    vehicle_group_condition += " and ti.brand = '{vehicle_variant}'".format(vehicle_variant=vehicle_variant)
    
    vehicle_group_details = frappe.db.sql("""
        SELECT 
            ti.brand AS vehicle_group,
            COUNT(DISTINCT tp.name) AS ro_count,
            SUM(tp.total_sales_amount) AS revenue,
            tp.branch as branch
        FROM 
            `tabProject` tp
        JOIN 
            `tabVehicle` tv
        ON 
            tv.name = tp.applies_to_vehicle
        JOIN 
            `tabItem` ti
        ON
            ti.name = tv.variant_of
        WHERE (
                tp.project_status in ('Awaiting LPO', 'Not Invoiced', 'Ready for Collection', 'Tasks Completed') AND
                tp.project_date >= '{from_date}' AND 
                tp.project_date <= '{to_date}'  AND 
                tp.cost_center = '{cost_center}'
                {vehicle_group_condition} {customer_group_condition}
            )
        GROUP BY 
            vehicle_group, tp.branch
    """.format(
        from_date=from_date, to_date=to_date, 
        cost_center=cost_center, vehicle_group_condition=vehicle_group_condition,
        customer_group_condition=customer_group_condition), as_dict=True)
    
    return vehicle_group_details

def fetch_revenue_customer_group_based_on_ro_wip(from_date, to_date, cost_center, customer_group, customer_group_list=None):
    customer_group_condition = ""
    customer_group_condition += " and gp.name = '{customer_group}'".format(customer_group=customer_group)
    customer_group_details = frappe.db.sql("""
        SELECT 
            gp.name AS customer_group,
            COUNT(DISTINCT tp.name) AS ro_count,
            SUM(tp.total_sales_amount) AS revenue,
            tp.branch as branch
        FROM 
            `tabProject` tp
        JOIN 
            `tabCustomer Group` cg
        ON 
            cg.name = IFNULL(tp.bill_to_customer_group, tp.customer_group)
        JOIN 
            `tabCustomer Group` gp
        ON 
            gp.lft <= cg.lft
        AND 
            gp.rgt >= cg.rgt
        WHERE (
                tp.project_status in ('Awaiting LPO', 'Not Invoiced', 'Ready for Collection', 'Tasks Completed') AND
                tp.project_date >= '{from_date}' AND 
                tp.project_date <= '{to_date}'  AND 
                tp.cost_center = '{cost_center}' {customer_group_condition}
            )
        GROUP BY 
            customer_group, tp.branch
    """.format(from_date=from_date, to_date=to_date, cost_center=cost_center, customer_group_condition=customer_group_condition), as_dict=True)
    return customer_group_details

def fetch_revenue_customer_group_based_on_costcenter(from_date, to_date, cost_center, customer_group, customer_group_list=None):
    customer_group_condition = ""
    customer_group_condition += " and gp.name = '{customer_group}'".format(customer_group=customer_group)
    customer_group_details = frappe.db.sql("""
        SELECT 
            gp.name AS customer_group,
            COUNT(DISTINCT sii.project) AS ro_count,
            SUM(sii.net_amount) AS revenue
        FROM 
            `tabSales Invoice Item` sii
        JOIN 
            `tabSales Invoice` si
        ON 
            sii.parent = si.name
        JOIN 
            `tabProject` tp
        ON 
            tp.name = sii.project
        JOIN 
            `tabCustomer Group` cg
        ON 
            cg.name = IFNULL(tp.bill_to_customer_group, tp.customer_group)
        JOIN 
            `tabCustomer Group` gp
        ON 
            gp.lft <= cg.lft
        AND 
            gp.rgt >= cg.rgt
        LEFT JOIN 
            `tabItem Group` ig
        ON 
            sii.item_group = ig.name
        WHERE (
                si.docstatus = 1 AND 
                si.posting_date >= '{from_date}' AND 
                si.posting_date <= '{to_date}'  AND 
                sii.project IS NOT NULL AND
                tp.cost_center = '{cost_center}' {customer_group_condition}
            )
        GROUP BY 
            customer_group
    """.format(from_date=from_date, to_date=to_date, cost_center=cost_center, customer_group_condition=customer_group_condition), as_dict=True)
    return customer_group_details

@frappe.whitelist()
def fetch_revenue_branchwise(from_date, to_date, cost_center):
    return frappe.db.sql("""
        SELECT tp.branch AS 'Branch',
            SUM(sii.net_amount) AS Revenue
        FROM `tabSales Invoice Item` sii
        JOIN `tabSales Invoice` si
            ON sii.parent = si.name
        JOIN `tabProject` tp
            ON tp.name = sii.project
        WHERE (
                si.docstatus = 1 AND 
                si.posting_date >= '{from_date}' AND 
                si.posting_date <= '{to_date}'  AND 
                sii.project IS NOT NULL AND
                tp.cost_center = '{cost_center}'
            )
        GROUP BY 
            tp.branch
        ORDER BY 
            tp.branch
    """.format(from_date=from_date, to_date=to_date, cost_center=cost_center), as_dict=True)


@frappe.whitelist()
def fetch_revenue_branchwise_based_on_costcenter(from_date, to_date):
    autoworks_customer_group_list = ["Budget Mobility"]
    autocare_customer_group_list = []
    autoworks_vehicle_group_list = ["TESLA"]
    autocare_vehicle_group_list = ["BMW", "GEELY"]
    whole_vehicle_group_list = ["TESLA", "BMW", "GEELY"]

    customer_group_cost_center_revenue_list = []
    cost_center_list = frappe.db.get_list("Cost Center", filters={"disabled":0, "is_group":0}, pluck="name")
    cost_center_branch_list = []
    for each_cost_center in cost_center_list:
        branch_revenue_details_list = []
        if fetch_revenue_branchwise(from_date, to_date, each_cost_center):
            for each_result_row in fetch_revenue_branchwise(from_date, to_date, each_cost_center):
                print(each_result_row)
                each_result_row["Target"] = get_target_revenue_branchwise(
                    getdate(from_date),getdate(to_date),each_result_row.get('Branch'), each_cost_center)
                branch_revenue_details_list.append(each_result_row)
            cost_center_branch_list.append({
                "cost_center":each_cost_center, 
                "branch_revenue_details":branch_revenue_details_list
            })
        customer_group_cost_center_revenue_list.append(
            {
                "cost_center":each_cost_center, 
                "customer_group_cost_center_details":[]
            }
        )

        if each_cost_center == "AutoWorks - PASLLC":
            for each_customer_group in autoworks_customer_group_list:
                customer_group_details = fetch_revenue_customer_group_based_on_ro_wip(from_date, to_date, each_cost_center, each_customer_group)
                for each_customer_group_cost_center_revenue_list in customer_group_cost_center_revenue_list:
                    if each_customer_group_cost_center_revenue_list.get("cost_center") == each_cost_center:
                        each_customer_group_cost_center_revenue_list.get("customer_group_cost_center_details").extend(customer_group_details)

            for each_vehicle_group in autoworks_vehicle_group_list:
                vehicle_group_details = fetch_revenue_vehicle_group_based_on_ro_wip(from_date, to_date, each_cost_center, each_vehicle_group, autoworks_customer_group_list)
                for each_vehicle_group_cost_center_revenue_list in customer_group_cost_center_revenue_list:
                    if each_vehicle_group_cost_center_revenue_list.get("cost_center") == each_cost_center:
                        each_vehicle_group_cost_center_revenue_list.get("customer_group_cost_center_details").extend(vehicle_group_details)
        
        if each_cost_center == "AutoCare - PASLLC":
            for each_customer_group in autocare_customer_group_list:
                customer_group_details = fetch_revenue_customer_group_based_on_ro_wip(from_date, to_date, each_cost_center, each_customer_group)
                for each_customer_group_cost_center_revenue_list in customer_group_cost_center_revenue_list:
                    if each_customer_group_cost_center_revenue_list.get("cost_center") == each_cost_center:
                        each_customer_group_cost_center_revenue_list.get("customer_group_cost_center_details").extend(customer_group_details)

            for each_vehicle_group in autocare_vehicle_group_list:
                vehicle_group_details = fetch_revenue_vehicle_group_based_on_ro_wip(from_date, to_date, each_cost_center, each_vehicle_group, autocare_customer_group_list)
                for each_vehicle_group_cost_center_revenue_list in customer_group_cost_center_revenue_list:
                    if each_vehicle_group_cost_center_revenue_list.get("cost_center") == each_cost_center:
                        each_vehicle_group_cost_center_revenue_list.get("customer_group_cost_center_details").extend(vehicle_group_details)
        
        if each_cost_center == "AutoWorks - PASLLC":
            other_group_details = fetch_revenue_others_group_based_on_ro_wip(from_date, to_date, each_cost_center, autoworks_customer_group_list, autoworks_vehicle_group_list)
        elif each_cost_center == "AutoCare - PASLLC":
            other_group_details = fetch_revenue_others_group_based_on_ro_wip(from_date, to_date, each_cost_center, autocare_customer_group_list, autocare_vehicle_group_list)
        else:
            other_group_details = fetch_revenue_others_group_based_on_ro_wip(from_date, to_date, each_cost_center, autocare_customer_group_list, whole_vehicle_group_list)

        for each_vehicle_group_cost_center_revenue_list in customer_group_cost_center_revenue_list:
            if each_vehicle_group_cost_center_revenue_list.get("cost_center") == each_cost_center:
                each_vehicle_group_cost_center_revenue_list.get("customer_group_cost_center_details").extend(other_group_details)

    return {
        "cost_center_branch_list":cost_center_branch_list, 
        "customer_group_cost_center_revenue_list":customer_group_cost_center_revenue_list
    }

def get_target_revenue_branchwise(from_date, to_date, branch, cost_center):
    month_list = months_between(from_date, to_date)
    target_revenue = 0.0
    branch_revenue_row = frappe.db.get_all(
        "Branch Monthly Revenue Target", 
        filters= {
            "parenttype":"Company",
            "branch":branch,
            "cost_center":cost_center,
            "fiscal_year":from_date.year
        },
        fields = ["*"]
    )
    if branch_revenue_row:
        for each_month in month_list:
            target_revenue += branch_revenue_row[0].get(each_month)
    return target_revenue

def months_between(d1, d2):
    months = []
    for m in range(d1.month, d2.month + 1):
        if m < 10:
            months.append(f"0{m}")
        else:
            months.append(str(m))
    return months
