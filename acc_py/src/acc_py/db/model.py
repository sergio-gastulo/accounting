import datetime
from sqlalchemy import String, Date, Numeric
from sqlalchemy.orm import Mapped, mapped_column, declarative_base, Session


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