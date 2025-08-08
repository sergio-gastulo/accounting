import sys
import json
from random import choices
import pandas as pd
from pathlib import Path
import json
import matplotlib.pyplot as plt
# custom module
from plot import *
from validate import _get_json

class CustomDictionaries:
    def __init__(self, path: Path):
        # Month dictionary for translation from ENG to SPA
        self.months_es = {
                1: "Enero",
                2: "Febrero",
                3: "Marzo",
                4: "Abril",
                5: "Mayo",
                6: "Junio",
                7: "Julio",
                8: "Agosto",
                9: "Septiembre",
                10: "Octubre",
                11: "Noviembre",
                12: "Diciembre"
            }
        self.categories = _get_json(path)


class DataPlotter:
    def __init__(self, db_path: Path):
        self.df = sql_to_pd(db_path)
        self.td_period = pd.Timestamp.today().to_period('M')


class MainInterface:
    def __init__(self, csv_plot: DataPlotter):
        self.csv = csv_plot

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
