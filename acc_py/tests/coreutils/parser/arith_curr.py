from typing import Callable
from unittest import TestCase
from unittest.mock import call
from pkg.coreutils.parser.arith_curr import (parse_arithmetic_operation,
                                             parse_currency,
                                             parse_double_currency,)
from tests._shared import Patcher


TEST_MODULE = 'pkg.coreutils.parser.arith_curr'


def patchthis(f: Callable | str, **kwargs) -> Patcher:
    return Patcher(TEST_MODULE, f, **kwargs)


class TestArithmeticOperationParser(TestCase):

    def test_simple_operations(self):
        cases = [
            ('+65 - 66.99', -1.99),
            ('=9.9/88 + 5 * 65.1', 325.6125),
            ('+-5+9+1/6.5', 4.15385),
            ('-5-6', -11),
        ]
        for expr, expected in cases:
            with self.subTest(expr=expr):
                self.assertAlmostEqual(parse_arithmetic_operation(expr, -99999), 
                                       expected,
                                       places=4)

    def test_err_and_injections(self):
        malicious = [
            'malicious test',
            'import os; os.system("cls")',
            '+5+8;print("injected!")',
            '=98=5',
            '=x+y',
            ''
        ]
        for expr in malicious:
            with self.assertRaises(ValueError):
                parse_arithmetic_operation(expr)

    def test_lower_bound(self):
        with self.assertRaises(ValueError):
            parse_arithmetic_operation('+1+1', 3)


class TestCurrencyParser(TestCase):

    def test_currency(self):
        cases = [
            ('sdD', 'SDD'),
            ('USD', 'USD'),
            ('  pen   ', 'PEN'),
        ]
        for curr, expected_curr in cases:
            with self.subTest(currency=curr):
                self.assertEqual(
                    parse_currency(curr),
                    expected_curr
                )

    def test_currency_err(self):
        cases = [
            'not a valid one',
            '2+2',
            '   ',
            '',
        ]
        for currency_input in cases:
            with self.subTest(currency_input=currency_input):
                with self.assertRaises(ValueError):
                    parse_currency(currency_input)



class TestDoubleCurrencyPairParser(TestCase):
    
    def test_double_currency(self):
        lbound = -99999
        def_curr = 'DCU'
        places_ = 3
        cases = [
            ('=5+2 usd           ', ('=5+2', 'usd'), (7, 'USD'), False),
            ('+5.5 - 2.5/2.5 pen', ('+5.5 - 2.5/2.5', 'pen'), (6.5, 'PEN'), False),
            ('   -5+9.00     ', ('-5+9.00', '-5+9.00'), (4., 'DCU'), True),
            ('   2.2 eur     ', ('2.2', 'eur'), (2.2, 'EUR'), False),
            ('2.2', ('2.2', '2.2'), (2.2, 'DCU'), True),
        ]
        for raw_input, (arg_arith, arg_curr), (e_amount, e_currency), use_default in cases:
            with self.subTest(raw_input=raw_input):
                with (patchthis(parse_arithmetic_operation) as mock_arith,
                      patchthis(parse_currency) as mock_curr):
                    mock_arith.return_value = e_amount
                    if use_default:
                        mock_curr.side_effect = [ValueError, e_currency]
                    else:
                        mock_curr.return_value = e_currency
                    amount, currency = parse_double_currency(raw_input, def_curr, lbound)
                    mock_arith.assert_called_once_with(arg_arith, lbound)
                    if use_default:
                        self.assertEqual(mock_curr.call_args_list, [call(arg_curr), call(def_curr)])
                    else:
                        mock_curr.assert_called_once_with(arg_curr)
                    self.assertAlmostEqual(amount, e_amount, places=places_)
                    self.assertEqual(currency, e_currency)

    def test_double_currency_err(self):
        lbound = -9999
        def_curr = 'DEF'
        cases = [
            '=5+5 usd usd',
            '5.       5',
            '2.2 / foo',
            'pen',
            '',
            '               ',
        ]
        for raw_input, err in cases:
            with self.subTest(raw_input=raw_input):
                with self.assertRaises(ValueError):
                    parse_double_currency(def_curr, raw_input, lbound)