import datetime
from sqlalchemy import String, Date, Numeric, MetaData
from sqlalchemy.orm import Mapped, mapped_column, declarative_base, Session
from ..context.context import ctx


Base = declarative_base()


class Record(Base):

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

    def pretty(self) -> str:
        return (
            f"Record(\n"
            f"\tid={self.id!r},\n"
            f"\tdate={self.date!r},\n"
            f"\tamount={self.amount!r},\n"
            f"\tcurrency={self.currency!r},\n"
            f"\tdescription={self.description!r},\n"
            f"\tcategory={self.category!r}\n)"
        )

    def pprint(self) -> None:
        print(self.pretty())


class Conversion(Base):

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
    
    def pretty(self) -> str:
        exchange : float = self.base_amount / self.target_amount
        return (
            f"conv_{self.id}: {self.base_amount} {self.base_currency} "
            f"->(x{exchange:.2f}) {self.target_amount} {self.target_currency}"
            f"\ndescription: {self.description!r}"
        )
    
    def pprint(self) -> None:
        print(self.pretty())



def create_tables() -> None:
    Base.metadata.create_all(ctx.engine, checkfirst=True)