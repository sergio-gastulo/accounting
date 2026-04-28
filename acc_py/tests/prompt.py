import unittest
from unittest.mock import patch, MagicMock
from typing import Callable
from tests._shared import (
    TEST_FILE_DIRECTORY,
    patch_this,
)


#region ============================ utils =====================================

TEST_MODULE = 'utilities.prompt'

def _patch_this(f : Callable | str) -> MagicMock:
    return patch_this(TEST_MODULE, f)


def _patch_input() -> MagicMock:
    return patch('builtins.input')

#endregion =====================================================================


@unittest.skip("Playing with input mocker.")
class TestInputMocker(unittest.TestCase):

    def test(self):
        with _patch_input() as mock_input:
            mock_input.return_value = 5
            self.assertEqual(
                input(),
                5
            )


class TestMainLoop(unittest.TestCase):

    def test_main_loop(self):
        pass





if __name__ == "__main__":
    unittest.main()