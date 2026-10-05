def generate_weightage_table(based_on, base_incentive):
    from .employee_incentive_calculation import BASED_ON_TEMPLATE_DATA

    if BASED_ON_TEMPLATE_DATA.get(based_on):
        weightages = BASED_ON_TEMPLATE_DATA.get(based_on).get("weightages", {})

        labels = {
            "sold_hrs": "Sold Hrs",
            "efficiency": "Efficiency",
            "productivity": "Productivity",
        }

        rows = ""

        for key, percentage in weightages.items():
            amount = base_incentive * percentage / 100
            label = labels.get(key, key.replace("_", " ").title())

            rows += f"""
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;">
                        {label}
                    </td>
                    <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">
                        <strong>{percentage}%</strong>
                    </td>
                    <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">
                        <strong>{amount:.2f}</strong>
                    </td>
                </tr>
            """

        return f"""
            <table style="border-collapse: collapse; width: 400px; font-family: Arial, sans-serif; font-size: 14px;">
                <thead>
                    <tr>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">
                            Weightages
                        </th>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: center;">
                            %
                        </th>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: center;">
                            Amount
                        </th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        """


def generate_employee_weightage_table(template_data, base_incentive=0.0):
    employee_weightages = (template_data or {}).get("employee_weightages", [])

    if not employee_weightages:
        return None

    acronyms = {"tat", "gp", "cs", "qc"}

    # Fields and their labels, in order of first appearance in the data
    labels = {}

    for employee in employee_weightages:
        for field in employee.get("weightage", {}):
            if field not in labels:
                labels[field] = " ".join(
                    word.upper() if word.lower() in acronyms else word.title()
                    for word in field.split("_")
                )

    fields = list(labels)

    header_cells = ""

    for field in fields:
        label = labels[field]

        header_cells += f"""
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: center;">
                            {label}
                        </th>
        """

    rows = ""

    for employee in employee_weightages:
        weightages = employee.get("weightage", {})
        cells = ""

        for field in fields:
            percentage = weightages.get(field)

            if percentage is None:
                cells += """
                        <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">
                            -
                        </td>
                """
                continue

            amount = base_incentive * percentage / 100

            cells += f"""
                        <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">
                            <strong>{percentage}%</strong><br>
                            {amount:.2f}
                        </td>
            """

        total_percentage = sum(weightages.values())
        total_amount = base_incentive * total_percentage / 100

        rows += f"""
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;">
                            {employee.get("employee_id", "")}
                        </td>
                        <td style="border: 1px solid #ddd; padding: 8px;">
                            {employee.get("employee_name", "")}
                        </td>
                        {cells}
                        <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">
                            <strong>{total_percentage}%</strong><br>
                            {total_amount:.2f}
                        </td>
                    </tr>
        """

    return f"""
            <table style="border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; font-size: 14px;">
                <thead>
                    <tr>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">
                            Employee ID
                        </th>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">
                            Employee Name
                        </th>
                        {header_cells}
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: center;">
                            Total
                        </th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        """


def generate_ladder_html(based_on, ladder_field, header):
    from .employee_incentive_calculation import BASED_ON_TEMPLATE_DATA

    if not BASED_ON_TEMPLATE_DATA.get(based_on):
        return None

    ladder = BASED_ON_TEMPLATE_DATA[based_on].get(ladder_field, {})

    if not ladder:
        return None

    thresholds = sorted(ladder.keys())

    range_labels = []

    # First range
    range_labels.append(f"&lt; {thresholds[0]}%")

    # Middle ranges
    for i in range(1, len(thresholds)):
        previous = thresholds[i - 1]
        current = thresholds[i]

        range_labels.append(f"{previous}% - {current - 1}%")

    # Final range
    range_labels.append(f"&ge; {thresholds[-1]}%")

    # Results
    results = [ladder[threshold] for threshold in thresholds]

    # Final range result
    results.append(thresholds[-1])

    html = f"""
    <table style="
        border-collapse: collapse;
        width: 100%;
        font-family: Arial, sans-serif;
        font-size: 14px;
        text-align: center;
    ">
        <tbody>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px;">
                    <strong>{header}</strong>
                </td>
    """

    for label in range_labels:
        html += f"""
                <td style="border: 1px solid #ddd; padding: 8px;">
                    {label}
                </td>
        """

    html += """
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px;">
                    <strong>Multiplier</strong>
                </td>
    """

    for result in results:
        html += f"""
                <td style="border: 1px solid #ddd; padding: 8px;">
                    {result}%
                </td>
        """

    html += """
            </tr>
        </tbody>
    </table>
    """

    return html


def rate_based_generate_ladder_html(based_on, ladder_field, header, symbol=""):
    from .employee_incentive_calculation import BASED_ON_TEMPLATE_DATA

    if not BASED_ON_TEMPLATE_DATA.get(based_on):
        return None

    ladder = BASED_ON_TEMPLATE_DATA[based_on].get(ladder_field, {})

    if not ladder:
        return None

    thresholds = sorted(ladder.keys())

    range_labels = []
    results = []

    # First threshold represents everything below the next threshold
    if len(thresholds) == 1:
        range_labels.append(f"&ge; {thresholds[0]}")
        results.append(ladder[thresholds[0]])
    else:
        for i in range(len(thresholds) - 1):
            range_labels.append(f"&lt; {thresholds[i + 1]}")
            results.append(ladder[thresholds[i]])

        # Final threshold
        range_labels.append(f"&ge; {thresholds[-1]}")
        results.append(ladder[thresholds[-1]])

    html = f"""
    <table style="
        border-collapse: collapse;
        width: 100%;
        font-family: Arial, sans-serif;
        font-size: 14px;
        text-align: center;
    ">
        <tbody>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px;">
                    <strong>{header}{symbol}</strong>
                </td>
    """

    for label in range_labels:
        html += f"""
                <td style="border: 1px solid #ddd; padding: 8px;">
                    {label}{symbol}
                </td>
        """

    html += """
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px;">
                    <strong>Multiplier</strong>
                </td>
    """

    for result in results:
        html += f"""
                <td style="border: 1px solid #ddd; padding: 8px;">
                    {result}%
                </td>
        """

    html += """
            </tr>
        </tbody>
    </table>
    """

    return html


def generate_employee_ladder_html(based_on, ladder_field, header):
    """Like `generate_ladder_html`, for ladders kept per employee: a list of
    `{"employee_id", "employee_name", "criteria": {threshold: result}}`."""
    from .employee_incentive_calculation import BASED_ON_TEMPLATE_DATA

    if not BASED_ON_TEMPLATE_DATA.get(based_on):
        return None

    employee_ladders = BASED_ON_TEMPLATE_DATA[based_on].get(ladder_field, [])

    if not employee_ladders:
        return None

    rows = []

    for employee in employee_ladders:
        ladder = employee.get("criteria") or {}

        if not ladder:
            continue

        thresholds = sorted(ladder.keys())

        range_labels = [f"&lt; {thresholds[0]}%"]

        for i in range(1, len(thresholds)):
            range_labels.append(f"{thresholds[i - 1]}% - {thresholds[i] - 1}%")

        range_labels.append(f"&ge; {thresholds[-1]}%")

        results = [ladder[threshold] for threshold in thresholds]
        results.append(thresholds[-1])

        rows.append((employee, list(zip(range_labels, results))))

    return employee_ladder_table_html(header, rows)


def employee_rate_based_generate_ladder_html(based_on, ladder_field, header, symbol=""):
    """Like `rate_based_generate_ladder_html`, for ladders kept per employee: a
    list of `{"employee_id", "employee_name", "criteria": {threshold: result}}`."""
    from .employee_incentive_calculation import BASED_ON_TEMPLATE_DATA

    if not BASED_ON_TEMPLATE_DATA.get(based_on):
        return None

    employee_ladders = BASED_ON_TEMPLATE_DATA[based_on].get(ladder_field, [])

    if not employee_ladders:
        return None

    rows = []

    for employee in employee_ladders:
        ladder = employee.get("criteria") or {}

        if not ladder:
            continue

        thresholds = sorted(ladder.keys())

        range_labels = []
        results = []

        if len(thresholds) == 1:
            range_labels.append(f"&ge; {thresholds[0]}{symbol}")
            results.append(ladder[thresholds[0]])
        else:
            for i in range(len(thresholds) - 1):
                range_labels.append(f"&lt; {thresholds[i + 1]}{symbol}")
                results.append(ladder[thresholds[i]])

            range_labels.append(f"&ge; {thresholds[-1]}{symbol}")
            results.append(ladder[thresholds[-1]])

        rows.append((employee, list(zip(range_labels, results))))

    return employee_ladder_table_html(f"{header}{symbol}", rows)


def employee_ladder_table_html(header, rows):
    """One row per employee: ID, name, then a `range / multiplier` cell per
    step of that employee's ladder. `rows` is a list of
    `(employee, [(range_label, result), ...])`."""
    if not rows:
        return None

    max_steps = max(len(steps) for _employee, steps in rows)

    body = ""

    for employee, steps in rows:
        cells = ""

        for label, result in steps:
            cells += f"""
                        <td style="border: 1px solid #ddd; padding: 8px;">
                            {label}<br>
                            <strong>{result}%</strong>
                        </td>
            """

        for _ in range(max_steps - len(steps)):
            cells += """
                        <td style="border: 1px solid #ddd; padding: 8px;">
                            -
                        </td>
            """

        body += f"""
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px; text-align: left;">
                            {employee.get("employee_id", "")}
                        </td>
                        <td style="border: 1px solid #ddd; padding: 8px; text-align: left;">
                            {employee.get("employee_name", "")}
                        </td>
                        {cells}
                    </tr>
        """

    return f"""
    <table style="
        border-collapse: collapse;
        width: 100%;
        font-family: Arial, sans-serif;
        font-size: 14px;
        text-align: center;
    ">
        <thead>
            <tr>
                <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">
                    Employee ID
                </th>
                <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">
                    Employee Name
                </th>
                <th colspan="{max_steps}" style="border: 1px solid #ddd; padding: 8px;">
                    {header} / Multiplier
                </th>
            </tr>
        </thead>
        <tbody>
            {body}
        </tbody>
    </table>
    """
