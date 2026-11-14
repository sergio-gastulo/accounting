import datetime
from copy import deepcopy

from sqlalchemy import (String,
                        Date,
                        Numeric,
                        Engine,)
from sqlalchemy.orm import (Mapped,
                            Session,
                            mapped_column,
                            declarative_base,)

from pkg.coreutils.parser.dates import parse_date
from pkg.coreutils.parser.arith_curr import (parse_arithmetic_operation,
                                             parse_currency,)
from pkg.classes.context import ctx


CATEGORIES = list(ctx.categories_dict.keys())
PRINT_ON_WRITE_DEFAULT = False


Base = declarative_base()


class Entity:

    def __eq__(self, other) -> bool:
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

    def validate(self):
        pass

    def write(
            self,
            label: str | None = None,
            quiet: bool = PRINT_ON_WRITE_DEFAULT
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

        if label is None:
            label = "The following record has been added to database:"

        self.validate()  # TODO: test
        with Session(ctx.engine) as session:
            session.add(self)
            session.commit()
            session.refresh(self)
            if not quiet:
                print(label, self, sep="\n")

    def delete(self) -> None:
        """
        Deletes a Record | Conversion directly without asking for commit.
        """
        with Session(ctx.engine) as session:
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

    @staticmethod
    def get():
        pass


class Record(Base, Entity):

    __tablename__ = "cuentas"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(nullable=False)

    def validate(self):
        """Validate each of the fields of `self`."""

        self.date = parse_date(self.date)
        self.amount = parse_arithmetic_operation(self.amount)
        self.currency = parse_currency(self.currency)
        if not isinstance(self.description, str):
            raise ValueError(f"Description '{self.description!r}' "
                            "is not a string.")
        if self.category not in CATEGORIES:
            raise ValueError(f"Category {self.category!r} not "
                            "in `ctx.categories_dict`.")


class Conversion(Base, Entity):

    __tablename__ = "conversions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    base_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    target_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    target_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    description: Mapped[str] = mapped_column(String,nullable=False)

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
    
    def get_rate(self) -> float:
        """base * rate = target"""
        return self.target_amount / self.base_amount

    def validate_conversion(self: Conversion):
        """Validate each of the fields of `conv`."""
        self.date = parse_date(self.date)
        self.base_amount = parse_arithmetic_operation(self.base_amount)
        self.base_currency = parse_arithmetic_operation(self.base_currency)
        self.target_amount = parse_arithmetic_operation(self.target_amount)
        self.target_currency = parse_arithmetic_operation(self.target_currency)
        if not isinstance(self.description, str):
            raise ValueError(f"Description '{self.description!r}' "
                            "is not a string.")



    # TODO: method that swaps base and target and writes to database directly
    def invert(self):
        pass



def create_tables(engine: Engine) -> None:
    Base.metadata.create_all(engine, checkfirst=True)