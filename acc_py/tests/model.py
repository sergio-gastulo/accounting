import unittest
from unittest import TestCase
from unittest.mock import patch, MagicMock, call
from typing import Callable

from db.model import (
    Entity, 
    Record, 
    Conversion,
    Session,
    ensure,
    soft_warning,
)
from tests._shared import (
    Patcher,
    TODAY,
    patch_builtin,
    session_mocker
)

#region ============================ header ====================================

TEST_MODULE = 'db.model'
def _patch_this(f: Callable | str, **kwargs) -> Patcher:
    return Patcher(TEST_MODULE, f, **kwargs)

#endregion =====================================================================



class TestEntity(TestCase):
    
    class MockedEntity(Entity):
        def __init__(self, value : int):
            super().__init__()
            self.id = value
            keys_mock = MagicMock(return_value=["id"])
            self.__table__ = MagicMock(columns=MagicMock(keys=keys_mock))

    def test_equality(self):
        e1 = Entity()
        e2 = Entity()
        e1.id = e2.id = "foo"
        self.assertTrue(e1 == e2)

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

    def test_pretty_printer(self):
        e = self.MockedEntity(5)
        res = e.pretty()
        self.assertIn("MockedEntity", res)
        self.assertIn("5", res)

    @unittest.skip("Do we really need to test this...?")
    def test_print(self):
        pass

    def test_write_flow(self):
        label = "test"
        quiet = False
        session = session_mocker()
        e = self.MockedEntity(23)
        with (
            patch_builtin(print) as mock_print,
            _patch_this(Session, return_value=session),
            _patch_this(ensure)
        ):
            e.write(MagicMock(), label, quiet)
        madd : MagicMock = session.add
        madd.assert_called_once_with(e)
        mcommit : MagicMock = session.commit
        mcommit.assert_called_once()
        mrefresh : MagicMock = session.refresh
        mrefresh.assert_called_once_with(e)
        mock_print.assert_has_calls([call(label), call(e.pretty())])


    def test_delete_flow(self):
        e = self.MockedEntity(20)
        engine = MagicMock()
        session = session_mocker()
        with (
            _patch_this(ensure),
            _patch_this(Session, return_value=session),
            _patch_this(soft_warning) as mock_soft
        ):
            e.delete(engine)
        mcommit : MagicMock = session.commit
        mcommit.assert_called_once()
        mdelete : MagicMock = session.delete
        mdelete.assert_called_once_with(e)
        warningmsg, = mock_soft.call_args.args
        self.assertIn("Warning: ", warningmsg)

    def test_duplicate_flow(self):
        e = Entity()
        e.id = 5
        e.foo = 4
        new = e.duplicate()
        self.assertEqual(new.foo, e.foo)
        self.assertTrue(new.id is None)


class TestRecord(TestCase):

    def test_table_name(self):
        record = Record(TODAY, 5, "foo", "foo", "foo")
        self.assertEqual("cuentas", record.__tablename__)

    def test_repr(self):
        record = Record(TODAY, 5, "foobarbaz", "foobarbaz", "foobarbaz")
        _repr = repr(record)
        expected_strs = ["5", "foobarbaz", "(", ")", "Record"]
        for expected in expected_strs:
            with self.subTest(expected=expected):
                self.assertIn(expected, _repr)



class TestConversion(TestCase):

    def test_table_name(self):
        conv = Conversion(TODAY, 5, "USD", 6, "EUR", "any-desc")
        self.assertEqual("conversions", conv.__tablename__)

    def test_repr(self):
        conv = Conversion(TODAY, 5, "USD", 6, "EUR", "any-desc")
        


if __name__ == "__main__":
    unittest.main()