import sys
import json
from random import choices
import pandas as pd
from .classes.custom_dictionaries import CustomDictionaries
from .classes.data_plotter import DataPlotter

class MainInterface:
    def __init__(self, csv_plot: DataPlotter):
        self.csv = csv_plot


    def _get_category(self) -> str:
        """
        Returns a `category` from user input. 
        In the worst case, it will be randomly chosen from `csv_plot.dictionary.categories`
        """
        dict_cat = self.csv.dictionary.categories

        while True:
            try:
                print(json.dumps(dict_cat, indent=4))
                print("Type the category you would like to plot ('x' to leave and select a random category.): ")
                category = str(input()).upper()

                if category == 'X':
                    raise EOFError
                if category in dict_cat:
                    return category
                else: 
                    print("The category written is not valid. Please try again.")

            except EOFError:
                print("Random category chosen.")
                category = choices(list(dict_cat.keys()))[0]                
                return category
    

    def _get_period(self) -> pd.Period | None: 
        """
        Returns a `period` from user input. 
        If the parse is not successful, `get_period` returns None, so other functions can work with the default option.
        If the parse is successful but the values are unreal integers (e.g., `month = 20`), they are added as monthts.
        """

        while True:
            try:
                print(f"Type 'x' to enter a given period. Press any other key to select today's period: {self.csv.period.__str__()}")
                validation = input()
                if validation.lower() == 'x':
                    print("Type the year of the period: ")
                    year = int(input())
                    print("Type the month of the period: ")
                    month = int(input())
                    period = pd.Period(year=year,month=month, freq='M')
                else:
                    period = None
                break
            except ValueError:
                print("Integer parsing unsuccessful. Running this again.")
            except Exception as e:
                print(f"Unknown error occured: {e}")
                print("Using current period as default.")
                period = None
                break

        return period

    def _doc_printer(self, func: callable) -> None:
        cyan_str = '\033[96m'
        end_str = '\033[0m'
        print(f'{cyan_str}Function name: \n{func.__name__}{end_str}\n')
        print(f'{cyan_str}Documentation{end_str}: {func.__doc__}')


    def main_interface(self):
        """
        Plots and prints function definitions while taking user input.
        """
        self._doc_printer(self.csv.categories_per_month)
        self.csv.categories_per_month(self._get_period())

        self._doc_printer(self.csv.expenses_time_series)
        self.csv.expenses_time_series(self._get_period())
        
        self._doc_printer(self.csv.monthly_time_series)
        self.csv.monthly_time_series(self._get_period())
        
        self._doc_printer(self.csv.category_time_series)
        self.csv.category_time_series(self._get_category(), self._get_period())


if __name__ == '__main__':
    
    try:
        csv_path = sys.argv[1]
    except IndexError:
        print("Something went wrong during the csv_path call.")
        print("Enter the path (if possible, non-relative) of the CSV: ")
        csv_path = input()
    
    try: 
        json_path = sys.argv[2]
    except IndexError:
        print("Something went wrong during the json_path call.")
        print("Enter the path (if possible, non relative) of the JSON")
        json_path = input()

    MainInterface(DataPlotter(csv_path, CustomDictionaries(json_path))).main_interface()
