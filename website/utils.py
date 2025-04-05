from datetime import datetime, timedelta
import calendar
import json

def get_date_range(period='month', date=None):
    """Get start and end dates for a given period."""
    if date is None:
        date = datetime.now()
    
    if period == 'day':
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
    elif period == 'week':
        start_date = date - timedelta(days=date.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=7)
    elif period == 'month':
        start_date = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_day = calendar.monthrange(date.year, date.month)[1]
        end_date = date.replace(day=last_day, hour=23, minute=59, second=59)
    elif period == 'year':
        start_date = date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = date.replace(month=12, day=31, hour=23, minute=59, second=59)
    else:
        raise ValueError(f"Invalid period: {period}")
    
    return start_date, end_date

def format_currency(amount, currency_symbol='$', decimals=2):
    """Format a number as currency."""
    try:
        return f"{currency_symbol}{amount:,.{decimals}f}"
    except (TypeError, ValueError):
        return f"{currency_symbol}0.00"

def parse_tags(tags_string):
    """Parse a comma-separated string of tags into a list."""
    if not tags_string:
        return []
    return [tag.strip() for tag in tags_string.split(',') if tag.strip()]

def format_tags(tags):
    """Format a list of tags into a comma-separated string."""
    return ', '.join(tags) if tags else ''

def calculate_percentage(value, total):
    """Calculate percentage safely."""
    try:
        return (value / total * 100) if total > 0 else 0
    except (TypeError, ZeroDivisionError):
        return 0

def format_date(date, format='%Y-%m-%d'):
    """Format a date object as string."""
    try:
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d')
        return date.strftime(format)
    except (ValueError, AttributeError):
        return ''

def safe_json_loads(json_string, default=None):
    """Safely load JSON string."""
    try:
        return json.loads(json_string) if json_string else default
    except json.JSONDecodeError:
        return default

def get_month_name(month_number):
    """Get month name from month number."""
    try:
        return calendar.month_name[int(month_number)]
    except (ValueError, IndexError):
        return ''

def calculate_trend(current, previous):
    """Calculate trend percentage between two values."""
    try:
        if previous == 0:
            return 100 if current > 0 else 0
        return ((current - previous) / abs(previous)) * 100
    except (TypeError, ZeroDivisionError):
        return 0

def format_large_number(number):
    """Format large numbers with K, M, B suffixes."""
    try:
        number = float(number)
        if number < 1000:
            return str(int(number))
        elif number < 1000000:
            return f"{number/1000:.1f}K"
        elif number < 1000000000:
            return f"{number/1000000:.1f}M"
        else:
            return f"{number/1000000000:.1f}B"
    except (TypeError, ValueError):
        return "0" 