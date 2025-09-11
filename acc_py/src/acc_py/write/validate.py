import re
from datetime import date, timedelta
from datetime import datetime as dt


def validate_arithmetic_operation(
        user_input : str | None = None, 
        lower_bound: float = 0.0, 
        validate_label: str | None = None, 
        explain : bool = True
    ) -> float:

    validate_sentence = f"Write '{validate_label}': " if validate_label is not None else "Type valid operation: "

    if explain and user_input is None:
        print(
            f"To use this parser, you can type a number or use basic arithmetic.\n"
            f"Example: '=1+1' parses to '2'. Must start with '=', '+', or '-'.\n"
        )

    def core(string : str) -> float:
        if string[0] in ['+', '=']:
            print("Parsing double operation.")
            if re.match(r'\w', string):
                raise SyntaxError(f"Input can't contain words. Got: '{string}'")
            else:
                value = eval(string[1:], {"__builtins__": {}}) # removing '+', '=' from the beginning of the str
        else:
            print(f"Input '{string}' does not match an arithmetic operation. Will assume double.")
            value = float(string)

        if value < lower_bound:
            raise ValueError(f"'{value}' must be >= '{lower_bound}'")

        return value

    while True:
        if user_input is None:
            user_input = input(validate_sentence)
        try: 
            value = core(string=user_input)
            print(f"Success: '{value}'")
            return value
        except Exception as e:
            print(f"Something went wrong: {e}")
            user_input = None


def validate_currency(currency_input : str | None = None) -> str:

    def core(currency : str) -> str:
        if re.match(r'^[a-zA-Z]{3}$', string=currency):
            return currency.upper()
        else:
            raise ValueError(f"'{currency}' is not a valid currency.")
    
    while True: 
        if currency_input is None:
            currency_input = input("Write your ISO currency -- 3 characters: ")

        try:
            currency = core(currency=currency_input)
            print(f"Success: '{currency}'")
            return currency
        except Exception as e: 
            print(f"'{currency_input}' could not be parsed: {e}")
            currency_input = None


def validate_date_operation(
        date_str_input : str | None = None, 
        explain : bool = True
    ) -> date:
    
    today = date.today()
    
    if explain and date_str_input is None:
        print(
            f"Enter a particular date in 'day', 'day month', 'year month day' format.\n"
            f"To select basic arithmetic, type '+n' or '-n'. This will operate as follows: today +/- n days.\n"
            f"To select today, just write '0'.\n"
        )

    def core(string : str) -> date:

        string = string.strip()

        if string == '0':
            return today
        
        elif re.match(r'^[+-]\d{1,}$', string):
            print("Basic day-arithmetic chosen.")
            return today + timedelta(days=int(string))
        
        elif re.match(r'^\d{1,2}$', string):
            print("current year - current month - day")
            return today.replace(day=int(string)) 
        
        elif re.match(r'^\d{1,2} \d{1,2}$', string):
            print("current year - month - day")
            day, month = map(int, string.split())
            return today.replace(day=day, month=month) 
        
        for fmt in ("%Y %m %d", "%y %m %d"):
            try:
                return dt.strptime(string, fmt).date()
            except ValueError:
                pass
        
        raise SyntaxError(f"'{string}' can't be parsed as a valid date string.")

    while True:
        if date_str_input is None:
            date_str_input = input("Insert period or day arithmetic: ")
        try: 
            return_date = core(string=date_str_input)
            print(f"Success: {return_date.strftime("%a %d %b %Y")}")
            return return_date
        except Exception as e:
            print(f"'{date_str_input}' could not be parsed: {e}")
            date_str_input = None


def validate_both_double_currency(
        double_curr_input : str | None = None, 
        lower_bound : float = 0.0, 
        explain : bool = True
    ) -> tuple[float, str]:
    
    if explain and double_curr_input is None:
        print(
            f"To use this parser, you can do [+|=]operation [usd|eur|pen|...] (empty for default)."
            f"e.g. =9+9 usd -> (18, 'USD')"
        )
    
    def core(string: str) -> tuple[float, str]:
        try:
            m = re.match(r'(.*)(\w{3})$', string)
            operation_str, currency_str = m[1], m[2]
            operation = validate_arithmetic_operation(user_input=operation_str, lower_bound=lower_bound)
            currency = validate_currency(currency_input=currency_str)
            return operation, currency
        except:
            raise SyntaxError(f"'{string}' could not be parsed as a valid operation, currency pair.")


    while True: 
        if double_curr_input is None:
            double_curr_input = input("Type your currency operation: ")
        try:
            amount, currency = core(double_curr_input)
            print(f"Sucess: amount={amount} currency={currency}")
            return amount, currency
        except Exception as e:
            print(f"'{double_curr_input}' could not be parsed as a valid double, currency: {e}")
            double_curr_input = None
        

def validate_category(
        category_json : dict[str, str | dict[str, str]],
        category_input : str | None = None
) -> str:
    
    def category_print () -> None:
        
        pass

    def core():
        pass

    while True:
        if category_input is None:
            category_print()
            category_input = input("Type the corresponding keybind from the dictionary above.")

        try:
            category = core(category_input)
            print(f"Sucess: {category}")
            return category
        except Exception as e:
            print(f"Something went wrong: {e}")
            category_input = None


    pass