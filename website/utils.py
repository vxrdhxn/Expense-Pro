import os
import requests
import json
from datetime import datetime, timedelta
from functools import lru_cache
import sys

# Cache for exchange rates
_exchange_rates_cache = {}
_last_update = None

def _get_api_key():
    """Get the ExchangeRate-API key from environment variables."""
    api_key = os.getenv('EXCHANGERATE_API_KEY')
    if not api_key:
        raise ValueError("ExchangeRate API key not found in environment variables")
    return api_key

def _get_cache_duration():
    """Get the cache duration from environment variables or use default (1 hour)."""
    try:
        return int(os.getenv('CURRENCY_REFRESH_INTERVAL', 3600))
    except ValueError:
        return 3600

@lru_cache(maxsize=1)
def _get_api_base_url():
    """Get the API base URL from environment variables or use default."""
    return os.getenv('EXCHANGERATE_API_BASE_URL', 'https://v6.exchangerate-api.com/v6/')

def _should_update_cache():
    """Check if the cache needs to be updated."""
    if not _last_update:
        return True
    cache_duration = _get_cache_duration()
    return datetime.now() - _last_update > timedelta(seconds=cache_duration)

def update_exchange_rates():
    """Update the exchange rates cache."""
    global _exchange_rates_cache, _last_update
    
    try:
        api_key = _get_api_key()
        base_url = _get_api_base_url()
        
        # Make API request
        response = requests.get(f"{base_url}{api_key}/latest/USD")
        response.raise_for_status()
        
        # Update cache
        data = response.json()
        if 'conversion_rates' in data:
            _exchange_rates_cache = data['conversion_rates']
            _last_update = datetime.now()
            print("Exchange rates updated successfully", file=sys.stderr)
        else:
            raise ValueError("Invalid response format from API")
            
    except requests.RequestException as e:
        print(f"Error fetching exchange rates: {str(e)}", file=sys.stderr)
        if not _exchange_rates_cache:
            raise
    except Exception as e:
        print(f"Unexpected error updating exchange rates: {str(e)}", file=sys.stderr)
        if not _exchange_rates_cache:
            raise

def get_exchange_rate(from_currency, to_currency):
    """Get the exchange rate between two currencies."""
    if _should_update_cache():
        update_exchange_rates()
    
    if not _exchange_rates_cache:
        raise ValueError("Exchange rates not available")
    
    # Normalize currency codes
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()
    
    # Get rates (using USD as base)
    if from_currency not in _exchange_rates_cache or to_currency not in _exchange_rates_cache:
        raise ValueError(f"Exchange rate not found for {from_currency} to {to_currency}")
    
    # Calculate cross-rate through USD
    usd_to_from = _exchange_rates_cache[from_currency]
    usd_to_to = _exchange_rates_cache[to_currency]
    
    return usd_to_to / usd_to_from

def convert_currency(amount, from_currency, to_currency):
    """Convert an amount from one currency to another."""
    try:
        rate = get_exchange_rate(from_currency, to_currency)
        return round(amount * rate, 2)
    except Exception as e:
        print(f"Error converting currency: {str(e)}", file=sys.stderr)
        return amount  # Return original amount if conversion fails

def format_currency(amount, currency='USD'):
    """Format a currency amount with the appropriate symbol."""
    currency = currency.upper()
    symbols = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'JPY': '¥',
        'INR': '₹',
        'AUD': 'A$',
        'CAD': 'C$',
        'CHF': 'Fr',
        'CNY': '¥',
        'NZD': 'NZ$'
    }
    
    symbol = symbols.get(currency, currency + ' ')
    
    if currency in ['JPY', 'KRW']:  # Currencies typically shown without decimal places
        return f"{symbol}{int(amount):,}"
    else:
        return f"{symbol}{amount:,.2f}" 