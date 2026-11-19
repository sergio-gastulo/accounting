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

from pkg.coreutils.prompt import (prompt_arithmetic_operation,
                                  prompt_double_currency,
                                  prompt_currency,
                                  prompt_date_operation,
                                  prompt_category_from_keybinds,)
from pkg.coreutils.colors import fg
from .context import ctx


PRINT_ON_WRITE_DEFAULT = False
MAX_NUMBER_LENGTH = 10
MAX_DECIMAL_LENGTH = 2
CURRENCY_ISO_FORMAT_LENGTH = 3
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
    ) -> int:
        """
        Writes to database without asking for commit.
        """
        self.validate()
        with Session(ctx.engine) as session:
            session.add(self)
            session.commit()
            session.refresh(self)
        return self.id

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

    @classmethod
    def get(cls, id_: int):
        """Get an entity by `id`."""
        if not isinstance(id_, int):
            raise TypeError(f"Argument {id_=!r} is not an integer.")
        with Session(ctx.engine) as session:
            entity = session.get(cls, id_)
        if entity is None:
            raise ValueError(f"Entity with {id_=!r} does not exist.")
        return entity

    def validate_description(self):
        if self.description is None:
            self.description = input("Type your description: ")
        if not isinstance(self.description, str):
            raise TypeError(f"Argument {self.description=!r} is not str.")

    def validate_date(self):
        self.date = prompt_date_operation(self.date)


class Record(Base, Entity):

    __tablename__ = "cuentas"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(MAX_NUMBER_LENGTH, MAX_DECIMAL_LENGTH), nullable=False)
    currency: Mapped[str] = mapped_column(String(CURRENCY_ISO_FORMAT_LENGTH), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(nullable=False)

    def validate_amount_currency(self):
        """Validate amount and currency exclusively."""
        if self.amount is None and self.currency is None:
            self.amount, self.currency = prompt_double_currency(ctx.default_currency,
                                                                None)
        else:
            self.amount = prompt_arithmetic_operation(self.amount)
            self.currency = prompt_currency(self.currency)

    def validate_category(self):
        self.category = prompt_category_from_keybinds(
            ctx.keybinds, self.category
        )

    def validate(self):
        """Validate each of the fields of `self`."""
        self.validate_date()
        self.validate_amount_currency()
        self.validate_description()
        self.validate_category()


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

    def validate_amount_currency(self, *, attr: str = "base"):
        """Validate {attr}_amount and {attr}_currency exclusively."""
        amount = self, f"{attr}_amount"
        currency = self, f"{attr}_currency"

        if getattr(*amount) is None and getattr(*currency) is None:
            print(f"{fg.yellow}Validating '{attr.upper()}' "
                  f"[base->target].{fg.reset}")
            pair = prompt_double_currency(ctx.default_currency, None)
            setattr(*amount, pair[0])
            setattr(*currency, pair[1])
        else:
            setattr(*amount, prompt_arithmetic_operation(getattr(*amount)))
            setattr(*currency, prompt_currency(getattr(*currency)))

    def validate(self):
        """Validate each of the fields of `conv`."""
        self.validate_date()
        self.validate_description()
        self.validate_amount_currency(attr="base")
        self.validate_amount_currency(attr="target")

    def swap(self):
        """Swaps base attrs to target and viceversa."""
        (self.base_amount,
         self.base_currency,
         self.target_amount,
         self.target_currency) = (self.target_amount,
                                  self.target_currency,
                                  self.base_amount,
                                  self.base_currency)


def create_tables(engine: Engine) -> None:
    Base.metadata.create_all(engine, checkfirst=True)