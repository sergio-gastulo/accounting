from typing import Any, Optional
import datetime
from copy import deepcopy

from sqlalchemy import (
    String, Date, Numeric, Engine
)
from sqlalchemy.orm import (
    Mapped, Session,
    mapped_column, declarative_base,
)

from pkg.utilities.core import ensure, soft_warning


Base = declarative_base()


class Entity:

    def __eq__(self, other: Any) -> bool:
        if not isinstance(self, type(other)):
            return False
        cols = self.__table__.columns.keys()
        for attr in cols:
            if not (hasattr(other, attr) and 
                    getattr(self, attr) == getattr(other, attr)):
                return False
        return True


    def __repr__(self) -> str:
        cols = self.__table__.columns.keys()
        values = {col: getattr(self, col) for col in cols}
        attrs = "\n".join(f"  {k}={v}" for k, v in values.items())
        self_type = type(self).__name__
        wrap = f"{self_type}(\n{attrs}\n)" 
        return wrap

    def write(
            self, 
            engine: Engine, 
            label: Optional[str] = None,
            quiet: bool = False
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
            Controls if both label and `entity` are printed to sys.stdout.
            Defaults to False (yes, print, please!)
        """
        # Important: type(ctx.engine) in Engine works
        # but isinstance(ctx.engine, Engine) is false
        # ensurer works for this case 
        ensure(engine, Engine)
        ensure(label, str, allow_none=True)
        ensure(quiet, bool)

        if label is None:
            label = "The following record has been added to database:"
        
        with Session(engine) as session:
            session.add(self)
            session.commit()
            session.refresh(self)
            if not quiet:
                print(label, self, sep="\n")

    def delete(self, engine: Engine) -> None:
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


class Record(Base, Entity):

    __tablename__ = "cuentas"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(nullable=False)



class Conversion(Base, Entity):

    __tablename__ = "conversions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    base_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    target_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    target_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    description: Mapped[str] = mapped_column(String,nullable=False)


    def get_rate(self) -> float:
        """base * rate = target"""
        return self.target_amount / self.base_amount


    def __format__(self, opt: str) -> str:
        
        rate = self.get_rate()
        if opt in ["inverted", "inv", "i"]:
            rate = 1 / rate
            rateop = f"{self.base_currency}/{self.target_currency}"
        else:
            rateop = f"{self.target_currency}/{self.base_currency}"

        idstr = f"{self.id:4}" if self.id else "----"
        return  f"{idstr}: {self.base_amount:,.2f} {self.base_currency}" \
                f" -> {self.target_amount:,.2f} {self.target_currency}" \
                f" @ {rate:.4f} {rateop}" \
                f"\n         {self.description}"


    def __repr__(self) -> str:
        return f"{self:i}"


    # TODO: method that swaps base and target and writes to database directly
    def invert(self):
        pass




def create_tables(engine: Engine) -> None:
    Base.metadata.create_all(engine, checkfirst=True)