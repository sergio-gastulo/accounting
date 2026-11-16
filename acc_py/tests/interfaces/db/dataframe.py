from unittest import TestCase, skip
from unittest.mock import patch
import io
import datetime

import pandas as pd

from pkg.interfaces.db.dataframe import (pprint_df,
                                     is_datetime,
                                     is_record_like,
                                     has_recordid,
                                     sanitize_df,)
from tests._shared import TODAY


#TODO: test GEOACCESSOR


class TestIsDatetime(TestCase):
    def test_simple_cases(self):
        cases = (
            (
                pd.Series([TODAY, TODAY.replace(year=2020)]),
                "datetime like"
            ),
            (
                pd.date_range(start="1/1/2018", end="1/08/2018"),
                "date_range"
            ),
        )
        for df, label in cases:
            with self.subTest(label=label):
                self.assertTrue(is_datetime(df))



class TestHasRecordId(TestCase):
    def test_has_recordid(self):
        valids = [
            pd.DataFrame({"id": [1], "val": [2]}).set_index("id"),
            pd.DataFrame([1], columns=["id"]),
        ]
        for valid in valids:
            with self.subTest(valid=valid):
                self.assertTrue(has_recordid(valid))

    def test_doesnt_have_id(self):
        badcases = [
            pd.DataFrame([], columns=["idddss"]),
            pd.DataFrame({"ids": [2], "vals": [1]}).set_index("ids"),
        ]
        for bad in badcases:
            with self.subTest(bad=bad):
                self.assertFalse(has_recordid(bad))

    def test_hasid_but_notype(self):
        badcases = [
            pd.DataFrame([2.3], columns=["id"]),
            pd.DataFrame({"id": [1.0, 2.0], "vals": [1, 2]}).set_index("id"),
        ]
        for bad in badcases:
            with self.subTest(bad=bad):
                self.assertFalse(has_recordid(bad))

    def test_has_both(self):
        baddf = pd.DataFrame(dict(a=[1,2], id=[3,4])).set_index('id')
        baddf.columns = ["id"]
        self.assertFalse(has_recordid(baddf), msg=baddf)

        

class TestIsRecordLike(TestCase):

    recordcolumns = ["date", "amount", "currency", "description", "category"]
    recordid = "id"

    def test_good_columns(self):
        """Test that `df` contains record columns only returns `True`."""
        goodcolumns = [
            self.recordcolumns + [self.recordid],
            self.recordcolumns,
        ]
        for columns in goodcolumns:
            data = range(len(columns))
            df = pd.DataFrame(data).T
            df.columns = columns
            with self.subTest(column=columns):
                self.assertTrue(is_record_like(df), msg=df)

    def test_index(self):
        """Test that `df` can have an index called `id`"""
        data = range(len(self.recordcolumns) + 1)
        df = pd.DataFrame(data).T
        df.columns = self.recordcolumns + [self.recordid]
        df.set_index(self.recordid, inplace=True)
        self.assertTrue(is_record_like(df))

    def test_badcolumns(self):
        """Test that the following `df`s are not valid Record DataFrames."""
        badcolumns = [
            [],
            ["nothing", "thisisbad"],
            ["date", "currency", "almost"],
            self.recordcolumns + ["foo"],
        ]
        for columns in badcolumns:
            df = pd.DataFrame([], columns=columns)
            with self.subTest(column=columns):
                self.assertFalse(is_record_like(df))

    def test_idindex_and_idcolumn(self):
        data = range(len(self.recordcolumns) + 2)
        df = pd.DataFrame(data).T
        df.columns = self.recordcolumns + [self.recordid, "foo"]
        df.set_index(self.recordid)
        df.rename(columns={"foo": self.recordid})
        self.assertFalse(is_record_like(df), msg=df)


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
                    "date": datetime.date(2024, 12, 31),
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
                sanitized = sanitize_df(df_input, self.category_list)
                # https://stackoverflow.com/questions/69535331/how-to-compare-2-dataframes-in-python-unittest-using-assert-methods
                self.assertTrue(df_expected.equals(sanitized))

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
                "missing currency"
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


class TestDataFramePrettyPrinter(TestCase):
    
    def test_pprint_df_no_header(self):
        cases = [
            (

                pd.DataFrame({
                    "amount" : [1.11, 1.12], 
                    "description" : [
                        "long descriptiondescriptiondescriptiondescriptiondescriptiondescriptiondescriptiondescriptiondescriptiondescription 1",
                        "long descriptiondescriptiondescriptiondescriptiondescriptiondescriptiondescriptiondescriptiondescriptiondescription 2",
                    ]}),

                "+----------+------------------------------------------------------------------------------------------------------+\n"
                "|   amount | description                                                                                          |\n"
                "+==========+======================================================================================================+\n"
                "|     1.11 | long descriptiondescriptiondescriptiondescriptiondescriptiondescriptiondescriptiondescriptiondescrip |\n"
                "|     1.12 | long descriptiondescriptiondescriptiondescriptiondescriptiondescriptiondescriptiondescriptiondescrip |\n"
                "+----------+------------------------------------------------------------------------------------------------------+\n",
                
                "amount description"
            ),
            (
                
                pd.DataFrame({
                    "id" : [1729, 1730],
                    "amount" : [6.54, 1.32],
                    "description" : ["short 1", "short 2"]
                }).set_index('id'),
                
                "+------+----------+---------------+\n"
                "|   id |   amount | description   |\n"
                "+======+==========+===============+\n"
                "| 1729 |     6.54 | short 1       |\n"
                "| 1730 |     1.32 | short 2       |\n"
                "+------+----------+---------------+\n",

                "id, amount, description"
            ),
        ]
        for df, df_str, label in cases:
            with self.subTest(label=label):
                with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
                    pprint_df(df)
                    # self.maxDiff = 10000
                    self.assertEqual(
                        mock_stdout.getvalue(),
                        df_str
                    )

    def test_pprint_df_header(self):
        df = pd.DataFrame({
                    "id" : [1729, 1730],
                    "amount" : [6.54, 1.32],
                    "description" : ["short 1", "short 2"]
                }).set_index('id')
        header = "random string"
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            pprint_df(df, header)
            self.assertIn(header, mock_stdout.getvalue())

    def test_df_non_default_index_no_name(self):
        df = pd.DataFrame({"a" : [1, 2], "b" : [3, 4]}, index=list("AB"))
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            pprint_df(df)
            self.assertIn("A", mock_stdout.getvalue())

    def test_df_non_default_index_with_name(self):
        df = pd.DataFrame({"a" : [1, 2], "b" : [3, 4]})
        df.index.name = "foo"
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            pprint_df(df)
            self.assertIn("foo", mock_stdout.getvalue())
        
    def test_df_formats_datetypes(self):
        df = pd.DataFrame({"date": ['2015-08-10', '2015-08-11']})
        df["date"] = pd.to_datetime(df["date"])
        expected_month = "August"
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            pprint_df(df)
            self.assertIn(expected_month, mock_stdout.getvalue())

    def test_year_isnt_printed(self):
        df = pd.DataFrame({"date": ['2015-08-10', '2015-08-10']})
        df["date"] = pd.to_datetime(df["date"])
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            pprint_df(df)
            self.assertNotIn("2010", mock_stdout.getvalue())


