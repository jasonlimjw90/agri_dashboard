MONTH_ABBR = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)


def format_marketing_year(crop_year: int) -> str:
    """Format a crop year as 2025/26."""

    year = int(crop_year)
    next_year = (year + 1) % 100

    return f"{year}/{next_year:02d}"


def format_month_offset(offset: str, crop_year: int) -> str:
    """Format an offset as a month and calendar year."""

    year_off, month_num = parse_month_offset(offset)

    calendar_year = int(crop_year) + year_off
    month_name = MONTH_ABBR[month_num - 1]

    return f"{month_name} {calendar_year}"


def parse_month_offset(offset: str) -> tuple[int, int]:
    """Parse an offset such as '0_05' or '1_10'."""

    parts = str(offset).strip().split("_")

    if len(parts) != 2:
        raise ValueError(
            "month_offset must use 'year_month' format, "
            "e.g. '0_05'."
        )

    try:
        year_off = int(parts[0])
        month_num = int(parts[1])
    except ValueError as exc:
        raise ValueError(
            f"Invalid month_offset: {offset}"
        ) from exc

    if year_off < 0 or not 1 <= month_num <= 12:
        raise ValueError(f"Invalid month_offset: {offset}")

    return year_off, month_num