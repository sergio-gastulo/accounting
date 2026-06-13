import unittest
from unittest import TestCase
from typing import Callable
from unittest.mock import (
    patch,
)

from tests._shared import (
    RUN_API_TEST,
    Patcher
)
from pkg.utilities.currency import (
    fetch_exchange_rates,
    get_exchange_rate,
    exchange_memo,
    get_exchange_dict,
    build_exchange,
    check_currency_list,
)


#region ============================ utils  ====================================

TEST_MODULE = 'pkg.utilities.currency'

def _patch_this(f: Callable | str, **kwargs) -> Patcher:
    return Patcher(TEST_MODULE, f, **kwargs)

#endregion =====================================================================




@unittest.skipUnless(RUN_API_TEST, "skipping API tests (set RUN_API_TESTS=1 to enable)")
class TestExchangeRateFetcher(TestCase):

    def test_fetch_exchange_rate(self):
        cases = [
            "pen",
            "eur"
        ]
        for currency in cases:
            with self.subTest(currency=currency):
                res = fetch_exchange_rates(currency)
                self.assertIsInstance(
                    res,
                    dict
                )
                for curr, exchange in res.items():
                    with self.subTest(curr=curr):
                        self.assertIsInstance(curr, str)
                        self.assertIsInstance(exchange, float | int)

    def test_fetch_from_bad_currency(self):
        bad_cases = [
            ("any-currency",    ValueError),
            (print,             TypeError),
            (None,              TypeError),
            ("asd",             ValueError)
        ]
        for bad_currency, err in bad_cases:
            with self.subTest(bad_currency=bad_currency):
                with self.assertRaises(err):
                    fetch_exchange_rates(bad_currency)

    def test_fetch_exchange_rate_memo(self):
        currency = "pen"
        expected = "foo"
        with patch(exchange_memo, {currency : expected}):
            with _patch_this('_fetch_exchange') as mock_fetch_exchange:
                res = fetch_exchange_rates(currency)
                mock_fetch_exchange.assert_not_called()
                self.assertEqual(res, expected)


@unittest.skipUnless(RUN_API_TEST, "skipping API tests (set RUN_API_TESTS=1 to enable)")
class TestExchangeRateGetter(TestCase):
    def test_get_exchange_rate(self):
        cases = [
            ("pen", "usd"),
            ("usd", "eur"),
        ]
        for curr1, curr2 in cases:
            with self.subTest(curr1=curr1, curr2=curr2):
                self.assertIsInstance(
                    get_exchange_rate(curr1, curr2),
                    float
                )


class TestExchangeBuilder(TestCase):
    def test_build_exchange(self):
        cases = [
            (
                ["foo", "bar", "baz"],
                {
                    "foo" : {
                        "foo" : 2.0,
                        "bar" : 2.0,
                        "baz" : 2.0
                    },
                    "bar" : {
                        "foo" : 2.0,
                        "bar" : 2.0,
                        "baz" : 2.0
                    },
                    "baz" : {
                        "foo" : 2.0,
                        "bar" : 2.0,
                        "baz" : 2.0
                    }
                }
            ),
        ]
        for curr_list, expected in cases:
            with self.subTest(curr_list=curr_list):
                with _patch_this('get_exchange_rate') as mock_get_exchange:
                    mock_get_exchange.return_value = 2.0
                    self.assertEqual(
                        build_exchange(curr_list),
                        expected
                    )
        

class TestExchangeDictionaryGetter(TestCase):

    def test_get_exchange_dict_flow(self):
        cache = False
        quiet = True
        curr_list = ['JPY', 'EUR']
        build_return = {
            "jpy" : {
                "jpy" : 1.0,
                "eur" : 2.0
            },
            "eur" : {
                "jpy" : 0.5,
                "eur" : 1.0
            }
        }
        
        with (
            # _patch_this(check_currency_list) as mock_curr_list,
            _patch_this('has_internet') as mock_internet,
            _patch_this(build_exchange) as mock_build,
            _patch_this('_jdump') as mock_jdump,
            _patch_this('_jprint') as mock_jprint,
        ):
            mock_build.return_value = build_return
            mock_internet.return_value = True
            res = get_exchange_dict(curr_list, cache, quiet)
        mock_jdump.assert_called_once()
        jdump_args, _cached_path = mock_jdump.call_args.args
        self.assertEqual(jdump_args, res)
        mock_jprint.assert_not_called()
        self.assertEqual(res, build_return)

    def test_cache_call(self):
        res = "any"
        with (
            _patch_this('_jopen') as mock_jopen,
            _patch_this(build_exchange) as mock_build_cache,
            _patch_this('build_exchange') as mock_build,
        ):
            mock_build_cache.return_value.exists.return_value = True
            get_exchange_dict(res, True)
            mock_jopen.assert_called_once()
            mock_build.assert_not_called()
    
    def test_not_quiet_prints(self):
        cache = False
        quiet = False
        curr_list = ['JPY', 'EUR']
        build_return = {
            "jpy" : {
                "jpy" : 1.0,
                "eur" : 2.0
            },
            "eur" : {
                "jpy" : 0.5,
                "eur" : 1.0
            }
        }
        
        with (
            _patch_this('has_internet') as mock_internet,
            _patch_this(build_exchange) as mock_build,
            _patch_this('_jdump') as mock_jdump,
            _patch_this('_jprint') as mock_jprint,
        ):
            mock_build.return_value = build_return
            mock_internet.return_value = True
            get_exchange_dict(curr_list, cache, quiet)
        mock_jprint.assert_called_once_with(build_return)


class TestCurrencyListChecker(TestCase):
    def test_check_currency_list(self):
        arg = ["FOO", "BAR", "BAZ"]
        self.assertEqual(
            check_currency_list(arg),
            ["foo", "bar", "baz"]
        )

    def test_check_currency_list_err(self):
        bad = ["foo", "bar4"]
        with self.assertRaises(ValueError):
            check_currency_list(bad)