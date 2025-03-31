import requests
from functools import lru_cache
from datetime import datetime, timedelta

# Cache exchange rates for 1 hour to avoid excessive API calls
@lru_cache(maxsize=1)
def get_exchange_rates(base_currency='USD'):
    """Get current exchange rates from an API."""
    try:
        # Using ExchangeRate-API (you'll need to sign up for a free API key)
        api_key = 'YOUR_API_KEY'  # Replace with your API key
        url = f'https://v6.exchangerate-api.com/v6/{api_key}/latest/{base_currency}'
        response = requests.get(url)
        data = response.json()
        return data.get('conversion_rates', {})
    except Exception as e:
        print(f"Error fetching exchange rates: {e}")
        return {}

def convert_currency(amount, from_currency, to_currency):
    """Convert amount from one currency to another."""
    if from_currency == to_currency:
        return amount
    
    rates = get_exchange_rates(from_currency)
    if not rates or to_currency not in rates:
        return amount  # Return original amount if conversion fails
    
    return amount * rates[to_currency]

def format_currency(amount, currency):
    """Format amount with appropriate currency symbol and decimal places."""
    from .models import SUPPORTED_CURRENCIES
    
    symbol = SUPPORTED_CURRENCIES.get(currency, '$')
    
    # Handle different currency formatting conventions
    if currency == 'JPY':
        return f"{symbol}{int(amount):,}"  # No decimal places for JPY
    else:
        return f"{symbol}{amount:,.2f}"  # 2 decimal places for other currencies 