import unittest
from unittest.mock import patch

# general
from pathlib import Path
import pandas as pd
import io

# submodule being tested
from utilities.miscellanea import *


TEST_FILE_DIRECTORY = Path(__file__).parent / "files"


class TestFieldImporter(unittest.TestCase):
    
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
                with patch('utilities.miscellanea._jopen') as mock_jopen:
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
                with patch('utilities.miscellanea._jopen') as mock_jopen:
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


@unittest.skip("TODO: Implement later.")
class TestFunctionDocumentationPrinter(unittest.TestCase):
    pass


class TestDataFramePrettyPrinter(unittest.TestCase):
    
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
        cases = [
            (
                
                pd.DataFrame({
                    "id" : [1729, 1730],
                    "amount" : [6.54, 1.32],
                    "description" : ["short 1", "short 2"]
                }).set_index('id'),
                
                "header",

                "+------+----------+---------------+\n"
                "header\n"
                "+------+----------+---------------+\n"
                "|   id |   amount | description   |\n"
                "+======+==========+===============+\n"
                "| 1729 |     6.54 | short 1       |\n"
                "| 1730 |     1.32 | short 2       |\n"
                "+------+----------+---------------+\n"

            ),
        ]  
        for df, header, df_str in cases:
            with self.subTest(header=header):
                with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
                    pprint_df(df, header)
                    # self.maxDiff = 10000
                    self.assertEqual(
                        mock_stdout.getvalue(),
                        df_str
                    )


@unittest.skip("TODO: do we really need to test it?")
class TestHasInternet(unittest.TestCase):
    pass


class TestGetHelpDictionary(unittest.TestCase):
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


class TestCategoriesPrettyPrinter(unittest.TestCase):
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


class TestGetAllCategories(unittest.TestCase):
    def test_get_all_categories(self):
        category_dict = [
            {
                "shortname" : "foobarbaz",
                "another_field": "another field",
                "subcategories" : [
                    {
                        "shortname" : "foobarbaz2",
                        "random_field" : "random_field"
                    },
                    {
                        "shortname" : "foobarbaz3"
                    }
                ]
            },
            {
                "shortname" : "imagination",
                "different_field" : "diff"
            }
        ]
        expected = [
            "foobarbaz",
            "foobarbaz2",
            "foobarbaz3",
            "imagination"
        ]
        self.assertEqual(
            get_all_categories(category_dict),
            expected
        )

    def test_get_all_categories_err(self):
        bad_category_dict = [
            {
                "not_shortname" : "any"
            }
        ]
        with self.assertRaises(ValueError):
            get_all_categories(bad_category_dict)


class TestCategoryDictionaryFetcher(unittest.TestCase):
    def test_fetch_category_dictionary(self):
        cases = [
            (
                [
                    {
                        "shortname" : "cat_1",
                        "description" : "category 1"
                    },
                    {
                        "shortname" : "cat_2",
                        "description" : "category 2"
                    }
                ],
                {
                    "cat_1" : "category 1",
                    "cat_2" : "category 2",
                },
                "no nesting"
            ),
            (
                [
                    {
                        "shortname" : "cat_1",
                        "description" : "category 1",
                        "subcategories" : [
                            {
                                "shortname" : "cat_2",
                                "description" : "category 2"
                            }
                        ]
                    }
                ],
                {
                    "cat_2" : "category 2"
                },
                "nesting"
            )
        ]
        for field_input, expected, label in cases:
            with self.subTest(label=label):
                self.assertEqual(
                    fetch_category_dictionary(field_input),
                    expected
                )
                
@unittest.skip("Working on it")
class TestSortDictionary(unittest.TestCase):
    pass


@unittest.skip("Working on it")
class TestKeybindDictionaryFetcher(unittest.TestCase):
    def test_fetch_keybind_dict(self):
        pass











if __name__ == "__main__":
    unittest.main()