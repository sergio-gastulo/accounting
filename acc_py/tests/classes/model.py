from unittest import TestCase, skip
from unittest.mock import MagicMock
from typing import Callable

from sqlalchemy.orm import Session

from pkg.classes.model import (Entity,
                               Record,
                               Conversion,)
from pkg.coreutils.prompt import (prompt_date_operation,
                                  prompt_arithmetic_operation,
                                  prompt_currency,
                                  prompt_double_currency,
                                  prompt_category_from_keybinds,)
from pkg.classes.context import ctx
from tests._shared import (Patcher,
                           TODAY,
                           patch_builtin,
                           session_mocker,
                           mem_engine,)

#region ============================ header ====================================

TEST_MODULE = 'pkg.classes.model'
def patch(f: Callable | str, **kwargs) -> Patcher:
    return Patcher(TEST_MODULE, f, **kwargs)

#endregion =====================================================================


class MockedEntity(Entity):
    def __init__(self, **kwargs):
        super().__init__()
        for attr, value in kwargs.items():
            setattr(self, attr, value)
        keys_mock = MagicMock(return_value=list(kwargs))
        self.__table__ = MagicMock(columns=MagicMock(keys=keys_mock))


class TestEntity(TestCase):


    def test_equality(self):
        e1 = e2 = MockedEntity(id=2)
        self.assertTrue(e1 == e2)

    def test_larger_equality(self):
        kwargs = {"id": "foo", 
                  "bar": "foo", 
                  "different": "hold",}
        e1 = MockedEntity(**kwargs)
        e2 = MockedEntity(**kwargs)
        e1.different = "foo"
        self.assertFalse(e1 == e2)

    def test_equality_different_types(self):
        e = Entity()
        entities = [
            "not-valid",
            callable,
            67,
            None
        ]
        for entity in entities:
            with self.subTest(entity=entity):
                self.assertFalse(e == entity)

    def test_repr(self):
        e = MockedEntity(id=5)
        res = repr(e)
        self.assertIn("MockedEntity", res)
        self.assertIn("5", res)

    def test_write_flow(self):
        """Test that `Session` calls `self.validate`, `session.add`, 
        `session.commit`, and `session.refresh` exactly once, and the
        return value."""

        session = session_mocker()
        id_ = 1
        e = MockedEntity(id=id_)
        e.validate = MagicMock(return_value=None)
        with patch(Session, return_value=session):
            res = e.write()
        e.validate.assert_called_once()
        e_add: MagicMock = session.add
        e_add.assert_called_once_with(e)
        e_commit: MagicMock = session.commit
        e_commit.assert_called_once()
        e_refresh: MagicMock = session.refresh
        e_refresh.assert_called_once_with(e)
        self.assertEqual(id_, res)
        

    def test_delete_flow(self):
        """Test that `Session` calls `session.commit` and `session.delete` 
        exactly once."""
        e = MockedEntity(id=20)
        session = session_mocker()
        with patch(Session, return_value=session):
            e.delete()
        mdelete: MagicMock = session.delete
        mdelete.assert_called_once_with(e)
        mcommit: MagicMock = session.commit
        mcommit.assert_called_once()


    def test_duplicate_flow(self):
        """Check that id is not returned on new object copy."""
        e = Entity()
        e.id = 5
        e.foo = "foo"
        new = e.duplicate()
        self.assertEqual(new.foo, e.foo)
        self.assertTrue(new.id is None)

    def test_validate_description(self):
        """Assert that no error ir raised and input is not called."""
        e = MockedEntity(description="foo")
        with patch_builtin(input) as mockinput:
            e.validate_description()
        mockinput.assert_not_called()

    def test_validate_description_typeerror(self):
        e = MockedEntity(description=print)
        with self.assertRaises(TypeError):
            e.validate_description()

    def test_validate_description_callsinput(self):
        e = MockedEntity(description=None)
        expected = "any"
        with patch_builtin(input, return_value=expected) as mockinput:
            e.validate_description()
        args, _ = mockinput.call_args
        self.assertIn("Type ", args[0])
        self.assertEqual(e.description, expected)

    def test_validate_date(self):
        data = [None, TODAY]
        for date in data:
            with self.subTest(date=date):
                e = MockedEntity(date=date)
                with patch(prompt_date_operation) as mockdate:
                    e.validate_date()
                mockdate.assert_called_once_with(date)


class TestGetClassMethod(TestCase):

    def test_get_on_record(self):
        rec = Record(date=TODAY,
                     amount=4,
                     currency="foo",
                     description="bar",
                     category="baz")
        ctx.engine = mem_engine()
        rec.validate = MagicMock()
        id_ = rec.write()
        newrec = Record.get(id_)
        self.assertEqual(newrec, rec)

    def test_get_on_conversion(self):
        conv = Conversion(date=TODAY,
                          base_currency="USD",
                          base_amount=1.0,
                          target_currency="EUR",
                          target_amount=5.0,
                          description="foobarbaz")
        ctx.engine = mem_engine()
        conv.validate = MagicMock()
        id_ = conv.write()
        newconv = Conversion.get(id_)
        self.assertEqual(newconv, conv)


    def test_doesnt_exist(self):
        ctx.engine = mem_engine()
        for cls in [Record, Conversion]:
            with self.subTest(cls=cls):            
                with self.assertRaises(ValueError):
                    Record.get(999)

    def test_typecheck(self):
        ctx.engine = mem_engine()
        for cls in [Record, Conversion]:
            with self.subTest(cls=cls):            
                with self.assertRaises(TypeError):
                    Record.get(print)



class TestRecord(TestCase):

    fooargs = {
        "date": TODAY,
        "amount": 5,
        "description": "foo",
        "currency": "bar",
        "category": "baz",
    }

    def test_repr(self):
        record = Record(**self.fooargs)
        repr_ = repr(record)
        expected_strs = ["5", "foo", "bar", "(", ")", "Record"]
        for expected in expected_strs:
            with self.subTest(expected=expected):
                self.assertIn(expected, repr_)

    def test_noid(self):
        record = Record(**self.fooargs)
        self.assertIsNone(record.id)

    def test_hasid_on_write(self):
        ctx.engine = mem_engine()
        record = Record(**self.fooargs)
        record.validate = MagicMock()
        expectedid = 1
        id_ = record.write()
        for testid in [expectedid, record.id]:
            with self.subTest(testid=testid):
                self.assertEqual(testid, id_)

    def test_validate_amountcurrency(self):
        """Test basic if-else branching."""
        rec = Record(amount=4, currency="USD")
        with (patch(prompt_double_currency) as mock_arith_curr,
              patch(prompt_arithmetic_operation,
                    return_value=rec.amount) as mockarith,
              patch(prompt_currency,
                    return_value=rec.currency) as mockcurr):
            rec.validate_amount_currency()
        mock_arith_curr.assert_not_called()
        mockarith.assert_called_once_with(rec.amount)
        mockcurr.assert_called_once_with(rec.currency)

    def test_validate_amountcurrency_both_missing(self):
        rec = Record()
        amount = 1
        currency = "USD"
        ctx.default_currency = "USD"
        with (patch(prompt_double_currency,
                    return_value=(amount, currency)) as mock_arith_curr,
              patch(prompt_arithmetic_operation,
                    return_value=amount) as mockarith,
              patch(prompt_currency,
                    return_value=currency) as mockcurr):
            rec.validate_amount_currency()
        mock_arith_curr.assert_called_once_with(ctx.default_currency, None)
        mockarith.assert_not_called()
        mockcurr.assert_not_called()
        self.assertEqual(rec.amount, amount)
        self.assertEqual(rec.currency, currency)

    def test_validate_category(self):
        rec = Record()
        returnval = "FOOBARBAZ"
        ctx.keybinds = {"bar": "baz"}
        with patch(prompt_category_from_keybinds,
                   return_value=returnval) as mockprompt:
            rec.validate_category()
        mockprompt.assert_called_once_with(ctx.keybinds, None)
        self.assertEqual(rec.category, returnval)


    @skip(reason="Is it really necessary?")
    def test_validate_noargs(self):
        pass


class TestConversion(TestCase):

    fooargs = {
        "date": TODAY,
        "base_currency": "usd",
        "base_amount": 55,
        "target_currency": "eur",
        "target_amount": 50,
        "description": "foobarbaz"
    }

    def test_format(self):
        conv = Conversion(**self.fooargs)
        formated = f"{conv}"
        expected_strs = [
            "eur/usd",
            "----",
            "50.",
            "55.",
            "foobarbaz",
        ]
        for expected in expected_strs:
            with self.subTest(expected=expected):
                self.assertIn(expected, formated)

    def test_format_inverted(self):
        conv = Conversion(**self.fooargs)
        formated = f"{conv:i}"
        expected_strs = ["usd/eur"]
        for expected in expected_strs:
            with self.subTest(expected=expected):
                self.assertIn(expected, formated)

    def test_noid(self):
        conv = Conversion(**self.fooargs)
        self.assertIsNone(conv.id)

    def test_hasid_on_write(self):
        ctx.engine = mem_engine()
        conv = Conversion(**self.fooargs)
        expectedid = 1
        convid = conv.write()
        self.assertEqual(expectedid, convid)
        self.assertEqual(expectedid, conv.id)

    def test_get_rate(self):
        conv = Conversion(**self.fooargs)
        self.assertEqual(50 / 55, conv.get_rate())

    def test_validate_amount_currency(self):
        conv = Conversion(**self.fooargs)
        with (patch(prompt_double_currency) as mockarithcurr,
              patch(prompt_arithmetic_operation,
                    return_value=conv.base_amount) as mockarith,
              patch(prompt_currency,
                    return_value=conv.base_currency) as mockcurr,
              patch_builtin(print) as mockprint):
            conv.validate_amount_currency(attr="base")
        mockarithcurr.assert_not_called()
        mockarith.assert_called_once_with(conv.base_amount)
        mockcurr.assert_called_once_with(conv.base_currency)
        mockprint.assert_not_called()

    def test_validate_amount_currency_noargs(self):
        conv = Conversion(**self.fooargs)
        amount, conv.target_amount = conv.target_amount, None
        currency, conv.target_currency = conv.target_currency, None
        ctx.default_currency = "USD"
        with (patch(prompt_double_currency,
                    return_value=(amount, currency)) as mockarithcurr,
              patch(prompt_arithmetic_operation) as mockarith,
              patch(prompt_currency) as mockcurr,
              patch_builtin(print) as mockprint):
            conv.validate_amount_currency(attr="target")
        mockarithcurr.assert_called_once_with(ctx.default_currency, None)
        mockarith.assert_not_called()
        mockcurr.assert_not_called()
        args, _ = mockprint.call_args
        self.assertIn("base->target", args[0])
        self.assertEqual(conv.target_amount, amount)

    def test_swap(self):
        conv = Conversion(**self.fooargs)
        conv.swap()
        self.assertEqual("eur", conv.base_currency)
        self.assertEqual("usd", conv.target_currency)