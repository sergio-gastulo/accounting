from unittest import TestCase, main
from pkg.coreutils.functools import (success,
                                     softerror,
                                     early_return,
                                     type_check)
from tests._shared import (Patcher,
                           patch_builtin,)


class TestSuccess(TestCase):

    def test_success_single_arg(self):
        string = "hey"
        with patch_builtin(print) as mockprint:
            success(string)
        mockprint.assert_called_once()
        (printarg, ), _ = mockprint.call_args
        self.assertIn("Success: ", printarg)
        self.assertIn(string, printarg)

    def test_success_several_args(self):
        strings = ["hey", "there"]
        with patch_builtin(print) as mockprint:
            success(*strings)
        mockprint.assert_called_once()
        (printarg, ), _ = mockprint.call_args
        self.assertIn("Success: ", printarg)
        for string in strings:
            with self.subTest(str=string):
                self.assertIn(string, printarg)


class TestSoftError(TestCase):
    def test_simple_exc(self):
        err = ValueError(msg := "msg")
        errstr = str(type(err).__name__)
        with patch_builtin(print) as mockprint:
            softerror(err)
        (printarg, ), _ = mockprint.call_args
        mockprint.assert_called_once()
        self.assertIn(errstr, printarg)
        self.assertIn(msg, printarg)


class TestEarlyReturn(TestCase):

    def test_single_arg(self):
        called = False
        def f(int_):
            nonlocal called
            called = True
            return int_ + 999
        arg = 1
        res = early_return(int)(f)(arg)
        self.assertFalse(called)
        self.assertIs(res, arg)

    def test_argorder(self):
        called = False
        def f(int_, str_):
            nonlocal called
            called = True
            pass
        (intarg, strarg), narg = (1, "foo"), 1
        res = early_return(str, narg=narg)(f)(intarg, strarg)
        self.assertFalse(called)
        self.assertIs(res, strarg)

    def test_notype_does_evaluate(self):
        called = False
        expected = 999
        def f(int_, str_):
            nonlocal called
            called = True
            return expected
        narg = 1
        res = early_return(str, narg=narg)(f)("any", print)
        self.assertTrue(called)
        self.assertIs(res, expected)


class TestTypeCheck(TestCase):

    def test_simple_arg(self):
        anint = 4
        def f(x: int) -> int:
            return anint
        res = type_check(["x"])(f)(anint)
        self.assertIs(res, anint)

    def test_simple_raise(self):
        def f(x: int):
            pass
        notanint = print
        with self.assertRaises(TypeError):
            type_check(["x"])(f)(notanint)

    def test_noargs_but_returntypehint_passes(self):
        def f(x: int):
            pass
        try:
            type_check()(f)(1)
        except TypeError as e:
            self.fail(f"Unexpected: {e}.")
    
    def test_notypehints(self):
        def f(x, y, z):
            pass
        try:
            type_check(["x", "y", "z"])(f)(1, 2, 3)
        except TypeError as e:
            self.fail(f"Unexpected: {e}.")

    def test_noargs_passed_to_typecheck(self):
        def f(i: int, s: str, d: dict):
            pass
        try:
            type_check()(f)(1, "", {1: 1})
        except TypeError as e:
            self.fail(f"Unexpected: {e}.")

    def test_index_error_not_raised(self):
        def f(x: int, y: str = ""):
            pass
        try:
            type_check()(f)(1)
        except TypeError as e:
            self.fail(f"Unexpected: {e}.")

    def test_parametrized_generic_on_origin(self):
        """Test that at least the origin of the 
        generics is tested."""
        def f(x: dict[str, str], y: list[str]):
            pass
        try:
            type_check()(f)({1: 2}, [2])
        except TypeError as e:
            self.fail(f"Unexpected: {e}.")

    def test_uniontype(self):
        def f(x: int | str) -> int | str:
            return x
        try:
            type_check(["x"])(f)(1)
        except TypeError as e:
            self.fail(f"Unexpected: {e}.")


if __name__ == "__main__":
    main()