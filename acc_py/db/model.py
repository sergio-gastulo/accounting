from typing import Any, Optional
import datetime
from copy import deepcopy

from sqlalchemy import String, Date, Numeric
from sqlalchemy.orm import Mapped, mapped_column, declarative_base, Session
from sqlalchemy import Engine

from utilities.core import ensure, soft_warning


Base = declarative_base()


class Entity:

    def __eq__(self, other : Any):
        same_type = isinstance(other, type(self))
        if not same_type:
            return False
        return (self.id == other.id)


    # TODO: check if this is basically just a repr and should be renamed
    def pretty(self) -> str:
        """Default class prettier. Returns all attributes with indentation."""
        cols = self.__table__.columns.keys()
        values = {col: getattr(self, col) for col in cols}
        attrs = "\n".join(f"  {k}={v}" for k, v in values.items())
        self_type = type(self).__name__
        wrap = f"{self_type}(\n{attrs}\n)" 
        return wrap

    def pprint(self) -> None:
        """Default pretty printer, prints self.pretty()"""
        print(self.pretty())

    def write(
            self, 
            engine : Engine, 
            label : Optional[str] = None,
            quiet : bool = False
    ) -> None:
        """
        Writes to database without asking for commit. 
        Checks `engine`, `label` and `quiet` type. 
        
        Arguments
        ---------
        `engine`
            sqlalchemy.Engine object to generate a session from to write Record 
            | Conversion to. Does not perform any other assumption.
        `label`
            Simple label that is passed to print before showing entity's pretty
            str
        `quiet`
            Controls if both label and entity.pretty() are printed to sys.stdout.
            Defaults to False (yes, print, please!)
        """
        # --- Important: type(ctx.engine) in Engine works
        # --- but isinstance(ctx.engine, Engine) is false
        # --- ensurer works for this case 
        ensure(engine, Engine)
        ensure(label, str, allow_none=True)
        ensure(quiet, bool)

        if label is None:
            label = "The following record has been added to database:"
        # --- write ---
        with Session(engine) as session:
            session.add(self)
            session.commit()
            session.refresh(self)
            if not quiet:
                print(label)
                self.pprint()

    def delete(self, engine : Engine) -> None:
        """
        Deletes a Record | Conversion directly without asking for commit. 
        Prints soft_warning message before deleting.
        """
        ensure(engine, Engine)
        soft_warning("Warning: you may lose data permanently.")
        with Session(engine) as session:
            session.delete(self)
            session.commit()

    def duplicate(self):
        """
        Returns a copy of `self`, removing id to prevent from overwriting data
        to database if accidentally written to it.
        """
        new = deepcopy(self)
        new.id = None
        return new


class Record(Entity, Base):

    __tablename__ = "cuentas"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(nullable=False)

    def __repr__(self) -> str:
        return (
            f"Record(id={self.id!r}, date={self.date!r}, "
            f"amount={self.amount!r}, currency={self.currency!r}, "
            f"description={self.description!r}, category={self.category!r})"
        )


class Conversion(Entity, Base):

    __tablename__ = "conversions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    base_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    target_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    target_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    description: Mapped[str] = mapped_column(String,nullable=False)

    def __repr__(self) -> str:
        return (
            f"Conversion("
            f"id={self.id!r}, "
            f"date={self.date!r}, "
            f"base_currency={self.base_currency!r}, "
            f"base_amount={self.base_amount!r}, "
            f"target_currency={self.target_currency!r}, "
            f"target_amount={self.target_amount!r}, "
            f"description={self.description!r})"
        )
    
    def pretty(self, inverted : bool = True) -> str:
        """Overwritten class prettier to show exchange rate as well."""
        ensure(inverted, bool)
        rate = self.target_amount / self.base_amount
        if inverted:
            rate = 1 / rate
        return (
            f"{self.id}: {self.base_amount:,.2f} {self.base_currency}"
            f" -> {self.target_amount:,.2f} {self.target_currency}"
            f" @ {rate:.4f} {self.base_currency}/{self.target_currency}"
            f"\n         {self.description}"
        )


def create_tables(engine: Engine) -> None:
    Base.metadata.create_all(engine, checkfirst=True)