from unittest import TestCase, skip
from unittest.mock import MagicMock, patch
from typing import Callable
from pathlib import Path

from pkg.coreutils.file import (file_open,
                                check_editor,
                                askeditor,)
from pkg.coreutils.paths import (PROJECT_DIRECTORY,
                                 PYTHON_MODULE)
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


class TestFileOpen(TestCase):

    editor = "mocked"

    def test_file_open_resolves_to_projectdir(self):
        readme = "readme.md"
        arg = f"/{PROJECT_DIRECTORY}/{readme}"
        with patch("subprocess.call") as mockcall:
            res = file_open(arg, self.editor)
        (_, subprocess_path),  = mockcall.call_args.args
        mockcall.assert_called_once()
        for paths in [res, subprocess_path]:
            with self.subTest(path=paths):
                split = paths.parts
                for name in [PROJECT_DIRECTORY.name, readme]:
                    with self.subTest(name=name):
                        self.assertIn(name, split)

    def test_file_open_resolves_to_module(self):
        main = "main.py"
        arg = f"/{PYTHON_MODULE.module_source}/{main}"
        with patch("subprocess.call") as mockcall:
            res = file_open(arg, self.editor)
        (_, subprocess_path),  = mockcall.call_args.args
        mockcall.assert_called_once()
        for paths in [res, subprocess_path]:
            with self.subTest(path=paths):
                split = paths.parts
                for name in [PYTHON_MODULE.module_source, main]:
                    with self.subTest(name=name):
                        self.assertIn(name, split)


    def test_opendir(self):
        opendir = False
        dir_ = Path().home()
        with self.assertRaises(ValueError):
            file_open(dir_, self.editor, opendir=opendir)