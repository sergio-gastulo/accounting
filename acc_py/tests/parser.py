# unittest tooling
import unittest
from unittest.mock import call, MagicMock
from unittest import TestCase

# generics
import datetime
from db.model import Record
from sqlalchemy.dialects import sqlite
from sqlalchemy import text, true, select, create_engine
import pandas as pd
from datetime import date, timedelta
from typing import Callable

from db.model import Record, Base, Session, Engine

from tests._shared import (
    Patcher, 
    patch_builtin, 
    TEST_FILE_DIRECTORY
)

from utilities.parser import (
    parse_period,
    parse_arithmetic_operation,
    parse_currency,
    parse_date,
    parse_double_currency,
    core_semantic_filter_parse,
    parse_semantic_filter,
    parse_valid_element_list,
    cast_csv_types,
    sanitize_df,
    parse_record_from_id
)

#region ============================ utils =====================================

TEST_MODULE = 'utilities.parser'
def _patch_this(f: Callable | str, **kwargs) -> Patcher:
    return Patcher(TEST_MODULE, f, **kwargs)


def compile_sql(sql_expr):
    """Compiles sqlachemy stmt to vanilla sqlite3."""
    dialect = sqlite.dialect()
    kwargs = {"literal_binds" : True}
    return str(sql_expr.compile(dialect=dialect, compile_kwargs=kwargs))


#endregion =====================================================================



class TestArithmeticOperationParser(TestCase):

    def test_simple_operations(self):
        cases = [
            ('+65 - 66.99',                 -1.99),
            ('=9.9/88 + 5 * 65.1',          325.6125),
            ('+-5+9+1/6.5',                 4.15385),
            ('-5-6',                        -11),
        ]
        for expr, expected in cases:
            with self.subTest(expr=expr):
                self.assertAlmostEqual(
                    parse_arithmetic_operation(expr, -99999),
                    expected,
                    places=4
                )

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
            ('sdD',         'SDD'),
            ('USD',         'USD'),
            ('  pen   ',    'PEN'),
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


class TestDateParser(TestCase):

    today = datetime.date.today()

    def test_date(self):
        cases = [
            (10,                self.today.replace(day=10)),
            (0,                 self.today),
            ('-5',              self.today + timedelta(days=-5)),
            (-5,                self.today + timedelta(days=-5)),
            ('10',              self.today.replace(day=10)),
            ('10 08',           self.today.replace(month=10, day=8)),
            ('  2025-12 31 ',   datetime.date(year=2025, month=12, day=31)), 
            ('2025 12 31',      datetime.date(year=2025, month=12, day=31)), 
            ('25 12 31',        datetime.date(year=2025, month=12, day=31)), 
            ('today',           self.today),
            ('0',               self.today),
            ('',                self.today),
            ('10-08',           self.today.replace(month=10, day=8)),
            ('\'10-08\'',       self.today.replace(month=10, day=8))
        ]
        for date, expected in cases:
            with self.subTest(date_input=date):
                self.assertEqual(
                    parse_date(date),
                    expected
                )

    def test_date_err(self):
        cases = [
            99,
            'foo',
            'foo bar baz',
            '99',
            'dasads ads -asd asd asd das'
        ]
        for date_input in cases:
            with self.subTest(date_input=date_input):
                with self.assertRaises(ValueError):
                    parse_date(date_input)


class TestDoubleCurrencyPairParser(TestCase):
    
    def test_double_currency(self):
        lbound = -99999
        def_curr = 'DCU'
        places_ = 3
        cases = [
            ('=5+2 usd           ',     ('=5+2', 'usd'),                (7, 'USD'),         False),
            ('+5.5 - 2.5/2.5 pen',      ('+5.5 - 2.5/2.5', 'pen'),      (6.5, 'PEN'),       False),
            ('   -5+9.00     ',         ('-5+9.00', '-5+9.00'),         (4., 'DCU'),        True),
            ('   2.2 eur     ',         ('2.2', 'eur'),                 (2.2, 'EUR'),       False),
            ('2.2',                     ('2.2', '2.2'),                 (2.2, 'DCU'),       True),
        ]
        for raw_input, (arg_arith, arg_curr), (e_amount, e_currency), use_default in cases:
            with self.subTest(raw_input=raw_input):
                with (
                    _patch_this(parse_arithmetic_operation) as mock_arith,
                    _patch_this(parse_currency) as mock_curr
                ):
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
            ('=5+5 usd usd',        ValueError),
            ('5.       5',          ValueError),
            ('2.2 / foo',           ValueError),
            ('pen',                 ValueError),
            ('',                    ValueError),
            ('               ',     ValueError),
        ]
        for raw_input, err in cases:
            with self.subTest(raw_input=raw_input):
                with self.assertRaises(err):
                    parse_double_currency(def_curr, raw_input, lbound)


class TestPeriodParser(TestCase):

    test_default = pd.Period(year=2000, month=7, freq='M')

    def test_period(self):
        cases = [
            (5,                         self.test_default + 5),
            (-6,                        self.test_default - 6),
            (None,                      self.test_default),
            ('2024-12',                 pd.Period(year=2024, month=12, freq='M')),
            ('2024 12',                 pd.Period(year=2024, month=12, freq='M')),
            ('       24 12',            pd.Period(year=2024, month=12, freq='M')),
            ('24 / 12',                 pd.Period(year=2024, month=12, freq='M')),
            ('24 - 12',                 pd.Period(year=2024, month=12, freq='M')),
            (self.test_default,         self.test_default),
            ('       ',                 self.test_default),
            (' 5   ',                   self.test_default + 5),
        ]
        for period, expected_period in cases:
            with self.subTest(period=period):
                self.assertEqual(
                    parse_period(period, self.test_default), 
                    expected_period
                )
    
    def test_period_err(self):
        cases = [
            ('   2022-332   ',  ValueError),
            (print,             TypeError),
            (2.0,               TypeError),
        ]
        for raw_input, err in cases:
            with self.subTest(raw_input=raw_input):
                with self.assertRaises(err):
                    parse_period(raw_input, self.test_default)

    def test_wrong_default_period(self):
        cases = [
            print,
            None,
            'foo',
            9
        ]
        for bad_input in cases:
            with self.subTest(bad_input=bad_input):
                with self.assertRaises(TypeError):
                    parse_period(period='', default_period=bad_input)


class TestCoreSemanticFilterParser(TestCase):

    @staticmethod
    def wrap(filter):
        """Replaces x -> compile(core_semantic_filter_parser(x))""" 
        return compile_sql(core_semantic_filter_parse(filter))

    today = datetime.date.today()

    def test_id(self):
        cases = [
            ('id range 9 2',            (9-2, 9+2)),
            ('id between 3 and 9',      (3, 9)),
            ('id between -3 and 6',     (-3, 6))
        ]
        for id_filter, (lower, upper) in cases:
            with self.subTest(id_filter=id_filter):
                self.assertEqual(
                    compile_sql(Record.id.between(lower, upper)),
                    self.wrap(id_filter)
                )    

    def test_id_err(self):
        cases = [
            'id range foo bar',
            'id between value and value2', 
            'id between foo bar baz'
        ]
        for filter in cases:
            with self.subTest(filter=filter):
                with self.assertRaises(ValueError):
                    self.wrap(filter)


    def test_amount(self):
        cases = (
            ('amount between 10.11 and 23.66',  (10.11, 23.66)),
            ('amount b 10.11 and -6.99',        (10.11, -6.99)),
            ('am b 9.45 and 100.99',            (9.45, 100.99)),
            ('am between 10.11 and 23.66',      (10.11, 23.66)),
            ('10.66 < amount < 10.97',          (10.66, 10.97)),
            ('100.95 > amount > 65.32',         (65.32, 100.95)),
            ('100.95 >= amount >= 65.32',       (65.32, 100.95)),
            ('10.66 <= amount <= 10.97',        (10.66, 10.97))
        )
        for filter, (lower, upper) in cases:
            with self.subTest(filter=filter):
                self.assertEqual(
                    compile_sql(Record.amount.between(lower, upper)),
                    self.wrap(filter)
                )

    def test_amount_gt(self):
        cases = [
            '3.0 < amount',
            '3.0 <= a',
            'amount >= 3.0',
            'a > 3.0',
        ]
        for filter in cases:
            with self.subTest(filter=filter):
                self.assertEqual(
                    compile_sql(Record.amount >= 3.0),
                    self.wrap(filter)
                )

    def test_amount_lt(self):
        cases = [
            '3.0 > amount',
            '3.0 >= a',
            'amount <= 3.0',
            'a < 3.0',
        ]
        for filter in cases:
            with self.subTest(filter=filter):
                self.assertEqual(
                    compile_sql(Record.amount <= 3.0),
                    self.wrap(filter)
                )

    def test_amount_err(self):
        cases = [
            ('amount << value',     ValueError), 
            ('amount <= value',     ValueError),
            ('1 < amount < 2.0foo', ValueError)
        ]
        for filter, err in cases:
            with self.subTest(filter=filter):
                with self.assertRaises(err):
                    self.wrap(filter)

    def test_date_like(self):
        cases = [
            ('date like 2025-12%', '2025-12%'),
            ('date like \'2025-12%\'', '2025-12%')
        ]
        for date_like, expected in cases:
            with self.subTest(date_like=date_like):
                self.assertEqual(
                    compile_sql(Record.date.like(expected)),
                    self.wrap(date_like)
                )

    def test_date_parse(self):
        cases = [
            ('date = 2025 10 31',           '2025 10 31',       datetime.date(year=2025, month=10, day=31)),
            ('date equal \'2025 10 31\'',   '\'2025 10 31\'',   datetime.date(year=2025, month=10, day=31)),
            ('date = -12',                  '-12',              self.today + datetime.timedelta(days=-12)),
            ('date = 0',                    '0',                self.today)
        ]
        for semantic_filter, date_call, expected in cases:
            with self.subTest(semantic_filter=semantic_filter):
                with _patch_this(parse_date) as mock_dateparser:
                    mock_dateparser.return_value = expected
                    result = self.wrap(semantic_filter)
                    mock_dateparser.assert_called_once_with(date_call)
                    self.assertEqual(
                        compile_sql(Record.date == expected),
                        result
                    )

    def test_date_regex(self):
        cases = [
            'date r 2025-01',
            'date regex 2025-01',
            'date regexp 2025-01',
        ]
        for date_regex_filter in cases:
            with self.subTest(date_regex_filter=date_regex_filter):
                self.assertEqual(
                    compile_sql(Record.date.regexp_match('2025-01')),
                    self.wrap(date_regex_filter)
                )

    def test_date_err(self):
        cases = [
            'date = 99',
            'date = \'18 - 2015 - 65\'',
            'date equal 2025-31-12',
            'dte = 2025-13-12',
            'date regex 2025 08'
        ]
        for date_filter in cases:
            with self.subTest(date_filter=date_filter):
                with self.assertRaises(ValueError):
                    self.wrap(date_filter)

    def test_category_like(self):
        cases = [
            ('category like foobarbaz%',            'FOOBARBAZ%'),
            ('cat like \'food%\'',                  'FOOD%'),
            ('cat like \"food%\"',                  'FOOD%')
        ]
        for filter, like in cases:
            with self.subTest(filter=filter):
                self.assertEqual(
                    compile_sql(Record.category.like(like)),
                    self.wrap(filter)
                )

    def test_category_regex(self):
        cases = [
            ('category r expr',         'expr'),
            ('cat regexp expr',         'expr'),
            ('category regex expr_',    'expr_')
        ]
        for filter, regexp in cases:
            with self.subTest(filter=filter):
                self.assertEqual(
                    compile_sql(Record.category.regexp_match(regexp)),
                    self.wrap(filter)
                )

    def test_category_eq(self):
        cases = [
            ('category foo',        'FOO'),
            ('category \'bar\'',    'BAR'),
            ('category "baz"',      'BAZ')
        ]
        for filter, category_ in cases:
            with self.subTest(filter=filter):
                self.assertEqual(
                    compile_sql(Record.category == category_),
                    self.wrap(filter)
                )

    def test_category_err(self):
        cases = [
            'category like foo bar baz%',
            'cat reg foo',
            'cat regexp invalid regex',
            'cat INvalid caTEGory',        
        ]
        for filter in cases:
            with self.subTest(filter=filter):
                with self.assertRaises(ValueError):
                    self.wrap(filter)

    def test_currency(self):
        cases = [
            ('currency USD',            'USD'),
            ('curr \'EUR\'',            'EUR'),
            ('curr = \'euR\'',          'EUR'),
            ('cur = "lowcase"',         'LOWCASE')
        ]
        for filter, currency_ in cases:
            with self.subTest(filter=filter):
                self.assertEqual(
                    compile_sql(Record.currency == currency_),
                    self.wrap(filter)
                )

    def test_currency_err(self):
        with self.assertRaises(ValueError):
            self.wrap('currency invalid currency')

    def test_description_like(self):
        cases = [
            ('description like valid desc%',    'valid desc%'),
            ('desc like "valid desc%"',         '"valid desc%"'),
            ('desc like %',                     '%'),
        ] 
        for filter, description in cases:
            with self.subTest(filter=filter):
                self.assertEqual(
                    compile_sql(Record.description.like(description)),
                    self.wrap(filter)
                )

    def test_description_eq(self):
        cases = [
            ('description = test case',     'test case'),
            ('desc equal "quotes"',         '"quotes"'),
            ('desc = \'more quotes\'',      "'more quotes'"),
        ]
        for filter, description_ in cases:
            with self.subTest(filter=filter):
                self.assertEqual(
                    compile_sql(Record.description == description_),
                    self.wrap(filter)
                )

    def test_description_regex(self):
        cases = [
            ('description  regexp valid regex',     'valid regex'),
            ('   description r ^"',                 '^\"'),
            ('  desc regex  ^beg\\.end$',           r'^beg\.end$')
        ]
        for filter, regexp in cases:
            with self.subTest(filter=filter):
                self.assertEqual(
                    compile_sql(Record.description.regexp_match(regexp)),
                    self.wrap(filter)
                )        

    def test_description_err(self):
        cases = [
            'description like ',
            'description regexp',
            'desc = '
        ]
        for filter in cases:
            with self.subTest(filter=filter):
                with self.assertRaises(ValueError):
                    self.wrap(filter)

    def test_true(self):
        valid_true = [
            '',
            "true",
            "True"
        ]
        true_stmt = compile_sql(true())
        for true_ in valid_true:
            with self.subTest(filter=true_):
                self.assertEqual(
                    true_stmt,
                    self.wrap(true_)
                )

    def test_generic_err(self):
        cases = [
            "false",
            "update cuentas set currency=BROKEN",
            "SELECT sql FROM sqlite_master",
            "not a valid query",
            "foo"
        ]
        for invalid in cases:
            with self.assertRaises(ValueError):
                self.wrap(invalid)


class TestSemanticFilterParser(TestCase):
    
    @staticmethod
    def wrap(sql_expr) : 
        return compile_sql(parse_semantic_filter(sql_expr))
    
    today = date.today()

    def test_semantic_filter(self):
        cases = [
            (
                "      sql: SELECT * FROM cuentas WHERE description like 'test%'",
                text("SELECT * FROM cuentas WHERE description like 'test%'")
            ),
            (
                'description like test% && date = 2',
                select(Record).where(
                    Record.description.like('test%'),
                    Record.date == self.today.replace(day=2)
                )
            ),
            (
                '      currency  =     EUR &&         amount < 2.3',
                select(Record).where(
                    Record.currency == 'EUR',
                    Record.amount <= 2.3
                )
            ),
            (
                'category TEST && amount   > 1200 && currency USD &&     date like "2024-10%"',
                select(Record).where(
                    Record.category == 'TEST',
                    Record.amount >= 1200.0,
                    Record.currency == 'USD',
                    Record.date.like('2024-10%')
                )
            ),
            (
                '              ',
                select(Record).where(true())
            ),
            (
                '   && &&                    && &&           ',
                select(Record).where(true())
            ),
        ]
        for raw_query, expected_query in cases:
            with self.subTest(raw_query=raw_query):
                self.assertEqual(
                    compile_sql(expected_query),
                    self.wrap(raw_query)
                )

    def test_semantic_filter_err(self):
        cases = [
            ('sql: UPDATE * FROM cuentas SET currency=\'CORRUPTED\'',       ValueError),
            ('sql: DROP cuentas',                                           ValueError),
            ('sql: INSERT INTO cuentas VALUES (1,1,1,1,1,1)',               ValueError),
        ]
        for query, err in cases:
            with self.subTest(query=query):
                with self.assertRaises(err):
                    self.wrap(query)


class TestValidElementFromListParser(TestCase):
    def test_parse_valid_element_list(self):
        keybinds = {
            "key" : "value",
            "key2" : "value2",
            "weird" : "weird value"
        }
        for key, value in keybinds.items():
            with self.subTest(key=key, value=value):
                self.assertEqual(
                    value,
                    parse_valid_element_list(
                        user_input=key,
                        keybinds=keybinds
                    )
                )
                self.assertEqual(
                    value, 
                    parse_valid_element_list(
                        user_input=value,
                        keybinds=keybinds
                    )
                )

    def test_parse_valid_element_list_err(self):
        cases = [
            ( { "key":  "value" },  "invalid",      ValueError),
            ( { },                  "any",          ValueError),
            ( { "key":  "value" },  2,              TypeError),
        ]
        for keybind, uinput, err in cases:
            with self.subTest(uinput=uinput, keybind=keybind):
                with self.assertRaises(err):
                    parse_valid_element_list(
                        user_input=uinput,
                        keybinds=keybind
                    )


@unittest.skip("TODO: not implemented yet -- a simple open call")
class TestCSVRecordParser(TestCase):
    pass


class TestCastCSVTypes(TestCase):

    def test_cast_csv_types(self):
        cases = [
            (
                "amount, description\n"
                "9.65, testing description\n"
                "0.65, testing unícode",
                pd.DataFrame({
                    "amount" : [9.65, 0.65],
                    "description" : [
                        "testing description",
                        "testing unícode"
                    ]
                }),
                "amount and description"
            ),
            (
                " date         , amount\n        "
                "2024-10-12, 9.11\n"
                "2025-03-31, 9.10\n",
                pd.DataFrame({
                    "date" : pd.array([
                        pd.Timestamp("2024-10-12"),
                        pd.Timestamp("2025-03-31")
                    ], dtype="datetime64[ns]"),
                    "amount" : [9.11, 9.10]
                }),
                "date and amount"
            ),
            (
                "category,      description\n"
                "category1, desc1\n"
                "category2, desc2",
                pd.DataFrame({
                    "category" : ["category1", "category2"],
                    "description" : ["desc1", "desc2"]
                }),
                "category and description"
            ),
            (
                "        category,      description\n",
                pd.DataFrame({
                    "category" : pd.array([], dtype='str'),
                    "description" : pd.array([], dtype='str')
                }),
                "empty df"
            ),
        ]
        for csv_str, expected_df, label in cases:
            with self.subTest(label=label):
                self.assertEqual(
                    True,
                    expected_df.equals(
                        cast_csv_types(csv_str)
                    )
                )

    def test_cast_csv_types_err(self):
        cases = [
            (
                " corrupted,    column\n"
                "9.65, desc corrupted\n"
                ".665, desc corrp",
                "corrupted cols"
            ),
            (
                "date, amount, currency, description, category, another_col\n"
                "2024-10-12, .3, EUR, foobarbaz, category1, another col",
                "more cols than specified"
            ),
            (
                "amount, description\n"
                "6.565, foobarbaz, another_col",
                "additional unexpected field"
            ),
            (
                "amount, description\n"
                "6.56, hi, my name is sergio\n"
                "6.67, and my last name is gustavo",
                "unexpected comma"
            )
        ]
        for bad_str, label in cases:
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    cast_csv_types(bad_str)


class TestDataFrameSanitizer(TestCase):

    category_list = ["category" + str(i) for i in range(10)]

    def test_sanitize_df(self):
        cases = [
            (
                pd.DataFrame([{
                    "date": pd.Timestamp("2024-12-31"),
                    "amount" : 65,
                    "currency" : "eur",
                    "description": "desc",
                    "category": "category2"
                }]),
                pd.DataFrame([{
                    "date": "2024-12-31",
                    "amount" : 65,
                    "currency" : "EUR",
                    "description": "desc",
                    "category": "category2"
                }]),
                "coerce date and upper currency"
            ),
        ]
        for df_input, df_expected, label in cases:
            with self.subTest(label=label):
                # https://stackoverflow.com/questions/69535331/how-to-compare-2-dataframes-in-python-unittest-using-assert-methods
                self.assertEqual(
                    True,
                    df_expected.equals(
                        sanitize_df(df_input, self.category_list)
                    )
                )

    def test_sanitize_df_err_small(self):
        cases = [
            (
                pd.DataFrame([ ]),
                "empty dataframe"
            ),
            (
                pd.DataFrame([
                    {
                        "date" : "2024-10-12", 
                        "amount": -5,
                        "currency" : "EUR",
                        "description": "any",
                        "category" : "invalid"
                    }
                ]),
                "negative amount"
            ),
            (
                pd.DataFrame([
                    {
                        "date" : "2024-10-12", 
                        "amount": "not valid amount",
                        "currency" : "EUR",
                        "description": "any",
                        "category" : "invalid"
                    }
                ]),
                "invalid amount type"
            ),
            (
                pd.DataFrame([
                    {
                        "date" : "2024-10-12", 
                        "amount": 5,
                        "currency" : None,
                        "description": "any",
                        "category" : "invalid"
                    }
                ]),
                "Missing currency"
            ),
            (
                pd.DataFrame([
                    {
                        "date" : None, 
                        "amount": 5,
                        "currency" : "EUR",
                        "description": "any",
                        "category" : "invalid"
                    }
                ]),
                "Missing date"
            ),
            (
                pd.DataFrame([
                    {
                        "date" : "2024-10-12", 
                        "amount": 5,
                        "currency" : "EUR",
                        "description": print,
                        "category" : "invalid"
                    }
                ]),
                "description not string"
            ),
            (
                pd.DataFrame([
                    {
                        "date" : "2024-10-12", 
                        "amount": 5,
                        "currency" : "EUR",
                        "description": "any desc",
                        "category" : "invalid"
                    }
                ]),
                "category not in category list"
            ),
            (
                pd.DataFrame([
                    {
                        "date" : "foobarbaz", 
                        "amount": 5,
                        "currency" : "EUR",
                        "description": "any desc",
                        "category" : "category 8"
                    }
                ]),
                "invalid date str"
            ),
            (
                pd.DataFrame([
                    {
                        "date" : "2024-10-65", 
                        "amount": 5,
                        "currency" : "EUR",
                        "description": "any desc",
                        "category" : "category 8"
                    }
                ]),
                "datetime-like but not parsable"
            ),
            (
                pd.DataFrame([
                    {
                        "date" : "foobarbaz", 
                        "amount": 5,
                        "category" : "category 8"
                    }
                ]),
                "missing cols"
            ),
        ]    
        for df, label in cases:
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    sanitize_df(df, self.category_list)

    def test_sanitize_df_err_types(self):
        cases = [
            [],
            (),
            None,
            print,
            5,
            "not valid"
        ]
        for bad_df in cases:
            with self.subTest(input=bad_df):
                with self.assertRaises(TypeError):
                    sanitize_df(bad_df)


class TestRecordFromIDParser(TestCase):
    @staticmethod
    def mem_engine() -> Engine:
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        return engine
    
    today = date.today()

    @staticmethod
    def write(engine : Engine, *args, **kwargs) -> Record:
        with Session(engine) as session:
            record = Record(*args, **kwargs)
            session.add(record)
            session.commit()
            session.refresh(record)
        return record

    def test_id_success(self):
        engine = self.mem_engine()
        record = self.write(
            engine=engine,
            date=self.today,
            amount=0.65,
            currency="foo",
            description="foo",
            category = "foo")
        inputs = [ "1", 1.0, 1 ]
        for uinput in inputs:
            with self.subTest(uinput=uinput):
                self.assertEqual(record, parse_record_from_id(uinput, engine))

    def test_uinput_not_int_parsable(self):
        uinput = "not-int"
        engine = self.mem_engine()
        with self.assertRaises(ValueError):
            parse_record_from_id(uinput, engine)

    def test_int_parsable_but_inexistent(self):
        engine = self.mem_engine()
        uinput = "99999"
        with self.assertRaises(ValueError):
            parse_record_from_id(uinput, engine)

    def test_type_error(self):        
        bad_inputs = [ print, None ]
        engine = self.mem_engine()
        for uinput in bad_inputs:
            with self.assertRaises(TypeError):
                parse_record_from_id(uinput, engine)



if __name__ == "__main__":
    unittest.main()