MONTH_CODES = "FGHJKMNQUVXZ"
STANDARD_TIMEZONE = "UTC"


def month_of_year(month_code: str) -> int:
    """Given a futures month code, returns an int between 1 and 12
    representing the month of the year."""
    code_to_month = dict(zip(MONTH_CODES, range(1, 13)))

    try:
        return code_to_month[month_code.upper()]
    except KeyError:
        raise ValueError(
            f"Invalid month code: {month_code!r}. Must be one of {list(code_to_month.keys())}"
        )
