import unittest
from unittest import TestCase
from typing import Callable

from tests._shared import (
    RUN_API_TEST,
    TEST_FILE_DIRECTORY,
    Patcher
)



#region ============================ utils  ====================================

TEST_MODULE = 'utilities.currency'

def _patch_this(f: Callable | str, **kwargs) -> Patcher:
    return Patcher(TEST_MODULE, f, **kwargs)

#endregion =====================================================================