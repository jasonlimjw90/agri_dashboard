
WASDE_LABELS = {
    "Acreage": {
        "planted area": "Area Planted",
        "planted": "Planted",
        "harvested area": "Area Harvested",
        "harvested": "Harvested",
        "yield": "Yield",
    },
    "Supply": {
        "beginning stocks": "Beginning Stocks",
        "production": "Production",
        "imports": "Imports",
        "supply total": "Total Supply",
    },
    "Usage": {
        "domestic feed or crush": "Domestic Feed or Crush",
        "feed residual": "Feed & Residual",
        "food seed industrial": "Food, Seed & Industrial",
        "food feed industrial": "Food, Feed & Industrial",
        "food": "Food",
        "seed": "Seed",
        "industrial": "Industrial",
        "ethanol": "Ethanol",
        "crushing": "Crushing",
        "bio diesel": "Biodiesel",
        "residual": "Residual",
        "feed": "Feed",
        "domestic use": "Domestic Use",
        "domestic total": "Domestic Total",
        "total domestic": "Total Domestic",
        "exports": "Exports",
        "exports total": "Total Exports",
        "domestic disappearance": "Domestic Disappearance",
        "unaccounted": "Unaccounted",
        "loss": "Loss",
        "use total": "Total Use",
        
    },
    "Ending Stocks": {
            "ending stocks": "Ending Stocks",
            "stock to use": "Stocks-to-Use",
            "avg. farm price": "Avg. Farm Price",
            "avg. price": "Avg. Price",
    },

}

# Additional names that should resolve to an existing canonical key.
LABEL_ALIASES = {
    "total supply": "supply total",
    "total exports": "exports total",
    "total use": "use total",
    "average farm price": "avg. farm price",
    "stocks to use": "stock to use",
    "stocks-to-use": "stock to use",
    "stock to use ratio": "stock to use",
    "stocks to use ratio": "stock to use",
}

MONTHS = [
    "January", "February", "March", "April",
    "May", "June", "July", "August",
    "September", "October", "November", "December",
]

CROP_LABELS = {
    "nc": "New Crop",
    "oc": "Old Crop",
}


def _build_wasde_label_lookup():
    return {
        key: label
        for section in WASDE_LABELS.values()
        for key, label in section.items()
    }


DISPLAY_LABELS = _build_wasde_label_lookup()


def format_label(value: str) -> str:
    key = str(value).strip().casefold()

    # Accept already-formatted labels.
    reverse_lookup = {
        label.casefold(): raw_key
        for raw_key, label in DISPLAY_LABELS.items()
    }
    key = reverse_lookup.get(key, key)

    # Resolve source-name variations.
    key = LABEL_ALIASES.get(key, key)

    return DISPLAY_LABELS.get(
        key,
        key.replace("_", " ").title(),
    )


# Monthly
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

# Weekly
WEEK_TICK_VALUES = list(range(1, 54))
WEEK_TICK_TEXT = [str(week) for week in WEEK_TICK_VALUES]

