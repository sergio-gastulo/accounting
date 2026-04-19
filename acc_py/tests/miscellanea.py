import unittest

from pathlib import Path
from utilities.miscellanea import *
import json


TEST_FILE_DIRECTORY = Path(__file__).parent / "files"


class TestGetAllCategories(unittest.TestCase):
    def test_get_all_categories(self):
        with open(TEST_FILE_DIRECTORY / "miscellanea.json") as file:
            category_dict = json.load(file)
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




if __name__ == "__main__":
    unittest.main()