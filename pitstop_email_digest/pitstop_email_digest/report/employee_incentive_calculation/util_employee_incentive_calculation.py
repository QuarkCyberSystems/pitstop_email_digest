def get_ladder_result(based_on, sold_hrs_percentage, ladder_field, top_cap):
    from .employee_incentive_calculation import BASED_ON_TEMPLATE_DATA

    if BASED_ON_TEMPLATE_DATA.get(based_on):
        ladder = BASED_ON_TEMPLATE_DATA.get(based_on).get(ladder_field)

        if ladder:
            for threshold, result in ladder.items():
                if sold_hrs_percentage < threshold:
                    return result
            return top_cap


def get_weightage_amount(based_on, base_incentive, field_name):
    from .employee_incentive_calculation import BASED_ON_TEMPLATE_DATA

    if BASED_ON_TEMPLATE_DATA.get(based_on):
        weightages = BASED_ON_TEMPLATE_DATA.get(based_on).get("weightages", {})

        for key, percentage in weightages.items():
            amount = base_incentive * percentage / 100
            if field_name == key:
                return amount


def get_rate_ladder_result(based_on, percentage, ladder_field, top_cap):
    from .employee_incentive_calculation import BASED_ON_TEMPLATE_DATA

    ladder = BASED_ON_TEMPLATE_DATA.get(based_on, {}).get(ladder_field, {})

    if not ladder:
        return None

    thresholds = sorted(ladder.keys())

    for threshold in reversed(thresholds):
        if percentage >= threshold:
            return ladder[threshold]

    # Less than the lowest threshold
    return ladder[thresholds[0]]
