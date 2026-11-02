"""MDM Customer Journey API (see "Pitstop MDM API RSD").

GET /api/mdm/v1/customer-journeys          (customer_journeys)
GET /api/mdm/v1/customer-journeys/count    (customer_journeys_count)
GET /api/mdm/v1/deleted                    (deleted)

Each is also callable as /api/method/pitstop_email_digest.pitstop_email_digest.api.mdm.<function>

Query params:
    modifiedSince  datetime, optional. Journeys: only those where the customer or any
                   of its opportunities / quotations / sales orders / sales
                   invoices / repair orders / service contracts changed since.
                   Deleted: only records deleted since.
    pageSize       default 100, max 500 (/count: only with groupBy)
    cursor         nextCursor from the previous page (/count: only with groupBy)
    groupBy        /count only, optional. "customer" returns, per journey, how many
                   records each array holds instead of the total.
"""

from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import cint, get_datetime
from werkzeug.routing import Rule
from werkzeug.wrappers import Response

from pitstop_email_digest.pitstop_email_digest.api.mdm_schema import (
    CUSTOMER,
    CUSTOMER_CHILDREN,
    DELETED_DOCTYPES,
    OPPORTUNITY,
    OPPORTUNITY_LINK,
)

DEFAULT_PAGE_SIZE = 100
MAX_PAGE_SIZE = 500


@frappe.whitelist(methods=["GET"])
def customer_journeys(modifiedSince=None, pageSize=None, cursor=None):
    check_permissions()

    page_size = get_page_size(pageSize)
    modified_since = get_datetime(modifiedSince) if modifiedSince else None

    names = get_customer_page(modified_since, cursor, page_size + 1)
    has_more = len(names) > page_size
    names = names[:page_size]

    return {
        "data": build_journeys(names),
        "paging": {
            "pageSize": page_size,
            "returned": len(names),
            "hasMore": has_more,
            "nextCursor": names[-1] if has_more else None,
        },
    }


@frappe.whitelist(methods=["GET"])
def customer_journeys_count(
    modifiedSince=None, groupBy=None, pageSize=None, cursor=None
):
    """Total journeys, or with groupBy=customer the record count of each array per journey (paged)."""
    check_permissions()

    modified_since = get_datetime(modifiedSince) if modifiedSince else None

    if groupBy:
        if groupBy != "customer":
            frappe.throw(_("groupBy only supports 'customer'"))
        return count_by_customer(modified_since, get_page_size(pageSize), cursor)

    # Interpolated text is the hardcoded journey query; modifiedSince is bound as %(since)s
    count = frappe.db.sql(  # nosemgrep: frappe-db-sql-injection
        f"select count(*) from ({get_journey_query(modified_since)}) journey",
        {"since": modified_since},
    )[0][0]

    return {"count": count}


def count_by_customer(modified_since, page_size, cursor):
    names = get_customer_page(modified_since, cursor, page_size + 1)
    has_more = len(names) > page_size
    names = names[:page_size]

    counts = {
        "Opportunities": count_per_customer(OPPORTUNITY, *OPPORTUNITY_LINK, names)
    }
    for key, (spec, link, cond) in CUSTOMER_CHILDREN.items():
        counts[key] = count_per_customer(spec, link, cond, names)

    return {
        "data": [
            {"customer": name, **{key: counts[key].get(name, 0) for key in counts}}
            for name in names
        ],
        "paging": {
            "pageSize": page_size,
            "returned": len(names),
            "hasMore": has_more,
            "nextCursor": names[-1] if has_more else None,
        },
    }


def count_per_customer(spec, link_field, condition, customers):
    """{customer: number of records} using the same filters as the journey arrays."""
    if not customers:
        return {}

    # Doctype, link field and conditions come from the module's specs; customers are bound
    return dict(
        frappe.db.sql(  # nosemgrep: frappe-db-sql-injection
            f"""
            select `{link_field}`, count(*) from `tab{spec['doctype']}`
            where `{link_field}` in %(customers)s{get_conditions(spec, condition)}
            group by `{link_field}`
            """,
            {"customers": tuple(customers)},
        )
    )


@frappe.whitelist(methods=["GET"])
def deleted(modifiedSince=None, pageSize=None, cursor=None):
    check_permissions()

    page_size = get_page_size(pageSize)
    modified_since = get_datetime(modifiedSince) if modifiedSince else None

    rows = get_deleted_page(modified_since, cursor, page_size + 1)
    has_more = len(rows) > page_size
    rows = rows[:page_size]

    return {
        "data": [
            {
                "doctype": row.deleted_doctype,
                "name": row.deleted_name,
                "customer": get_deleted_customer(row),
                "parent": row.parent,
                "deletedAt": row.creation,
            }
            for row in rows
        ],
        "paging": {
            "pageSize": page_size,
            "returned": len(rows),
            "hasMore": has_more,
            "nextCursor": f"{rows[-1].creation}|{rows[-1].name}" if has_more else None,
        },
    }


def get_page_size(page_size):
    page_size = cint(page_size) or DEFAULT_PAGE_SIZE
    if page_size < 1 or page_size > MAX_PAGE_SIZE:
        frappe.throw(_("pageSize must be between 1 and {0}").format(MAX_PAGE_SIZE))
    return page_size


# RSD URL -> whitelisted method. Same payload, without Frappe's `message` wrapper.
ROUTES = {
    "/api/mdm/v1/customer-journeys": customer_journeys,
    "/api/mdm/v1/customer-journeys/count": customer_journeys_count,
    "/api/mdm/v1/deleted": deleted,
}


def register_routes():
    """before_request hook: add the RSD URLs to Frappe's /api url map (once per worker)."""
    import frappe.api

    if getattr(frappe.api, "_mdm_routes_registered", False):
        return

    for path, method in ROUTES.items():
        frappe.api.API_URL_MAP.add(
            Rule(path, methods=["GET"], endpoint=make_route(method))
        )
    frappe.api._mdm_routes_registered = True


def make_route(method):
    def route():
        frappe.form_dict.pop("cmd", None)
        data = method(**frappe.form_dict)
        return Response(frappe.as_json(data, indent=None), mimetype="application/json")

    return route


def check_permissions():
    doctypes = [CUSTOMER["doctype"], OPPORTUNITY["doctype"]]
    doctypes += [spec["doctype"] for spec, _link, _cond in CUSTOMER_CHILDREN.values()]
    for doctype in doctypes:
        if not frappe.has_permission(doctype, "read"):
            frappe.throw(
                _("Not permitted to read {0}").format(doctype), frappe.PermissionError
            )


def get_customer_page(modified_since, cursor, limit):
    """Customer names for one page, ordered by name (keyset pagination on `cursor`)."""
    return frappe.db.sql_list(
        f"""
        select journey.customer from ({get_journey_query(modified_since)}) journey
        {"where journey.customer > %(cursor)s" if cursor else ""}
        order by journey.customer limit %(limit)s
        """,
        {"since": modified_since, "cursor": cursor, "limit": limit},
    )


def get_journey_query(modified_since):
    """SQL returning one `customer` row per journey (changed since `modified_since`, if given)."""
    if not modified_since:
        return "select name as customer from `tabCustomer`"

    # A journey has changed when the customer or any record in it changed
    sources = ["select name as customer from `tabCustomer` where modified >= %(since)s"]
    link, cond = OPPORTUNITY_LINK
    sources.append(
        f"select {link} from `tabOpportunity` where modified >= %(since)s and {cond}"
    )
    for spec, link, cond in CUSTOMER_CHILDREN.values():
        sources.append(
            f"select `{link}` from `tab{spec['doctype']}`"
            f" where modified >= %(since)s{get_conditions(spec, cond)}"
        )

    # `union` removes duplicates; the join drops links to customers that no longer exist
    return f"""
        select changed.customer from ({" union ".join(sources)}) changed
        inner join `tabCustomer` on `tabCustomer`.name = changed.customer
    """


def get_deleted_page(modified_since, cursor, limit):
    conditions = ["deleted_doctype in %(doctypes)s", "restored = 0"]
    values = {
        "doctypes": tuple(DELETED_DOCTYPES),
        "since": modified_since,
        "limit": limit,
    }

    if modified_since:
        conditions.append("creation >= %(since)s")
    if cursor:
        try:
            values["cursor_creation"], values["cursor_name"] = cursor.split("|", 1)
        except ValueError:
            frappe.throw(_("Invalid cursor"))
        conditions.append(
            "(creation > %(cursor_creation)s"
            " or (creation = %(cursor_creation)s and name > %(cursor_name)s))"
        )

    # `conditions` are hardcoded fragments; modifiedSince and cursor parts are bound values
    return frappe.db.sql(  # nosemgrep: frappe-db-sql-injection
        f"""
        select
            name, creation, deleted_doctype, deleted_name,
            json_value(data, '$.customer') as customer,
            json_value(data, '$.party_name') as party_name,
            json_value(data, '$.opportunity_from') as opportunity_from,
            json_value(data, '$.quotation_to') as quotation_to,
            json_value(data, '$.parent') as parent
        from `tabDeleted Document`
        where {" and ".join(conditions)}
        order by creation, name
        limit %(limit)s
        """,
        values,
        as_dict=True,
    )


def get_deleted_customer(row):
    """Customer whose journey the deleted record belonged to (None for item rows / non-customers)."""
    if row.deleted_doctype == "Customer":
        return row.deleted_name
    if row.deleted_doctype == "Opportunity":
        return row.party_name if row.opportunity_from == "Customer" else None
    if row.deleted_doctype == "Quotation":
        return row.party_name if row.quotation_to == "Customer" else None
    return row.customer


def build_journeys(names):
    if not names:
        return []

    customers = fetch(CUSTOMER, "name", names)
    link, cond = OPPORTUNITY_LINK
    opportunities = group_by(fetch(OPPORTUNITY, link, names, cond), link)
    children = {
        key: group_by(fetch(spec, link, names, cond), link)
        for key, (spec, link, cond) in CUSTOMER_CHILDREN.items()
    }

    journeys = []
    for customer in customers:
        for key in CUSTOMER_CHILDREN:
            customer[key] = children[key].get(customer["name"], [])
        journeys.append(
            {
                "Opportunities": opportunities.get(customer["name"], []),
                "Customer": customer,
            }
        )

    return journeys


def fetch(spec, link_field, link_values, condition=None):
    """Rows of spec's doctype where link_field in link_values, shaped as the RSD response."""
    doctype = spec["doctype"]
    aliases = spec.get("aliases", {})
    lookups = spec.get("lookups", {})
    columns = set(frappe.db.get_table_columns(doctype))

    select = {}
    for key in spec["keys"]:
        column = aliases.get(key, key)
        if key not in lookups and column in columns:
            select[key] = column
    for link_key, _target, _field in lookups.values():
        if link_key in columns:
            select.setdefault(link_key, link_key)

    # Columns are spec keys that exist on the table; doctype, link field and conditions come
    # from the module's specs; link values are bound
    rows = frappe.db.sql(  # nosemgrep: frappe-db-sql-injection
        f"""
        select {", ".join(f"`{column}` as `{key}`" for key, column in select.items())}
        from `tab{doctype}`
        where `{link_field}` in %(values)s{get_conditions(spec, condition)}
        order by `{link_field}`, creation
        """,
        {"values": tuple(link_values)},
        as_dict=True,
    )

    resolve_lookups(rows, lookups)

    bool_keys = get_bool_keys(
        doctype, {k: c for k, c in select.items() if k in spec["keys"]}
    )
    records = [{key: row.get(key) for key in spec["keys"]} for row in rows]
    for record in records:
        for key in bool_keys:
            record[key] = bool(record[key])

    if items := spec.get("items"):
        names = [record["name"] for record in records]
        items_by_parent = (
            group_by(fetch(items, "parent", names), "parent") if names else {}
        )
        for record in records:
            record["Items"] = items_by_parent.get(record["name"], [])

    return records


def get_conditions(spec, condition=None):
    conditions = ""
    if condition:
        conditions += f" and {condition}"
    if spec.get("submitted_only"):
        conditions += " and docstatus in (1, 2)"
    return conditions


def resolve_lookups(rows, lookups):
    """Fill the readable name for each link, with one query per target doctype + field."""
    targets = defaultdict(set)
    for link_key, doctype, field in lookups.values():
        targets[(doctype, field)].update(
            row.get(link_key) for row in rows if row.get(link_key)
        )

    values = {
        (doctype, field): dict(
            frappe.get_all(
                doctype,
                filters={"name": ("in", list(names))},
                fields=["name", field],
                as_list=True,
            )
        )
        if names
        else {}
        for (doctype, field), names in targets.items()
    }

    for row in rows:
        for key, (link_key, doctype, field) in lookups.items():
            row[key] = values[(doctype, field)].get(row.get(link_key))


def get_bool_keys(doctype, select):
    meta = frappe.get_meta(doctype)
    return [
        key
        for key, column in select.items()
        if (df := meta.get_field(column)) and df.fieldtype == "Check"
    ]


def group_by(records, key):
    grouped = defaultdict(list)
    for record in records:
        grouped[record[key]].append(record)
    return grouped
