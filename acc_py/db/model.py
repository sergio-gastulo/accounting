import datetime
from sqlalchemy import String, Date, Numeric
from sqlalchemy.orm import Mapped, mapped_column, declarative_base, Session
from sqlalchemy import Engine
from typing import Any
from utilities.core import ensure


Base = declarative_base()


class Mutuals:

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

    def write(self, engine : Engine) -> None:
        """
        General default writer. Checks engine type. Does not ask for commit.
        """
        # --- Important: type(ctx.engine) in Engine works
        # --- but isinstance(ctx.engine, Engine) is false
        # --- ensurer works for this case 
        ensure(engine, Engine)

        # --- write ---
        with Session(engine) as session:
            session.add(self)
            session.commit()
            print("Following record was added to database:")
            self.pprint()


class Record(Mutuals, Base):

    __tablename__ = "cuentas"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[datetime.date] = mapped_column(Date)
    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(3))
    description: Mapped[str] = mapped_column(String,nullable=False)
    category: Mapped[str] = mapped_column(nullable=False)

    def __repr__(self) -> str:
        return (
            f"Record(id={self.id!r}, date={self.date!r}, "
            f"amount={self.amount!r}, currency={self.currency!r}, "
            f"description={self.description!r}, category={self.category!r})"
        )
    
    def __eq__(self, other : Any):
        same_type = isinstance(other, Record)
        if not same_type:
            return False
        return (self.id == other.id)


class Conversion(Mutuals, Base):

    __tablename__ = "conversions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[datetime.date] = mapped_column(Date)
    base_currency: Mapped[str] = mapped_column(String(3))
    base_amount: Mapped[float] = mapped_column(Numeric(10, 2))
    target_currency: Mapped[str] = mapped_column(String(3))
    target_amount: Mapped[float] = mapped_column(Numeric(10, 2))
    description: Mapped[str] = mapped_column(String,nullable=False)

    def __repr__(self) -> str:
        return (
            f"Conversion("
            f"id={self.id!r}"
            f"date={self.date!r},"
            f"base_currency={self.base_currency!r},"
            f"base_amount={self.base_amount!r},"
            f"target_currency={self.target_currency!r},"
            f"target_amount={self.target_amount!r},"
            f"description={self.description!r})"
        )
    
    def pretty(self, inverted : bool = True) -> str:
        """Overridden class prettier to show exchange rate as well."""
        ensure(inverted, bool)
        rate = self.target_amount / self.base_amount
        if inverted:
            rate = 1 / rate
        return (
            f"{self.base_amount:,.2f} {self.base_currency}"
            f" -> {self.target_amount:,.2f} {self.target_currency}"
            f" @ {rate:.4f} {self.base_currency}/{self.target_currency}"
            f"\n         {self.description}"
        )



def create_tables(engine: Engine) -> None:
    Base.metadata.create_all(engine, checkfirst=True)