from datetime import date
from pandas import Period
import traceback
from json import dumps

from sqlalchemy.engine import Engine

from .core_parser import *
from ..db.model import Record, Session


# convention: prompt_usage ( object_input : str | None )


def prompt_arithmetic_operation(
        user_input : str | float | int |  None = None, 
        lower_bound: float = 0.0, 
        validate_label: str | None = None, 
        explain : bool = True
    ) -> float | int :

    if isinstance(user_input, int) or isinstance(user_input, float):
        return user_input

    validate_sentence = f"Write '{validate_label}': " if validate_label is not None else "Type valid operation: "

    if explain and user_input is None:
        print(
            f"To use this parser, you can type a number or use basic arithmetic.\n"
            f"Example: '=1+1' parses to '2'. Must start with '=', '+', or '-'.\n"
        )

    while True:
        if user_input is None:
            user_input = input(validate_sentence)
        try: 
            value = parse_arithmetic_operation(expr=user_input, lower_bound=lower_bound)
            print(f"Success: '{value}'")
            return value
        except Exception as e:
            print(f"Something went wrong: {e}")
            user_input = None


def prompt_currency(currency_input : str | None = None) -> str:
    
    while True: 
        if currency_input is None:
            currency_input = input("Write your ISO currency -- 3 characters: ")

        try:
            currency = parse_currency(currency=currency_input)
            print(f"Success: '{currency}'")
            return currency
        except Exception as e: 
            print(f"'{currency_input}' could not be parsed: {e}")
            currency_input = None


def prompt_date_operation(
        date_str_input : str | None = None, 
        explain : bool = True
    ) -> date:
    
    if explain and date_str_input is None:
        print(
            f"Enter a particular date in 'day', 'day month', 'year month day' format.\n"
            f"To select basic arithmetic, type '+n' or '-n'. This will operate as follows: today +/- n days.\n"
            f"To select today, just write '0'.\n"
        )

    while True:
        if date_str_input is None:
            date_str_input = input("Insert period or day arithmetic: ")
        try: 
            return_date = parse_date(date_str=date_str_input)
            print(f"Success: {return_date.strftime("%a %d %b %Y")}")
            return return_date
        except Exception as e:
            print(f"'{date_str_input}' could not be parsed: {e}")
            date_str_input = None


def prompt_double_currency(
        double_curr_input : str | None = None, 
        lower_bound : float = 0.0, 
        explain : bool = True
    ) -> tuple[float, str]:
    
    if explain and double_curr_input is None:
        print(
            f"To use this parser, you can do [+|=]operation [usd|eur|pen|...] (empty for default)."
            f"e.g. =9+9 usd -> (18, 'USD')"
        )

    while True: 
        if double_curr_input is None:
            double_curr_input = input("Type your currency operation: ")
        try:
            amount, currency = parse_double_currency(double_currency_str=double_curr_input, lower_bound=lower_bound)
            print(f"Sucess: amount={amount} currency={currency}")
            return amount, currency
        except Exception as e:
            print(f"'{double_curr_input}' could not be parsed as a valid double, currency: {e}")
            double_curr_input = None
        

def prompt_period(period_input : str | None = None) -> Period:

    today_period = Period(date.today() , 'M')

    while True:
        if period_input is None:
            print(
                f"The following formats for period are currently available:\n"
                f"  - yyyy[separator]MM // yy[separator]MM: 2025[separator]08 / 25[separator]08\n"
                f"  - valid separators: '-', '/', ' '\n"
                f"You can also type a single integer for months: e.g. '5' -> Period(year=this_year,month=5).\n"
                f"You can type '0' to use today's period: '{today_period}'.\n"
            )
            period_input = input("Write your string period: ")
        try:
            period = parse_period(period_input, today_period)
            print(f"Success: {period}")
            return period
        except Exception:
            print(f"Could not parse: '{period_input}' as a valid period:\n{traceback.format_exc()}")
            period_input = None


def prompt_category(
        category_dictionary : dict[str, str],
        category_input : str | None = None
) -> str:
    while True:
        if category_input is None:
            print(dumps(category_dictionary))
            category_input = input("Type category (leave empty for random choice): ")
        try: 
            category = parse_category(category_dictionary, category_input)
            print(f"Sucess: {category}")
            return category
        except Exception:
            print(f"Something went wrong: \n{traceback.format_exc()}")


# as this asks for double input depending on the context, 
# there is no call fromkeybind core_parser.py
def prompt_keybind(
        keybind_dict : dict[str, str | dict[str, str]],
        category_input : str | None = None
) -> str:

    while True:
        if category_input is None:
            print(dumps(keybind_dict, indent=4))  # printing entire dict
            category_input = input("Type the corresponding keybind from the dictionary above: ")

        category = keybind_dict.get(category_input)

        if not category:
            print("This is not a valid keybind.")
            category_input = None

        if isinstance(category, dict):
            print(dumps(category, indent=4))
            category_input = input("Your keybind leads to another dict. Select a second keybind: ")
            sub_category = category.get(category_input)
            if sub_category:
                return sub_category
            else:
                print("This is not a valid subcategory.")
                category_input = None

        elif isinstance(category, str):
            return category


def prompt_record_by_id(engine : Engine, id_ : int | None = None) -> Record:
    
    while True:
        if id_ is None:
            id_ = int(input("Type the id to filter: ")) # TODO: validate this in a better way?
        
        with Session(engine) as session:
            record = session.get(Record, id_)
        
        if record is None:
            print(f"Current id '{id_}' doesn't exist in the db.")
            id_ = None
        else:
            print(f"Sucess: {record}")
            return record


