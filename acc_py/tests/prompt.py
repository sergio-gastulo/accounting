import unittest
from unittest import TestCase
from unittest.mock import patch, MagicMock, call
from typing import Callable
from io import StringIO
from datetime import date

from tests._shared import (
    Patcher,
    patch_builtin,
    mem_engine,
    TODAY
)
from pkg.classes.model import Record, Conversion
from pkg.utilities.prompt import (
    main_loop,
    prompt_arithmetic_operation,
    prompt_category_from_keybinds,
    prompt_column_value,
    prompt_currency,
    prompt_date_operation,
    prompt_double_currency,
    prompt_list_of_fields,
    prompt_entity_by_id,
    get_from_nested_dict
)

#region ============================ utils =====================================

TEST_MODULE = 'pkg.utilities.prompt'
_patch_print_buffer = patch('sys.stdout', new_callable=StringIO)


def _patch_this(f: Callable | str, **kwargs) -> Patcher:
    return Patcher(TEST_MODULE, f, **kwargs)


#endregion =====================================================================


@unittest.skip("TODO: add tests to ensurer if sth breaks.")
class TestEnsure(TestCase):
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
            _patch_print_buffer
        ):
            mock_input.side_effect = return_input
            res = main_loop(uinput=None, prompt=icall, parser=int, max_attempts=max_attempts)
        self.assertEqual(res, 5)
        mock_input.assert_has_calls([call(icall)] * max_attempts)

    def test_on_error_called_per_bad_input(self):
        on_error = MagicMock()
        inputs = ["bad", "bad", "3"]
        with ( patch_builtin(input) as mock_input, _patch_print_buffer ):
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
        with ( patch_builtin(input) as mock_input, _patch_print_buffer ):
            mock_input.side_effect = inputs
            main_loop(uinput=None, prompt="any: ", parser=_parser)
        self.assertEqual(call_log, inputs)

    def test_exhausted_attempts_raises_runtime_error(self):
        max_attempts = 3
        icall = "any: "
        return_input = [ "bad" ] * ( max_attempts + 1 ) + [ "5" ]
        with ( patch_builtin(input) as mock_input, _patch_print_buffer ):
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
        with (patch_builtin(input) as mock_input, _patch_print_buffer):
            mock_input.side_effect = ["bad", "good"]
            res = main_loop(uinput=None, prompt="", parser=_parser, on_error=on_error)
        self.assertEqual(res, "GOOD")
        on_error.assert_called_once()

    def test_max_attempts_one_invalid_raises(self):
        max_attempts = 1
        with self.assertRaises(RuntimeError), _patch_print_buffer:
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

    def test_not_string_passed(self):
        bad_cases = [print, {}]
        for bad in bad_cases:
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    prompt_arithmetic_operation(bad)

    def test_calls(self):
        uinput = "+99 - 55"
        expected = 44
        with (
            _patch_this(main_loop) as mock_main,
            _patch_this('_success') as mock_success,
            _patch_print_buffer
        ):
            mock_main.side_effect = [ expected ]
            res = prompt_arithmetic_operation(uinput)
        mock_main.assert_called_once()
        mock_success.assert_called_once()
        self.assertEqual(res, expected)
        _, kwargs = mock_main.call_args
        self.assertEqual(kwargs["prompt"], "Type valid aithmetic operation: ")
        self.assertIn("parser", kwargs)

    def test_lower_bound_is_nonfloat(self):
        lbound = [ "any", print, type]
        for bad in lbound:
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    prompt_arithmetic_operation("any", lbound)


class TestCurrencyPrompt(TestCase):
    def test_calls_quiet(self):
        uinput = "usd"
        expected = "USD"
        with (
            _patch_this(main_loop) as mock_main,
            _patch_this('_success') as mock_success,
            _patch_print_buffer
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
            _patch_this(main_loop) as mock_main,
            _patch_this('_success') as mock_success,
            _patch_print_buffer
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

    def test_ensure_quiet_is_bool(self):
        quiet = print
        with self.assertRaises(TypeError):
            prompt_currency("uinput", quiet)
        

class TestDateOperationPrompt(TestCase):

    def test_calls(self):
        uinput = "0"
        expected = date.today()
        with (
            _patch_this(main_loop) as mock_main,
            _patch_this('_success') as mock_success,
            _patch_print_buffer
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


class TestDoubleCurrencyPrompt(TestCase):

    def test_calls(self):
        uinput = "=2+1.5 usd"
        expected = (3.5, "USD")
        default = 'EUR'
        lbound = 0.0
        with (
            _patch_this(main_loop) as mock_main,
            _patch_this('_success') as mock_success,
            _patch_print_buffer
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

    def test_type_error_on_default_curr(self):
        default = print
        with self.assertRaises(TypeError):
            prompt_double_currency(default, "uinput")
        
    def test_type_error_on_lower_bound(self):
        lbound = "any"
        with self.assertRaises(TypeError):
            prompt_double_currency("str", "uinput", lbound)


class TestFromNestedDictGetter(TestCase):
    
    def test_keybinds_not_nested(self):
        keybinds = { "foo" : "baz", "bar" : "bar" }
        uinput = "foo"
        prompt = "any"
        expected = "baz"
        with (
            _patch_print_buffer, 
            patch_builtin(input) as mock_input,
            _patch_this('jprint') as mock_jprint,
            _patch_this(get_from_nested_dict, wraps=get_from_nested_dict) as mock_self,
        ):
            res = get_from_nested_dict(keybinds, uinput, prompt)
        mock_jprint.assert_not_called()
        mock_input.assert_not_called()
        mock_self.assert_not_called()
        self.assertEqual(res, expected)

    def test_uinput_none_succeeds_first_try_not_nested(self):
        keybinds = { "foo" : "baz", "bar" : "bar" }
        expected = "baz"        
        with (
            patch_builtin(input) as mock_input,
            _patch_this('jprint') as mock_jprint,
        ):
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
            _patch_this('jprint') as mock_jprint,
            _patch_this(get_from_nested_dict, wraps=get_from_nested_dict) as mock_self,
        ):
            mock_input.return_value = input_return
            res = get_from_nested_dict(keybinds, uinput, prompt)
        mock_self.assert_called_once_with(nested, None, prompt)
        mock_jprint.assert_called_once_with(nested)
        self.assertEqual(res, expected)

    def test_soft_key_error_and_res_is_none(self):
        keybinds = { }
        uinput = "not-key"
        with (
            # _patch_print_buffer as mock_print,
            _patch_this('_soft_error') as mock_soft,
        ):
            res = get_from_nested_dict(keybinds, uinput, "")
        mock_soft.assert_called_once()
        self.assertEqual(res, None)

    def test_typeerror_on_nonstr(self):
        keybinds = { "a" : "b" }
        uinput = str
        with self.assertRaises(TypeError):
            get_from_nested_dict(keybinds, uinput, "")

    def test_typeerror_on_dict(self):
        bad_keybinds = [
            { "not", "a", "dict"},
            print,
            "callable",
            Callable
        ]
        uinput = prompt = "pass"
        for badkdict in bad_keybinds:
            with self.subTest(badkdict=badkdict):
                with self.assertRaises(TypeError):
                    get_from_nested_dict(badkdict, uinput, prompt)

    def test_typeerror_on_prompt_nonstr(self):
        prompt = tuple
        kdict = {"a" : "b"}
        uinput = "any"
        with self.assertRaises(TypeError):
            get_from_nested_dict(kdict, uinput, prompt)        


class TestCategoryFromKeybindsPrompt(TestCase):

    prompt = "Type the corresponding key from the dictionary above: "

    def test_uinput_provided_parses_immediately(self):
        keybinds = { "foo" : "f", "bar" : "b", "baz": "b" }
        uinput = "foo"
        expected = keybinds[uinput]
        with (
            _patch_this(get_from_nested_dict) as mock_getter,
            _patch_this('_success') as mock_success,
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
            _patch_this(get_from_nested_dict) as mock_getter,
            _patch_this('_success') as mock_success,
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
            _patch_this(get_from_nested_dict) as mock_getter,
            _patch_this('_success') as mock_success,
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
            _patch_this(get_from_nested_dict) as mock_getter,
            _patch_this('_success') as mock_success,
        ):
            mock_getter.side_effect = [ None ]
            with self.assertRaises(RuntimeError):
                prompt_category_from_keybinds(keybinds, None, max_attempts)
        mock_success.assert_not_called()
        mock_getter.assert_called_once()

    def test_typeerr_on_keybind(self):
        keybinds = [ "not a dict" ]
        with self.assertRaises(TypeError):
            prompt_category_from_keybinds(keybinds, "foo")

    def test_typeerr_on_max_attempts(self):
        max_attempts = [ "not a dict" ]
        with self.assertRaises(TypeError):
            prompt_category_from_keybinds({"a" : "b"}, "foo", max_attempts)

    def test_type_err_on_input(self):
        uinput = [ "not a dict" ]
        with self.assertRaises(TypeError):
            prompt_category_from_keybinds({"a" : "b"}, uinput)


class TestRecordByIDPrompt(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = mem_engine()
        return super().setUpClass()

    def test_str_none_passed_record(self):
        prompt = "Type id to be filtered: "
        record = Record(
            date=TODAY,
            amount=2.4,
            currency="foo",
            description="foo",
            category="foo"
        )
        record.write(self.engine, quiet=True)
        uinputs = [ "1", None, 1]
        for uinput in uinputs:
            with self.subTest(uinput=uinput):
                with (
                    _patch_this(main_loop) as mock_main,
                    _patch_this('_success') as mock_success,
                ):
                    mock_main.return_value = record
                    res = prompt_entity_by_id(self.engine, Record, uinput)
                mock_main.assert_called_once()
                mock_success.assert_called_once_with(record)
                arg, kwargs = mock_main.call_args
                self.assertEqual(arg[0], uinput)
                self.assertIn("parser", kwargs)
                self.assertEqual(prompt, kwargs["prompt"])
                self.assertEqual(self.engine, kwargs["engine"])
                self.assertEqual(res, record)

    def test_str_none_passed_conversion(self):
        prompt = "Type id to be filtered: "
        conv = Conversion(
            date=TODAY,
            base_currency="USD",
            base_amount=1.0,
            target_currency="EUR",
            target_amount=5.0,
            description="foobarbaz"
        )
        conv.write(self.engine, quiet=True)
        uinputs = [ "1", None, 1]
        for uinput in uinputs:
            with self.subTest(uinput=uinput):
                with (
                    _patch_this(main_loop) as mock_main,
                    _patch_this('_success') as mock_success,
                ):
                    mock_main.return_value = conv
                    res = prompt_entity_by_id(self.engine, Conversion, uinput)
                mock_main.assert_called_once()
                mock_success.assert_called_once_with(conv)
                arg, kwargs = mock_main.call_args
                self.assertEqual(arg[0], uinput)
                self.assertIn("parser", kwargs)
                self.assertEqual(prompt, kwargs["prompt"])
                self.assertEqual(self.engine, kwargs["engine"])
                self.assertEqual(res, conv)

    def test_type_err_on_nonstr_id(self):
        id_ = print
        with self.assertRaises(TypeError):
            prompt_entity_by_id(self.engine, Record, id_)

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()
        return super().tearDownClass()


class TestListOfFieldsPrompt(TestCase):

    def test_regular_input(self):
        uinput = "d c cat"
        prompt = "Write valid elements from list: "
        expected_from_parser = ["description", "currency", "category"]
        with (
            _patch_this(main_loop) as mock_main,
            _patch_this('jprint') as mock_jprint,
            _patch_this('_success') as mock_success,
        ):
            mock_main.return_value = expected_from_parser
            res = prompt_list_of_fields(uinput)
        mock_jprint.assert_called_once()
        mock_success.assert_called_once_with(*expected_from_parser)
        arg, kwargs = mock_main.call_args
        self.assertEqual(arg[0], uinput)
        self.assertIn("parser", kwargs)
        self.assertEqual(prompt, kwargs["prompt"])
        self.assertEqual(res, expected_from_parser)

    def test_bad_input(self):
        uinput = "not valid input"
        prompt = "Write valid elements from list: "
        expected_from_parser = ["description", "currency", "category"]
        with (
            _patch_this(main_loop) as mock_main,
            _patch_this('jprint') as mock_jprint,
            _patch_this('_success') as mock_success,
        ):
            mock_main.return_value = expected_from_parser
            res = prompt_list_of_fields(uinput)
        mock_jprint.assert_called_once()
        mock_success.assert_called_once_with(*expected_from_parser)
        arg, kwargs = mock_main.call_args
        self.assertEqual(arg[0], uinput)
        self.assertIn("parser", kwargs)
        self.assertEqual(prompt, kwargs["prompt"])
        self.assertEqual(res, expected_from_parser)

    def test_typeerr(self):
        uinput = aiter
        with self.assertRaises(TypeError):
            prompt_list_of_fields(uinput)



class TestColumnValuePrompt(TestCase):
    def test_simple_routine(self):
        # foobarbaz dictionary
        keybinds = { "a" : "arroz", "b" : "bueno"}
        
        # stands for description, currency
        uinput = "d c"
        res_mocked_prompt_list_fields = [ "description", "currency" ]
        
        # asking which description, which currency
        res_mocked_description = "any description"
        res_mocked_currency = "cur"

        expected = {
            "description" : res_mocked_description,
            "currency" : res_mocked_currency
        }
        with (
            _patch_this(prompt_list_of_fields) as mock_prompt,
            patch_builtin(input) as mock_input,
            _patch_this(prompt_currency) as mock_currency
        ):
            mock_prompt.return_value = res_mocked_prompt_list_fields
            mock_currency.return_value = res_mocked_currency
            mock_input.return_value = res_mocked_description
            res = prompt_column_value(keybinds, uinput)
        mock_prompt.assert_called_once_with(uinput)
        mock_currency.assert_called_once()
        mock_input.assert_called_once()
        self.assertEqual(res, expected)

    def test_type_err_on_input(self):
        keybinds = { "a" : "arroz", "b" : "bueno" }
        badinputs = [ print, aiter, 1.0, {"a" : "b"}]
        for bad in badinputs:
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    prompt_column_value(keybinds, bad)

    def test_type_err_on_keybinds(self):
        badinputs = [ print, aiter, 1.0, "not-dictionary"]
        for bad in badinputs:
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    prompt_column_value(bad, None)



if __name__ == "__main__":
    unittest.main()