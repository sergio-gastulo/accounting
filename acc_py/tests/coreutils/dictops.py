from unittest import TestCase
from unittest.mock import patch
import io
import json

from pkg.coreutils.jops import jopen
from pkg.coreutils.dictops import (import_fields,
                                   get_help_dictionary,
                                   pprint_categories,
                                   fetch_keybind_dict,
                                   fetch_category_dictionary,)
from tests._shared import (TEST_FILE_DIRECTORY,
                           Patcher,)


TEST_MODULE = "pkg.coreutils.dictops"
def patchf(f, **kwargs):
    return Patcher(TEST_MODULE, f, **kwargs)



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
                with patchf(jopen) as mock_jopen:
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
                with patchf(jopen) as mock_jopen:
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
            with self.subTest(label=label, msg=field_dict):
                self.assertEqual(
                    fetch_keybind_dict(field_dict),
                    expected,
                )



class TestCategoryDictionaryFetcher(TestCase):
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
