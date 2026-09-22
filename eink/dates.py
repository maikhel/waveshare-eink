"""Polish date formatting for the header and forecast strip."""

DAY_ABBR = {
    'Mon': 'Pon',
    'Tue': 'Wt',
    'Wed': 'Śr',
    'Thu': 'Czw',
    'Fri': 'Pt',
    'Sat': 'Sob',
    'Sun': 'Nie',
}


def day_abbr(dt):
    weekday = dt.strftime('%a')
    return DAY_ABBR.get(weekday, weekday)


def header_date(dt):
    """e.g. 'Pon 22.09'"""
    return f"{day_abbr(dt)} {dt.strftime('%d.%m')}"
