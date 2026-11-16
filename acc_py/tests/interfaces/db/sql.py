from unittest import TestCase
from unittest.mock import call
import datetime
from typing import Callable

from sqlalchemy.dialects import sqlite
from sqlalchemy import true, and_
from sqlalchemy.sql.elements import ColumnElement

from pkg.classes.model import Record
from pkg.coreutils.parser.dates import parse_date
from pkg.interfaces.db.sql import (ParseSQLError,
                                   ordering_query,
                                   string_query,
                                   date_query,
                                   sql_query,
                                   parse_semantic_query,)
from tests._shared import (TODAY,
                           Patcher,)


TEST_MODULE = 'pkg.interfaces.db.sql'
def patch(f: Callable | str, **kwargs) -> Patcher:
    return Patcher(TEST_MODULE, f, **kwargs)


def compile_sql(sql: ColumnElement[bool]) -> str:
    """Compiles sqlachemy stmt to vanilla sqlite3."""
    dialect = sqlite.dialect()
    kwargs = {"literal_binds" : True}
    return str(sql.compile(dialect=dialect, 
                           compile_kwargs=kwargs))


class TestOrderingQuery(TestCase):

    def wrap(self, query, *args):
        return compile_sql(ordering_query(query, *args)) 

    def test_basic_queries(self):
        queries = [
            ("amount between 1 and  2", Record.amount.between(1., 2.)),
            ("1 <= amount <= 2 ", and_(1. <= Record.amount, Record.amount <= 2.)),
            ("    1 < amount  ", 1. < Record.amount),
            ("   id > 2  ", Record.id > 2.),
            (" id == 2", Record.id == 2.),
            (" amount    =   2.3 ", Record.amount == 2.3)
        ]
        for (rawinput, expected) in queries:
            with self.subTest(query=rawinput):
                self.assertEqual(self.wrap(rawinput),
                                 compile_sql(expected))

    def test_map_is_correclty_called(self):
        # NOTE: mock map_ and verify that is correclty called under different 
        # queries
        pass

    def test_parse_error(self):
        badqueries = [
            "amountt > 222",
            "  non-existent <<<>>   22",
            "foo bsr bar > 2 amount",
            "amount < amount <<< 2 * amount"
        ]
        for badquery in badqueries:
            with self.subTest(query=badquery):
                with self.assertRaises(ParseSQLError):
                    ordering_query(badquery)

    def test_parsesuccess_mapfailure(self):
        """
        `map_` should always raise an error if it fails to convert the 
        values. `ValueError` is recommended.
        """
        badqueries = [
            "amount > foo",
            "id between foo and bar",
            "id < amount < foo"
        ]
        for badquery in badqueries:
            with self.subTest(query=badquery):
                with self.assertRaises(ValueError):
                    ordering_query(badquery)


class TestStringQuery(TestCase):

    def wrap(self, query, *args):
        return compile_sql(string_query(query, *args))

    def test_like(self):
        cases = [
            ('category like foobarbaz%', Record.category.like('foobarbaz%')),
            ('description like \'           food%     \'  ', Record.description.like('food%')),
            ('      currency       wildcard \"food%\"', Record.currency.like('food%')),
            ( 'description like %uten%', Record.description.like('%uten%'))
        ]
        for query, expected in cases:
            with self.subTest(query=query):
                self.assertEqual(compile_sql(expected), self.wrap(query))

    def test_equals(self):
        cases = [
            ('currency = "USD"', Record.currency == "USD"),
            ('   category == "USD"', Record.category == "USD"),
            ('   category   foobar', Record.category == "foobar"),
            ('currency eq USD', Record.currency == "USD"),
        ]
        for query, expected in cases:
            with self.subTest(query=query):
                self.assertEqual(compile_sql(expected),
                                 self.wrap(query))

    def test_regex(self):
        cases = [
            ('   currency regex expr', Record.currency.regexp_match('expr')),
            ('   date   regexp   2025-08*', Record.date.regexp_match('2025-08*')),
            (' description regexp "milk" ', Record.description.regexp_match('milk')),
            ('description regex  ^beg\\.end$', Record.description.regexp_match('^beg\\.end$'))
        ]
        for query, expected in cases:
            with self.subTest(query=query):
                self.assertEqual(compile_sql(expected),
                                 self.wrap(query))

    def test_parseerr(self):
        badqueries = [
            'nonexistentcolumn regex foo',
            '   anothernonexisteent like adfsfasdf ads fadsf ',
            '    description = ',
            '   date regexp',
        ]
        for badquery in badqueries:
            with self.subTest(query=badquery):
                with self.assertRaises(ParseSQLError):
                    string_query(badquery)


class TestDateQuery(TestCase):

    def wrap(self, query, *args):
        return compile_sql(date_query(query, *args))

    def test_date_like(self):
        cases = [
            ('date like 2025-12%', '2025-12%'),
            ('date like \'2025-12%\'', '2025-12%'),
        ]
        for query, expected in cases:
            with self.subTest(query=query):
                self.assertEqual(compile_sql(Record.date.like(expected)),
                                 self.wrap(query))

    def test_date_parse(self):
        """
        Test that query is correctly parsed and `parse_date` 
        is correctly called with the expected arguments.
        """
        cases = [
            ('date = 2025 10 31', '2025 10 31', datetime.date(year=2025, month=10, day=31)),
            ('date = \'2025 10 31\'', '\'2025 10 31\'', datetime.date(year=2025, month=10, day=31)),
            ('date = -12', '-12', TODAY + datetime.timedelta(days=-12)),
            ('date == 0', '0', TODAY)
        ]
        for query, date_call, expected in cases:
            with (self.subTest(query=query), 
                  patch(parse_date) as mock_dateparser):
                mock_dateparser.return_value = expected
                result = self.wrap(query)
                mock_dateparser.assert_called_once_with(date_call)
                self.assertEqual(result,
                                 compile_sql(Record.date == expected))

    def test_date_regex(self):
        cases = [
            'date regex 2025-01',
            'date regexp 2025-01',
        ]
        for date_regex_filter in cases:
            with self.subTest(date_regex_filter=date_regex_filter):
                self.assertEqual(self.wrap(date_regex_filter),
                                 compile_sql(Record.date.regexp_match('2025-01')))

    def test_parse_error(self):
        badqueries = [
            'dte = 2025-13-12',
        ]
        for badquery in badqueries:
            with self.subTest(badquery=badquery):
                with self.assertRaises(ParseSQLError):
                    self.wrap(badquery)

    def test_parsesuccess_mapfailure(self):
        badqueries = [
            'date = 99',
            'date = \'18 - 2015 - 65\'',
        ]
        for badquery in badqueries:
            with self.subTest(badquery=badquery):
                with self.assertRaises(ValueError):
                    self.wrap(badquery)


class TestSQLQuery(TestCase):

    def test_correct_redirects(self):
        cases = [
            ("date between a and b", date_query),
            ("amount > 13", ordering_query),
            ("id between 2023 and 2045", ordering_query),
            ("   description like %asdf%", string_query),
            ("currency USD", string_query),
        ]
        for query, redirectfunc in cases:
            with self.subTest(query=query, func=redirectfunc.__name__):
                with patch(redirectfunc) as mock_func:
                    sql_query(query)
                mock_func.assert_called_once_with(query)

    def test_true(self):
        trues = ["all", "true", "True", "All"]
        for true_ in trues:
            with self.subTest(truequery=true_):
                self.assertIs(sql_query(true_), true())

    def test_generic_err(self):
        cases = [
            "false",
            "update cuentas set currency=BROKEN",
            "SELECT sql FROM sqlite_master",
            "not a valid query",
            "foo"
        ]
        for invalid in cases:
            with self.subTest(invalid=invalid):
                with self.assertRaises(ParseSQLError):
                    sql_query(invalid)


# TODO: single query fails
class TestSemanticFilterParser(TestCase):
    
    def test_query_is_splitted(self):
        query = "a && b && c"
        with patch(sql_query) as mock_sql:
            mock_sql.return_value = true()
            parse_semantic_query(query)
        mock_sql.assert_has_calls([call("a"), call("b"), call("c")])


    def test_replacement(self):
        """Test that `sql_query` is called with correct arguments."""
        query = "[date between 1 and 24] or [currency USD]"
        left = "date between 1 and 24"
        right = "currency USD"
        with patch(sql_query) as mock_sql:
            mock_sql.return_value = true()
            parse_semantic_query(query)
        mock_sql.assert_has_calls([call(left), call(right)])


    def test_simple_query(self):
        cases = [
            ('description like test% && date = 2', ("cuentas.description", "test%", "date")),
            ('      [currency  =     EUR] OR         [amount < 2.3]', ("cuentas.currency", "cuentas.amount", "2.3", "EUR")),
            ('   && &&                    && &&           ', ("1 = 1")),  # true = 1 == 1
        ]
        for raw_query, keywords in cases:
            with self.subTest(raw_query=raw_query):
                compiled = compile_sql(parse_semantic_query(raw_query))
                for keyword in keywords:
                    with self.subTest(keyword=keyword):
                        self.assertIn(keyword, compiled)