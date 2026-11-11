from unittest import TestCase

from pkg.coreutils.colors import (convert_rgb,
                                  check_colors,
                                  askcolor)
from tests._shared import Patcher

TEST_MODULE = "pkg.coreutils.colors"
def patch(f):
    return Patcher(TEST_MODULE, f)


class TestRGBConverter(TestCase):
    def test_convert_rgb(self):
        cases = [
            ([255, 255, 255],   (1.0, 1.0, 1.0)),
            ([1.0, 0.0, 0.5],   (1.0, 0.0, 0.5)),
            ((0, 0, 0, 0),      (0, 0, 0, 0)),
            ((1.0, 128, 0, 0),  (1.0, 128 / 255, 0, 0))
        ]
        for color, expected in cases:
            with self.subTest(color=color):
                self.assertEqual(
                    convert_rgb(color), 
                    expected
                )

    def test_convert_rgb_err(self):
        cases = [
            ("foo",                 TypeError),
            ((300, 200, 100, 0),    ValueError),
            ([1.0, 1.1, 1.0, 1.5],  ValueError)
        ]
        for bad_color, err in cases:
            with self.subTest(bad_color=bad_color):
                with self.assertRaises(err):
                    convert_rgb(bad_color)


class TestColorChecker(TestCase):
    def test_check_colors(self):
        currencies = ["per", "eur", "usa"]
        colors = ["red", "blue", [1.0, 0.5, 0.5]]
        expected = {
            "per" : (1.0, 0.0, 0.0),
            "eur" : (0.0, 0.0, 1.0),
            "usa" : (1.0, 0.5, 0.5)
        }
        self.assertEqual(check_colors(currencies, colors), expected)

    def test_check_colors_dimensions_1(self):
        """more colors than currencies"""
        currencies = [ "per" ]
        colors = ["red", "blue", [1.0, 0.5, 0.5]]
        expected = {
            "per" : (1.0, 0.0, 0.0)
        }
        self.assertEqual(check_colors(currencies, colors), expected)

    def test_check_colors_dimensions_2(self):
        """Check that askcolor is called for each missing color."""
        currencies = [ "per", "eur", "usd" ]
        colors = [ "red" ]
        test_color = (0.5, 0.5, 0.5)
        expected = {
            "per" : (1, 0, 0),
            "eur" : test_color,
            "usd" : test_color,
        }
        with patch(askcolor) as mock_ask_color:
            mock_ask_color.return_value = (0.5, 0.5, 0.5), "hex"
            self.assertEqual(check_colors(currencies, colors),
                             expected)
        kwargs = [call.kwargs for call in mock_ask_color.call_args_list]
        for currency, kwarg in zip(["eur", "usd"], kwargs):  # in that order
            with self.subTest(currency=currency, kwarg=kwarg):
                self.assertIn(currency, kwarg["title"])

    def test_check_colors_err(self):
        currencies = [ "per", "eur" ]
        colors = [ "red", "not-a-color" ]
        with self.assertRaises(ValueError):
            check_colors(currencies, colors)

    def test_none_type(self):
        currencies = [ "per", "eur" ]
        colors = [ "red", None ]
        with self.assertRaises(ValueError):
            check_colors(currencies, colors)

