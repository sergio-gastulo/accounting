import unittest
from unittest import TestCase
from unittest.mock import MagicMock
from typing import Callable

from pkg.classes.model import (Entity,
                               Record,
                               Conversion,
                               Session,)
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



class TestEntity(TestCase):

    class MockedEntity(Entity):
        def __init__(self, **kwargs):
            super().__init__()
            for attr, value in kwargs.items():
                setattr(self, attr, value)
            keys_mock = MagicMock(return_value=list(kwargs))
            self.__table__ = MagicMock(columns=MagicMock(keys=keys_mock))

    def test_equality(self):
        e1 = e2 = self.MockedEntity(id=2)
        self.assertTrue(e1 == e2)

    def test_larger_equality(self):
        kwargs = {"id": "foo", 
                  "bar": "foo", 
                  "different": "hold",}
        e1 = self.MockedEntity(**kwargs)
        e2 = self.MockedEntity(**kwargs)
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
        e = self.MockedEntity(id=5)
        res = repr(e)
        self.assertIn("MockedEntity", res)
        self.assertIn("5", res)

    def test_write_flow(self):
        """Test that `Session` calls `session.add`, `session.commit`, 
        and `session.refresh` exactly once."""
        label = "test"
        quiet = False
        session = session_mocker()
        e = self.MockedEntity(id=23)
        with (patch_builtin(print),
              patch(Session, return_value=session)):
            e.write(MagicMock(), label, quiet)

        madd: MagicMock = session.add
        madd.assert_called_once_with(e)
        mcommit: MagicMock = session.commit
        mcommit.assert_called_once()
        mrefresh: MagicMock = session.refresh
        mrefresh.assert_called_once_with(e)
        

    def test_delete_flow(self):
        """Test that `Session` calls `session.commit` and `session.delete` 
        exactly once."""
        e = self.MockedEntity(id=20)
        engine = MagicMock()
        session = session_mocker()
        with patch(Session, return_value=session):
            e.delete(engine)
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


class TestRecord(TestCase):

    fooargs = {
        "date": TODAY,
        "amount": 5,
        "description": "foo",
        "currency": "bar",
        "category": "baz",
    }

    def test_table_name(self):
        record = Record(**self.fooargs)
        tablename = "cuentas"
        self.assertEqual(tablename, record.__tablename__)

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
        engine = mem_engine()
        record = Record(**self.fooargs)
        expectedid = 1
        with patch_builtin(print):  # NOTE: necessary?
            record.write(engine)
        self.assertEqual(expectedid, record.id)


class TestConversion(TestCase):

    fooargs = {
        "date": TODAY,
        "base_currency": "usd",
        "base_amount": 55,
        "target_currency": "eur",
        "target_amount": 50,
        "description": "foobarbaz"
    }

    def test_table_name(self):
        conv = Conversion(**self.fooargs)
        tablename = "conversions"
        self.assertEqual(tablename, conv.__tablename__)

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
        expected_strs = ["usd/eur", ]
        for expected in expected_strs:
            with self.subTest(expected=expected):
                self.assertIn(expected, formated)

    def test_noid(self):
        conv = Conversion(**self.fooargs)
        self.assertIsNone(conv.id)

    def test_hasid_on_write(self):
        engine = mem_engine()
        conv = Conversion(**self.fooargs)
        expectedid = 1
        with patch_builtin(print):
            conv.write(engine)
        self.assertEqual(expectedid, conv.id)


if __name__ == "__main__":
    unittest.main()