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


def prompt_currency(
        currency_input : str | None = None,
        silent : bool = True
) -> str:
    
    while True: 
        if currency_input is None:
            currency_input = input("Write your ISO currency -- 3 characters: ")

        try:
            currency = parse_currency(currency=currency_input)
            if not silent:
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
        if not date_str_input:
            date_str_input = input("Insert period or day arithmetic: ")
        try: 
            return_date = parse_date(date_str=date_str_input)
            print(f"Success: {return_date.strftime("%a %d %b %Y")}")
            return return_date
        except Exception as e:
            print(f"'{date_str_input}' could not be parsed: {e}")
            date_str_input = None


def prompt_double_currency(
        default_currency : str,
        double_curr_input : str | None = None, 
        lower_bound : float = 0.0, 
        explain : bool = True
    ) -> tuple[float, str]:
    
    if explain and not double_curr_input:
        print(
            f"To use this parser, you can do [+|=]operation [usd|eur|pen|...] (empty for default)."
            f"e.g. =9+9 usd -> (18, 'USD')"
        )

    while True: 
        if not double_curr_input:
            double_curr_input = input("Type your currency operation: ")
        try:
            amount, currency = parse_double_currency(
                default_currency, 
                double_curr_input, 
                lower_bound)
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


# as this asks for double input depending on the context, 
# there is no call fromkeybind core_parser.py
def prompt_category_from_keybinds(
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
            print(
                f"Record available:\n"
                f"{record.pretty()}"
            )
            return record


# ------------------------------------------------------
# The following function aims to cover the following
# possibilities
# string_of_ints (e.g. "1 2 3 4 5" -> column[1], column[2], ...)
# [categories] (e.g. ['amount', 'description']) // prolly never gonna happen
# string_with_spaces_initial_of_categories
#    e.g. "am des cu" -> [amount, description, currency]
# string_with_spaces_full_column
#    e.g. "amount description" -> [amount, description]
# ------------------------------------------------------
def prompt_list_of_fields(
        user_input : str | None = None,
        explain : bool = True
) -> List[str]:
    
    list_to_validate = ['date', 'amount', 'currency', 'description', 'category']
    keybind_dict = dict(zip(['d', 'a', 'c', 'desc', 'cat'], list_to_validate))

    if explain:
        print(
            f"Given the following list: \n"
            f"{list_to_validate}\n"
            f"You can whether type an elemnt or a corresponding keybind:\n"
            f"{dumps(keybind_dict, indent=4)}\n"
            f"e.g. 'd c cat' will be parsed to ['date', 'currency', 'category']"
        )

    # tries to convert to int
    # if it fails, returns str
    def mapper(i : str) -> int | str:
        try:
            return int(i)
        except ValueError:
            return i

    while True:
        if not user_input:
            user_input = input("Write valid elements from list: ")
        try:
            return [
                parse_valid_element_list(
                    column_input=mapper(column), 
                    list_to_validate=list_to_validate, 
                    keybinds=keybind_dict
                ) 
                for column in user_input.split()
            ]
            
        except:
            print(f"'{user_input}' could not be parsed: {traceback.format_exc()}")
            user_input = None



# ------------------------------------------------
# This function aims to return a dictionary:
# {
#     field1: value1,
#     field2: value2,
#     ...
# }
# That will be later converted into a valid Record
# e.g.
# [fields] = prompt_list_of_fields()
# dict = {}
# for field in fields: 
#     dict.update( { field : validate(field) } )
# ------------------------------------------------

def prompt_column_value(
        keybind_dict : dict[str, str],
        fields_str : str | None = None
) -> dict[str, str | int]:
    
    field_func : dict[str, callable] = {
        "date" : prompt_date_operation,
        "amount" : prompt_arithmetic_operation,
        "currency": prompt_currency,
        "description": lambda : input("Type your new description: "),
        "category": lambda : prompt_category_from_keybinds(keybind_dict)
    }

    list_fields = prompt_list_of_fields(fields_str)
    
    res : dict[str, str | int] = {}

    for field in list_fields:
        print(f"\nValidating: {field}\n")
        val = field_func[field]()
        res.update( { field : val } )
    
    return res