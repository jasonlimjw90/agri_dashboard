AC = "#002D72"
UPC = "#1a9a55"
DNC = "#d1432f"
MU = "#6b7686"
OR = "#F58220"
W = "#FFFFFF"
BLACK = "#000000"

UP_RGB = "26,154,85"
DN_RGB = "209,67,47"

COMMODITIES = ["Corn", "Soybeans", "Wheat"]

PALETTE = [
    "#3F7D58",
    "#6B8EAD",
    "#D6A84F",
    "#C47A52",
    "#8A7D9E",
    "#7E9B91",
    "#A9A9A9",
]

CHART_HEIGHT = 250

CHART_MARGIN = dict(
    l=0,
    r=0,
    t=5,
    b=0,
)

HISTORICAL_RANGE_FILL = "rgba(31,111,235,.13)"

YEAR_TICK_FORMAT = "%Y"

MONTH_TICK_VALUES = list(range(1, 13))

CALENDAR_MONTH_TICK_TEXT = [
    "Jan", "Feb", "Mar", "Apr",
    "May", "Jun", "Jul", "Aug",
    "Sep", "Oct", "Nov", "Dec",
]

MONTH_TICK_TEXT = [
    "May", "Jun", "Jul", "Aug",
    "Sep", "Oct", "Nov", "Dec",
    "Jan", "Feb", "Mar", "Apr",
]

WEEK_TICK_VALUES = list(range(1, 54))
WEEK_TICK_TEXT = [
    str(week)
    for week in WEEK_TICK_VALUES
]