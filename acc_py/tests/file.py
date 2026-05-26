import unittest
from unittest import TestCase
from unittest.mock import (
    patch, 
    MagicMock,
    mock_open
)
from typing import Callable
from pathlib import Path

import pandas as pd

from tests._shared import (
    RUN_API_TEST,
    TEST_FILE_DIRECTORY,
    Patcher
)
from utilities.file import (
    fimport, 
    fexport, 
    open_file_with_editor,
)


#region ============================ utils  ====================================

TEST_MODULE = 'utilities.files'

def _patch_this(f: Callable | str, **kwargs) -> Patcher:
    return Patcher(TEST_MODULE, f, **kwargs)

#endregion =====================================================================



class TestFileExport(TestCase): 

    @classmethod
    def setUpClass(cls):
        cls.csv = TEST_FILE_DIRECTORY / "tmp.csv"
        cls.json = TEST_FILE_DIRECTORY / "tmp.json"
        return super().setUpClass()

    def test_df_export(self):
        df = pd.DataFrame({"a" : [1,2,3], "b" : [1,2,4]})
        m : MagicMock = mock_open()
        with (
            patch('pandas.DataFrame.to_csv') as mock_tocsv,
            patch('builtins.open', m)
        ):
            fexport(df, self.csv)
        p, how = m.call_args.args
        self.assertEqual(how, "w")
        self.assertEqual(p, self.csv)
        _stream, kwargs = mock_tocsv.call_args
        self.assertIn("force_ascii", kwargs)

    def test_unsupported_type(self):
        unsupported = [
            print, dict, "primitive: ", 654, None 
        ]
        for bad in unsupported:
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    fexport(bad)
    
    def test_invalid_extension(self):
        invalids = ["foo.jsonc", "bar.yaml", "baz.toml"]
        df = pd.DataFrame({"a" : [1,2,3], "b" : [1,2,4]})
        for invalid in invalids:
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    fexport(df, Path(invalid))

    def test_dict_but_not_json(self):
        obj = {"a" : [1,2,3], "b" : list("abc")}
        with self.assertRaises(ValueError):
            fexport(obj, self.csv)
    
    
    @classmethod
    def tearDownClass(cls):
        cls.csv.unlink(missing_ok=True)
        cls.json.unlink(missing_ok=True)


@unittest.skip("TODO...")
class TestFetch(TestCase):
    pass


if __name__ == "__main__":
    unittest.main()