from decimal import Decimal
import datetime
from sqlalchemy import String, Date, Numeric, create_engine
from sqlalchemy.orm import Mapped, mapped_column, declarative_base, sessionmaker
from ..context.context import ctx
from sqlalchemy.engine import Dialect

Base = declarative_base()
engine = None

def init_engine() -> Dialect:
    global engine
    engine = create_engine(f"sqlite:///{ctx.db_path}", echo=True)
    return engine


class Record(Base):

    __tablename__ = "cuentas"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[datetime.date] = mapped_column(Date)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2, asdecimal=True))
    currency: Mapped[str] = mapped_column(String(3))
    description: Mapped[str] = mapped_column(String,nullable=False)
    category: Mapped[str] = mapped_column(nullable=False)

    def __repr__(self) -> str:
        return f"Record(id={self.id!r}, date={self.date!r}, amount={self.amount!r}, currency={self.currency!r}, description={self.description!r}, category={self.category!r})"
    
