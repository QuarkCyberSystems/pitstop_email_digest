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
