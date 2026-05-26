import unittest
from unittest import TestCase
from unittest.mock import patch, call
import io
import json
from pathlib import Path
from typing import Callable

import pandas as pd

from tests._shared import (
    TEST_FILE_DIRECTORY, 
    Patcher
)
from utilities.core import (
    import_fields,
    pprint_df,
    get_help_dictionary,
    pprint_categories,
    fetch_keybind_dict,
    check_editor,
    convert_rgb,
    check_colors,
)


#region ========================= quick utils ==================================

TEST_MODULE = 'utilities.core'

def _patch_this(f: Callable | str, **kwargs) -> Patcher:
    return Patcher(TEST_MODULE, f, **kwargs)

#endregion =====================================================================


class TestFieldImporter(TestCase):
    
    def test_import_fields(self):
        cases = [
            (
                [
                    {
                        "key" : "key",
                        "shortname" : "cat 1",
                        "description" : "nice cat 1 description"
                    }, 
                    {
                        "key" : "key 2",
                        "shortname" : "cat 2",
                        "description" : "nice cat 1 description",
                        "subcategories" : [
                            { 
                                "key" : "foo",
                                "shortname" : "foo 2",
                                "description" : "foo 3"
                            }
                        ] 
                    }, 
                ],
                "simple cat dict"
            ),
        ]
        for cat_dict, label in cases:
            with self.subTest(label=label):
                with _patch_this('_jopen') as mock_jopen:
                    mock_jopen.return_value = cat_dict
                    self.assertEqual(
                        import_fields("mocked/path"),
                        cat_dict
                    )

    def test_import_fields_err(self):
        cases = [
            (
                [ { "key" : "any", "description" : "any" } ],
                "no shortname"
            ),
            (
                [ { "shortname" : "any", "key" : "any"} ],
                "no description"
            ),
            (
                [ { "description" : "any", "shortname" : "any"} ],
                "no key"
            ),
            (
                [ { "shortname" : 654654 } ],
                "key is not str"
            ),
            (
                [  ],
                "not a single record"
            ),
            (
                [ { } ],
                "not a single record-2"
            ),
        ]
        for cat_dict, label in cases:
            with self.subTest(label=label):
                with _patch_this('_jopen') as mock_jopen:
                    mock_jopen.return_value = cat_dict
                    with self.assertRaises(ValueError):
                        import_fields("mocked/path")

    def test_import_fields_json_err(self):
        n = 3
        root = lambda i : f"test_import_fields_json_err_{i}.json"
        for i in range(n):
            path = TEST_FILE_DIRECTORY / root(i + 1)
            with self.subTest(i=i):
                with self.assertRaises(json.decoder.JSONDecodeError):
                    import_fields(path)


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
        


@unittest.skip("TODO: do we really need to test it?")
class TestHasInternet(TestCase):
    pass


class TestGetHelpDictionary(TestCase):
    def test_pprint_categories_help(self):
        field_dict = [
            {
                "shortname" : "category 1",
                "help" : "long category help",
                "subcategories" : [
                    {
                        "shortname" : "category 2",
                        "help" : "another long help"
                    }
                ]
            },
            {
                "shortname" : "cat 3"
            }
        ]
        expected = {
            "category 1" : "long category help", 
            "category 2" : "another long help",
            "cat 3" : ''
        }
        self.assertEqual(
            get_help_dictionary(field_dict),
            expected
        )

    def test_pprint_categories_help_err(self):
        cases = [
            print, 
            None
        ]
        for bad_input in cases:
            with self.assertRaises(TypeError):
                get_help_dictionary(bad_input)


class TestCategoriesPrettyPrinter(TestCase):
    def test_pprint_categories_no_help(self):
        cases = [
            (
                [
                    {'a' : 1, 'b' : 2}, 
                    {'a' : 3, 'b' : 'str'}
                ],

                [ { "shortname" : "field_dict" } ],

                '[\n    {\n        "a": 1,\n        "b": 2\n    },\n    {\n        "a": 3,\n        "b": "str"\n    }\n]\n',

                "simple json dumps"

            ),
        ]

        for cat_dict, field_dict, expected, label in cases:
            with self.subTest(label=label):
                with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
                    pprint_categories(cat_dict, field_dict)
                    self.assertEqual(
                        mock_stdout.getvalue(),
                        expected
                    )

    def test_pprint_categories_no_help_err(self):
        cases = [
            print,
        ]
        placeholder = [ { "shortname" : "pass" }]
        for bad_category_dict in cases:
            with self.assertRaises(TypeError):
                pprint_categories(bad_category_dict, placeholder)

    def test_pprint_categories_help(self):
        field_dict = [
            { "shortname" : "cat_1" },
            { "shortname" : "cat_2", "help" : "short help" }
        ]
        expected = '{\n    "cat_1": "",\n    "cat_2": "short help"\n}\n'
        with patch('sys.stdout', new_callable=io.StringIO) as mock_print:
            pprint_categories("any", field_dict, True)
            self.assertEqual(
                mock_print.getvalue(),
                expected
            )


class TestKeybindDictionaryFetcher(TestCase):
    def test_fetch_keybind_dict(self):
        cases = [
            (
                [
                    {
                        "shortname" : "foo",
                        "key" : "f",
                        "subcategories" : [
                            {
                                "shortname" : "bar",
                                "key" : "b"
                            }
                        ]
                    },
                    {
                        "shortname" : "category 1",
                        "key" : "c1"
                    }
                ],
                {
                    "c1" : "category 1", 
                    "f" : {
                        "b" : "bar"
                    }
                },
                "simple nested"
            ),
        ]
        for field_dict, expected, label in cases:
            with self.subTest(label=label):
                self.assertEqual(
                    fetch_keybind_dict(field_dict),
                    expected
                )


class TestEditorChecker(TestCase):

    def test_check_editor(self):
        editor = r'C:\Program Files\Notepad++\notepad++.exe'
        self.assertEqual(
            check_editor(editor),
            Path(editor)
        )

    def test_check_editor_err(self):
        bad_args = [
            print, 
            55,           
        ]
        for bad_arg in bad_args:
            with self.subTest(bad_arg=bad_arg):
                with self.assertRaises(TypeError):
                    check_editor(bad_arg)

    def test_check_editor_asks_for_file(self):
        any_args = [
            "invalid-path",
            None,
            Path("wrapped-but-invalid"),
        ]
        for arg in any_args:
            with self.subTest(arg=arg):
                with _patch_this('_ask_editor') as mock_ask_editor:
                    check_editor(arg)
                    mock_ask_editor.assert_called_once()


class TestRGBConverter(TestCase):
    def test_convert_rgb(self):
        cases = [
            ([255, 255, 255],   (1.0, 1.0, 1.0)),
            ([1.0, 0.0, 0.5],   (1.0, 0.0, 0.5)),
            ((0, 0, 0, 0),      (0, 0, 0, 0)),
            ((1.0, 128, 0, 0),  (1.0, 128 / 255, 0, 0))
        ]
        for color, expected in cases:
            with self.subTest(color=color):
                self.assertEqual(
                    convert_rgb(color), 
                    expected
                )

    def test_convert_rgb_err(self):
        cases = [
            ("foo",                 TypeError),
            ((300, 200, 100, 0),    ValueError),
            ([1.0, 1.1, 1.0, 1.5],  ValueError)
        ]
        for bad_color, err in cases:
            with self.subTest(bad_color=bad_color):
                with self.assertRaises(err):
                    convert_rgb(bad_color)


class TestColorChecker(TestCase):
    def test_check_colors(self):
        currencies = ["per", "eur", "usa"]
        colors = ["red", "blue", [1.0, 0.5, 0.5]]
        expected = {
            "per" : (1.0, 0.0, 0.0),
            "eur" : (0.0, 0.0, 1.0),
            "usa" : (1.0, 0.5, 0.5)
        }
        self.assertEqual(check_colors(currencies, colors), expected)

    def test_check_colors_dimensions_1(self):
        """more colors than currencies"""
        currencies = [ "per" ]
        colors = ["red", "blue", [1.0, 0.5, 0.5]]
        expected = {
            "per" : (1.0, 0.0, 0.0)
        }
        self.assertEqual(check_colors(currencies, colors), expected)

    def test_check_colors_dimensions_2(self):
        """more currencies than colors"""
        currencies = [ "per", "eur", "usd" ]
        colors = [ "red" ]
        test_color = (0.5, 0.5, 0.5)
        expected = {
            "per" : (1, 0, 0),
            "eur" : test_color, 
            "usd" : test_color
        }
        with _patch_this('_ask_color') as mock_ask_color:
            mock_ask_color.return_value = (0.5, 0.5, 0.5), "hex"
            self.assertEqual(
                check_colors(currencies, colors),
                expected
            )
            mock_ask_color.assert_has_calls([call("eur"), call("usd")])

    def test_check_colors_err(self):
        currencies = [ "per", "eur" ]
        colors = [ "red", "not-a-color" ]
        with self.assertRaises(ValueError):
            check_colors(currencies, colors)

    def test_none_type(self):
        currencies = [ "per", "eur" ]
        colors = [ "red", None ]
        with self.assertRaises(ValueError):
            check_colors(currencies, colors)


if __name__ == "__main__":
    unittest.main()