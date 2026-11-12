from typing import List
import urllib
import socket
import requests
import json
import re

from .paths import APPLICATION_CACHED_DIRECTORY
from .typing import ExchangeDictType
from .jops import jopen, jdump, jprint


# https://stackoverflow.com/a/33117579/29272030
def has_internet(
        host: str = "8.8.8.8", 
        port: int = 443, 
        timeout: int = 3
) -> bool:
    """Check if internet is available."""
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        print(ex)
        return False


def fetch_exchange(currency: str) -> dict[str, int | float]:
    """
    Fetch full list of currency exchanges associated to currency.
    """
    # https://github.com/fawazahmed0/exchange-api
    url_bases = [
        "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/",
        "https://latest.currency-api.pages.dev/v1/currencies/" 
    ]

    currency = currency.lower()
    endpoint = f"{currency}.json"
    for url in url_bases:
        url_request = urllib.parse.urljoin(url, endpoint)
        response = requests.get(url_request)
        if response.ok:
            # res example: 
            # https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/pen.json
            res = json.loads(response.content)
            res = res[currency]
            return res
            
    if response.status_code == 404:
        raise ValueError(
            f"Arguement '{currency}' is an invalid currency. "
            f"Full response: {response.text}."
        )
    else:
        raise RuntimeError(f"Unknown state. Full response: {response.text}.")


def to_currency(currency: str | list[str]) -> str:
    """
    Check that currency is a 3-word-length `str` and returns in lowercase.
    """
    if isinstance(currency, list):
        return list(map(to_currency, currency))

    if not isinstance(currency, str):
        raise TypeError(f"Argument {currency=!r} is not str.")

    currency = currency.strip().lower()
    if re.match(r'^[a-z]{3}$', currency):
        return currency
    raise ValueError(f"{currency=} is not a valid currency.")


exchange_memo = {}
def fetch_exchange_rates(
        currency: str
) -> dict:
    """
    Fetch exchange rate**S** from a given currency and update 
    `exchange_memo` if non-existent. 
    """
    currency = to_currency(currency)
    # if memoized, call it
    if currency in exchange_memo:
        return exchange_memo[currency]

    # if not, then update exchange_memo
    res = fetch_exchange(currency)
    exchange_memo.update({currency: res})
    return res


def get_exchange_rate(
        currency_1: str,
        currency_2: str
)-> float | int:
    """
    Gets exchange rate between `curr_1` and `curr_2`. Calls fetch_exchange_rate
    under the hood. Type checks are implemented.
    """    
    # type checking
    currency_1 = to_currency(currency_1)
    currency_2 = to_currency(currency_2)

    # unnecessary fetch is prevented
    if currency_1 == currency_2:
        return 1.0

    # fetch full exchange rates, if curr_2 does not exist, raise err
    res = fetch_exchange_rates(currency_1)
    if currency_2 in res:
        return res[currency_2]
    
    raise ValueError(f"{currency_2=} does not exist in exchange" 
                     f"dictionary for {currency_1=}.")
    


def build_exchange(curr_list: List[str]) -> ExchangeDictType:
    """
    Builds exchange dictionary from a list of currencies. 
    Check tests for a full check of coverage.
    """
    res = {curr1: {curr2: get_exchange_rate(curr1, curr2) 
                   for curr2 in curr_list}
           for curr1 in curr_list}
    return res


# NOTE: delete quiet? refactor tests.core.TestExchangeDictionaryGetter
def get_exchange_dict(
        curr_list: List[str],
        use_cache: bool = False,
        quiet: bool = False
) -> ExchangeDictType:
    """
    Builds exchange dictionary from curr_list. However, first tries to load 
    from cache. If failure, it type-checks curr_list and builds ex-dict from it.
    """
    
    # try to load from cache: whenever no internet is available or
    # explicitely passed as option
    name = "exchange.json"
    cached_path = APPLICATION_CACHED_DIRECTORY / name
    if (use_cache and cached_path.exists()) or (not has_internet()):
        res = jopen(cached_path)
        return res

    # ensure type check and build exchange dict
    curr_list = to_currency(curr_list)
    curr_exchange = build_exchange(curr_list)
    
    # load to cache and print if asked
    jdump(curr_exchange, cached_path)
    if not quiet:
        jprint(curr_exchange)
    exchange_memo.clear()
    return curr_exchange