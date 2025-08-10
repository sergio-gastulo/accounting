from pandas import Period
from random import choices
from pathlib import Path
import json


def _get_json(json_path: Path) -> dict[str, str]:
    """
    Loads JSON from 'path' and flattens the fields.json.        
    """
    shortname_descript_dict = {}

    with open(json_path,'r') as file:
        for item_dict in json.load(file):
            subcategories = item_dict.get("subcategories")
            if subcategories:
                for item in subcategories:
                    shortname_descript_dict.update({item["shortname"]: item["description"]})
            else:
                shortname_descript_dict.update({item_dict["shortname"]: item_dict["description"]})

    return shortname_descript_dict


def _get_period(default_period: Period) -> Period: 
    """
    Returns a 'period' from user input. 
    If the parse is not successful, 'get_period' returns None, so other functions can work with the default option.
    If the parse is successful but the values are unreal integers (e.g., 'month = 20'), they are added as monthts.
    """

    print(f"Type the period in format 'yyyy-MM'(e.g. 2025-08). Press [return] to use today's period: '{default_period}'")
    user_input = input()

    if not user_input:
        print(f"Using default period: '{default_period}'")
        return default_period

    else:
        try:
            year, month = [int(x) for x in user_input.split('-')]
            return (Period(year=year,month=month, freq='M'))
        except ValueError:
            print(f"Not enough variables to parse in '{user_input}'.")
        except NameError:
            print(f"Not a valid period in '{user_input}'")
        except Exception as e:
            print(f"Unknown error: {e}") 
        
        print(f"Using default period: '{default_period}'")
        return default_period


def _get_category(dict_cat: dict[str, str]):
    """
    Returns a 'category' from user input, part of all the 'shortnames' in 'json_paths'. 
    If no category is chosen, one is randomly picked.
    """
    while True:
        try:
            print(json.dumps(dict_cat, indent=4))
            print("Type the category you would like to plot. Press [return] to skip and chose a random category:")
            category = str(input()).upper()

            if category in dict_cat:
                return category
            if not category:
                raise EOFError
            else: 
                print("The category written is not valid. Please try again.")

        except EOFError:
            print("Random category chosen.")
            category = choices(list(dict_cat.keys()), k=1)[0]                
            return category
        

def _doc_printer(func: callable) -> None:
    cyan_str = '\033[96m'
    end_str = '\033[0m'
    print(f'{cyan_str}Function name: \n{func.__name__}{end_str}\n')
    print(f'{cyan_str}Documentation{end_str}: {func.__doc__}')


def _get_path(path: Path = None)-> Path:
    while not (path and path.is_file()):
        if path is not None:
            print(f"'{path}' is not a valid file.")
        path = Path(input("Enter the absolute path to the JSON category file: ")).resolve()
    
    return path



if __name__ == "__main__":
    from os import getenv
    from dotenv import load_dotenv
    from pandas import Timestamp
    
    load_dotenv()
    json_path = getenv("JSON_PATH")
    default_period = Timestamp.today().to_period('M')

    plot1 = lambda : _get_json(json_path=json_path)
    plot2 = lambda : _get_period(default_period=default_period)
    plot3 = lambda : _get_category(json_path=json_path)
    