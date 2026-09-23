"""Date formatting for the header and forecast strip."""


def day_abbr(dt):
    """Short weekday name, e.g. 'Tue'."""
    return dt.strftime('%a')


def header_date(dt):
    """e.g. 'Tue 22.09.2026'"""
    return f"{day_abbr(dt)} {dt.strftime('%d.%m.%Y')}"
