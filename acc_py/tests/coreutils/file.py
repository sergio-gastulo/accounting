from unittest import TestCase, skip
from typing import Callable
from pathlib import Path

from pkg.coreutils.file import (file_open,
                                check_editor,
                                askeditor,)

from tests._shared import (TEST_FILE_DIRECTORY,
                           Patcher,
                           patch_builtin,)


TEST_MODULE = 'pkg.coreutils.file'
def patchf(f: Callable | str, **kwargs) -> Patcher:
    return Patcher(TEST_MODULE, f, **kwargs)


@skip(reason="Geeks4Geeks function.")
class TestSHA256(TestCase):
    pass

@skip(reason="StackOverflow function.")
class TestRMDIR(TestCase):
    pass


class TestAskEditor(TestCase):
    def test_simple_workflow(self):
        with (patchf('askopenfilename',
                     return_value=Path()) as mock_asker,
              patch_builtin(print) as mock_print):
            res = askeditor()
        mock_print.assert_called_once()  # args are not important to test
        _, kwargs = mock_asker.call_args
        self.assertIn("initialdir", kwargs)
        self.assertIn("Select", kwargs["title"])
        self.assertIn("filetypes", kwargs)
        self.assertIsInstance(res, Path)


class TestEditorChecker(TestCase):

    def test_check_editor(self):
        editor = r'C:\Program Files\Notepad++\notepad++.exe'
        self.assertEqual(check_editor(editor),
                         Path(editor))

    def test_check_editor_err(self):
        bad_args = [print, 55]
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
                with patchf(askeditor) as mock_ask_editor:
                    check_editor(arg)
                mock_ask_editor.assert_called_once_with()

@skip(reason="TODO.")
class TestFileOpen(TestCase):
    pass