from unittest import TestCase, skip
from unittest.mock import patch, MagicMock, call
from typing import Callable
from io import StringIO
from datetime import date

from pkg.coreutils.prompt import (softerror,
                                  success,
                                  main_loop,
                                  prompt_arithmetic_operation,
                                  prompt_category_from_keybinds,
                                  prompt_currency,
                                  prompt_date_operation,
                                  prompt_double_currency,
                                  get_from_nested_dict,)
from tests._shared import (Patcher,
                           patch_builtin,)


TEST_MODULE = 'pkg.coreutils.prompt'
PATCH_STDOUT = patch('sys.stdout', new_callable=StringIO)

def patchf(f: Callable | str, **kwargs) -> Patcher:
    return Patcher(TEST_MODULE, f, **kwargs)


@skip(reason="TODO: ")
class TestEarlyReturn(TestCase):
    pass

@skip(reason="TODO: ")
class TestTypeCheck(TestCase):
    pass



class TestMainLoop(TestCase):

    def test_uinput_provided_parses_immediately(self):
        with patch_builtin(input) as mock_input:
            result = main_loop(uinput="42", prompt="enter: ", parser=int)
        mock_input.assert_not_called()
        self.assertEqual(result, 42)

    def test_uinput_none_succeeds_first_try(self):
        with patch_builtin(input) as mock_input:
            mock_input.return_value = "1"
            res = main_loop(uinput=None, prompt="any: ", parser=int)
        mock_input.assert_called_once()
        self.assertEqual(res, 1)

    def test_kwargs_forwarded_to_parser(self):
        mock_parser = MagicMock(return_value="ok")
        main_loop(uinput="hello", prompt="", parser=mock_parser, other=1, another=16)
        mock_parser.assert_called_once_with("hello", other=1, another=16)

    def test_succeeds_on_last_attempt(self):
        max_attempts = 5
        icall = "any: "
        return_input = [ "bad" ] * ( max_attempts - 1 ) + [ "5" ]
        with (
            patch_builtin(input) as mock_input,
            PATCH_STDOUT
        ):
            mock_input.side_effect = return_input
            res = main_loop(uinput=None, prompt=icall, parser=int, max_attempts=max_attempts)
        self.assertEqual(res, 5)
        mock_input.assert_has_calls([call(icall)] * max_attempts)

    def test_on_error_called_per_bad_input(self):
        on_error = MagicMock()
        inputs = ["bad", "bad", "3"]
        with ( patch_builtin(input) as mock_input, PATCH_STDOUT ):
            mock_input.side_effect = inputs
            res = main_loop(uinput=None, prompt="any: ", parser=int, on_error=on_error)
        self.assertEqual(on_error.call_count, 2)
        self.assertEqual(res, 3)

    def test_uinput_reset_to_none_after_error(self):
        call_log = []
        def _parser(value):
            call_log.append(value)
            return int(value)

        inputs = ["bad", "good", "42"]
        with ( patch_builtin(input) as mock_input, PATCH_STDOUT ):
            mock_input.side_effect = inputs
            main_loop(uinput=None, prompt="any: ", parser=_parser)
        self.assertEqual(call_log, inputs)

    def test_exhausted_attempts_raises_runtime_error(self):
        max_attempts = 3
        icall = "any: "
        return_input = [ "bad" ] * ( max_attempts + 1 ) + [ "5" ]
        with ( patch_builtin(input) as mock_input, PATCH_STDOUT ):
            mock_input.side_effect = return_input
            with self.assertRaises(RuntimeError) as errctx:
                main_loop(uinput=None, prompt=icall, parser=int, max_attempts=max_attempts)
        self.assertIn("3 attempts.", str(errctx.exception))

    def test_type_error_triggers_retry(self):
        call_count = 0
        def _parser(value : str):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise TypeError("generic")
            return value.upper()
        
        on_error = MagicMock()
        with (patch_builtin(input) as mock_input, PATCH_STDOUT):
            mock_input.side_effect = ["bad", "good"]
            res = main_loop(uinput=None, prompt="", parser=_parser, on_error=on_error)
        self.assertEqual(res, "GOOD")
        on_error.assert_called_once()

    def test_max_attempts_one_invalid_raises(self):
        max_attempts = 1
        with self.assertRaises(RuntimeError), PATCH_STDOUT:
            main_loop(uinput="bad", prompt="", parser=int, max_attempts=max_attempts)



class TestArithmeticOperationPrompt(TestCase):

    def test_early_return_type(self):
        cases = [99, -5.0]
        for case in cases:
            with self.subTest(case=case):
                self.assertEqual(
                    prompt_arithmetic_operation(case, -99), 
                    case
                )

    def test_nostring_fails(self):
        bad_cases = [print, {}]
        for bad in bad_cases:
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    prompt_arithmetic_operation(bad)

    def test_calls(self):
        uinput = "+99 - 55"
        expected = 44
        with (
            patchf(main_loop) as mock_main,
            patchf(success) as mock_success,
            PATCH_STDOUT
        ):
            mock_main.side_effect = [ expected ]
            res = prompt_arithmetic_operation(uinput)
        mock_main.assert_called_once()
        mock_success.assert_called_once()
        self.assertEqual(res, expected)
        _, kwargs = mock_main.call_args
        self.assertIn("operation", kwargs["prompt"])
        self.assertIn("parser", kwargs)



class TestDateOperationPrompt(TestCase):

    def test_calls(self):
        uinput = "0"
        expected = date.today()
        with (
            patchf(main_loop) as mock_main,
            patchf(success) as mock_success,
            PATCH_STDOUT
        ):
            mock_main.side_effect = [ expected ]
            res = prompt_date_operation(uinput)
        mock_main.assert_called_once()
        mock_success.assert_called_once_with(expected.strftime("%a %d %b %Y"))
        self.assertEqual(res, expected)
        _, kwargs = mock_main.call_args
        self.assertEqual(kwargs["prompt"], "Insert date operation: ")
        self.assertIn("parser", kwargs)

    def test_early_exit_date_type(self):
        inputdate = date.today()
        self.assertEqual(inputdate, prompt_date_operation(inputdate))

    def test_not_string_passed(self):
        bad_cases = [print, {}]
        for bad in bad_cases:
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    prompt_date_operation(bad)



class TestCurrencyPrompt(TestCase):
    def test_calls_quiet(self):
        uinput = "usd"
        expected = "USD"
        with (
            patchf(main_loop) as mock_main,
            patchf(success) as mock_success,
            PATCH_STDOUT
        ):
            mock_main.side_effect = [ expected ]
            res = prompt_currency(uinput)
        mock_main.assert_called_once()
        mock_success.assert_not_called()
        self.assertEqual(res, expected)
        _, kwargs = mock_main.call_args
        self.assertEqual(kwargs["prompt"], "Currency in ISO format: ")
        self.assertIn("parser", kwargs)

    def test_calls_not_quiet(self):
        uinput = "usd"
        expected = "USD"
        with (
            patchf(main_loop) as mock_main,
            patchf(success) as mock_success,
            PATCH_STDOUT
        ):
            mock_main.side_effect = [ expected ]
            res = prompt_currency(uinput, False)
        mock_main.assert_called_once()
        mock_success.assert_called_once()
        self.assertEqual(res, expected)
        _, kwargs = mock_main.call_args
        self.assertEqual(kwargs["prompt"], "Currency in ISO format: ")
        self.assertIn("parser", kwargs)

    def test_type_error_on_nonstr(self):
        uinput = print
        with self.assertRaises(TypeError):
            prompt_currency(uinput)
        



class TestDoubleCurrencyPrompt(TestCase):

    def test_calls(self):
        uinput = "=2+1.5 usd"
        expected = (3.5, "USD")
        default = 'EUR'
        lbound = 0.0
        with (
            patchf(main_loop) as mock_main,
            patchf(success) as mock_success,
            PATCH_STDOUT
        ):
            mock_main.side_effect = [ expected ]
            amount, currency = prompt_double_currency(default, uinput, lbound)
        mock_main.assert_called_once()
        mock_success.assert_called_once_with(*expected)
        self.assertEqual((amount, currency), expected)
        _, kwargs = mock_main.call_args
        self.assertEqual(kwargs["prompt"], "Type double-currency operation: ")
        self.assertEqual(kwargs["default_currency"], default)
        self.assertEqual(kwargs["lbound"], lbound)
        self.assertIn("parser", kwargs)
    
    def test_type_error_on_nonstr(self):
        uinput = tuple
        default = "str"
        with self.assertRaises(TypeError):
            prompt_double_currency(default, uinput)



class TestGetFromNestedDict(TestCase):
    
    def test_keybinds_not_nested(self):
        keybinds = { "foo" : "baz", "bar" : "bar" }
        uinput = "foo"
        prompt = "any"
        expected = "baz"
        with (
            PATCH_STDOUT, 
            patch_builtin(input) as mock_input,
            patchf('jprint') as mock_jprint,
            patchf(get_from_nested_dict, wraps=get_from_nested_dict) as mock_self,
        ):
            res = get_from_nested_dict(keybinds, uinput, prompt)
        mock_jprint.assert_not_called()
        mock_input.assert_not_called()
        mock_self.assert_not_called()
        self.assertEqual(res, expected)

    def test_uinput_none_succeeds_first_try_not_nested(self):
        keybinds = { "foo" : "baz", "bar" : "bar" }
        expected = "baz"
        with (patch_builtin(input) as mock_input,
              patchf('jprint') as mock_jprint,):
            mock_input.return_value = "foo"
            res = get_from_nested_dict(keybinds, None, "")
        mock_jprint.assert_called_once_with(keybinds)
        mock_input.assert_called_once_with("")
        self.assertEqual(res, expected)

    def test_succeeds_on_nested_level_1(self):
        keybinds = { 
            "foo" : "baz", 
            "bar" : "bar",
            "key" : { "foo" : "f", "bar" : "b" }
        }
        uinput = "key"
        nested = keybinds[uinput]
        input_return = "bar"
        expected = "b"
        prompt = ""

        with (
            patch_builtin(input) as mock_input, 
            patchf('jprint') as mock_jprint,
            patchf(get_from_nested_dict, wraps=get_from_nested_dict) as mock_self,
        ):
            mock_input.return_value = input_return
            res = get_from_nested_dict(keybinds, uinput, prompt)
        mock_self.assert_called_once_with(nested, None, prompt)
        mock_jprint.assert_called_once_with(nested)
        self.assertEqual(res, expected)

    def test_soft_key_error_and_res_is_none(self):
        keybinds = { }
        uinput = "not-key"
        with patchf(softerror) as mock_soft:
            res = get_from_nested_dict(keybinds, uinput, "")
        mock_soft.assert_called_once()
        self.assertEqual(res, None)

    def test_typeerror_on_nonstr(self):
        keybinds = { "a" : "b" }
        uinput = str
        with self.assertRaises(TypeError):
            get_from_nested_dict(keybinds, uinput, "")



class TestCategoryFromKeybindsPrompt(TestCase):

    prompt = "Type the corresponding key from the dictionary above: "

    def test_uinput_provided_parses_immediately(self):
        keybinds = { "foo" : "f", "bar" : "b", "baz": "b" }
        uinput = "foo"
        expected = keybinds[uinput]
        with (
            patchf(get_from_nested_dict) as mock_getter,
            patchf(success) as mock_success,
        ):
            mock_getter.return_value = expected
            res = prompt_category_from_keybinds(keybinds, uinput)
        mock_getter.assert_called_once_with(keybinds, uinput, self.prompt)
        mock_success.assert_called_once_with(expected)
        self.assertEqual(res, expected)

    def test_uinput_none_succeeds_first_try(self):
        uinput = None
        keybinds = { "foo" : "f", "bar" : "b", "baz": "b" }
        return_val = "bar"
        expected = keybinds[return_val]
        with (
            patchf(get_from_nested_dict) as mock_getter,
            patchf(success) as mock_success,
        ):
            mock_getter.return_value = expected
            res = prompt_category_from_keybinds(keybinds, uinput)
        mock_getter.assert_called_once_with(keybinds, None,  self.prompt)
        mock_success.assert_called_once_with(expected)
        self.assertEqual(res, expected)

    def test_succeeds_on_last_attempt(self):
        uinput = None
        keybinds = { "foo" : "f", "bar" : "b", "baz": "b" }
        max_attempts = 10
        expected = "f"
        nested_returns = [ None ] * (max_attempts - 1) + [expected]
        
        with (
            patchf(get_from_nested_dict) as mock_getter,
            patchf(success) as mock_success,
        ):
            mock_getter.side_effect = nested_returns
            res = prompt_category_from_keybinds(keybinds, uinput, max_attempts)
        mock_success.assert_called_once_with(expected)
        self.assertEqual(res, expected)
        self.assertEqual(max_attempts, mock_getter.call_count)
        
    def test_exhausted_attempts_raises_runtime_error(self):
        max_attempts = 1
        keybinds = { "a" : "b" }
        with (
            patchf(get_from_nested_dict) as mock_getter,
            patchf(success) as mock_success,
        ):
            mock_getter.side_effect = [ None ]
            with self.assertRaises(RuntimeError):
                prompt_category_from_keybinds(keybinds, None, max_attempts)
        mock_success.assert_not_called()
        mock_getter.assert_called_once()