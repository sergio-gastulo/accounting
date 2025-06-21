import sys
import json
from random import choices
from typing import Optional
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

class CustomDictionaries:
    def __init__(self, path: str):
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
        self.categories = self.create_json(path)


    def create_json(self, path: str) -> dict[str, str]:
        """
        Loads JSON from `path` and returns the JSON parsed as follows:
        * The pattern `key: {sname, description}` is mapped to `sname: description`
        * The pattern `key: {skey1: {sname, desc}, skey2: {sname, desc}}` is mapped to `sname1: desc1, sname2, desc2` (flattened)
        """
        
        shortname_descript_dict = {}

        with open(path,'r') as file:
            for item_dict in json.load(file):
                subcategories = item_dict.get("subcategories")
                if subcategories:
                    for item in subcategories:
                        shortname_descript_dict.update({item["shortname"]: item["description"]})
                else:
                    shortname_descript_dict.update({item_dict["shortname"]: item_dict["description"]})

        return shortname_descript_dict


class DataPlotter:

    def __init__(self, path: str, dictionary: CustomDictionaries):
        self.df = self.load_csv(path)
        self.period = pd.Timestamp.today().to_period('M')
        self.dictionary = dictionary 

        plt.style.use('dark_background')
        plt.rcParams['font.family'] = 'monospace'
        plt.rcParams['font.size'] = 12
    

    def load_csv(self, path: str) -> pd.DataFrame:
        """
        Loads a dataframe from `path`. 
        """
        usd_pen = 3.67
        raw_csv = pd.read_csv(
            path,
            header=0,
            index_col=None,
            dtype={"Category": "string","Amount":"float64","Description":"string"},
            parse_dates=["Date"],
            dayfirst=True
            )
        raw_csv.loc[raw_csv.Category == 'INGRESO-USD','Amount'] *= usd_pen
        raw_csv.loc[raw_csv.Category == 'INGRESO-USD','Category'] = 'INGRESO-SOLES'

        return raw_csv


    def categories_per_month(self, period: Optional[pd.Period] = None) -> None:
        """
        Plots the csv grouped by Category in the given `period`. 
        If `period` is None, it is assigned the value of the current period.
        If `period` is specified but the month is not included grouped csv, assumes the current period as given.
        """

        if period is None:
            period = self.period

        try:
            df_grouped_period = self.df.groupby([self.df.Date.dt.to_period('M'),'Category']).Amount.sum()[str(period)] 
        except KeyError:
            print("Period not found. Using current period as default.")
            period = self.period
            df_grouped_period = self.df.groupby([self.df.Date.dt.to_period('M'),'Category']).Amount.sum()[str(period)] 
        
        except Exception as e:
            print(f"Unknown error: {e}")
            return
        
        df_grouped_period = df_grouped_period[~df_grouped_period.index.isin(['BLIND','INGRESO-SOLES'])]


        fig, ax = plt.subplots()

        temp_max = max(df_grouped_period.values)

        bars = ax.barh(
            [self.dictionary.categories[key] for key in df_grouped_period.index],  
            df_grouped_period.values,  
            height=0.8,
            color=(1,1,1),
            align='center'
            )

        ax.tick_params(axis='y',labelsize=10)

        for bar in bars:
            width = bar.get_width()
            y = bar.get_y() + bar.get_height() / 2
            ax.text(
                (0.5 if temp_max / 2 < width else 1.1) * width,
                y,
                f'{width:.2f}',
                va='center',
                ha='left',
                fontsize=10,
                color = (0,0,0) if temp_max / 2 < width else (1,1,1)
            )

        ax.set_title(
            label=f'Gastos registrados al {self.dictionary.months_es[period.month]} del {period.year}:\nPEN {sum(df_grouped_period.values):.2f}',
            pad=20,
            loc='center',
            y = 1.0
            )

        ax.set_xlabel('Gastos', labelpad=8.0)
        ax.set_ylabel('Categories', labelpad=16.0)

        fig.subplots_adjust(left=0.2, right=0.9)
        plt.show()


    def expenses_time_series(self, period: Optional[pd.Period] = None) -> None:
        """
        Plots a time series formed by expenses per month. It scatters the given `period` in red.
        If `period` is not specified, then it scatters the current period.
        If `period` is specified but the month is not included in the time series, a simple statement is printed.
        """

        if period is None:
            period = self.period
        
        df_period_amount = self.df[~self.df.Category.isin(['BLIND','INGRESO-SOLES','SOLES-USD','USD-SOLES'])]
        df_period_amount = df_period_amount.groupby(df_period_amount.Date.dt.to_period('M')).Amount.sum()
        
        fig, ax = plt.subplots()
        ax.plot( df_period_amount.index.to_timestamp(),  df_period_amount.values,  marker='o', color=(1,1,1))
        
        try:
            scatter_value = df_period_amount[period.__str__()]
            ax.scatter( period.to_timestamp(), scatter_value, color=(1,0,0), zorder=5)
            ax.text( period.to_timestamp() + pd.Timedelta(days=10), 1.05 * scatter_value, s=f'PEN {scatter_value:.2f}', size='11')
            ax.axhline(scatter_value,color=(1,0,0))
        except KeyError:
            print("Period was succesfully parsed, but it is not present in the time series. Ignoring said period on the plot.")
        except:
            print("Unknown error.")

        ax.set_title('Gastos realizados por mes', pad=20)
        ax.set_xlabel('Fecha', labelpad=16.0)
        ax.set_ylabel('Gastos', labelpad=16.0)
        fig.autofmt_xdate()
        plt.show()
    

    def category_time_series(self, category: str, period: Optional[pd.Period] = None) -> None:
        """
        Plots a time series from the given `category`. This is not optional. 
        The validation of `category` is handled in `main_interface()`
        If `period` is not specified, then it tries to scatter the current period.
        If `period` is specified but the month is not included in the time series, a simple warning is printed.
        """

        if period is None:
            period = self.period        
        
        df_category_ts = self.df[self.df.Category == category]
        df_category_ts = df_category_ts.groupby(df_category_ts.Date.dt.to_period('M')).Amount.sum()
        td_period_string = period.__str__()
        
        fig, ax = plt.subplots()
        ax.plot(df_category_ts.index.to_timestamp(), df_category_ts.values, color=(1,1,1), marker='o')

        try: 
            category_value_td = df_category_ts[td_period_string]
            ax.scatter(period.to_timestamp(), category_value_td, color=(1,0,0), zorder=5)

            ax.text(
                period.to_timestamp(),
                category_value_td,
                s=f'PEN {category_value_td:.2f}',
                size='11',
                horizontalalignment = 'left' if mdates.date2num(period.to_timestamp()) < ax.get_xlim()[1] / 2 else 'right',
                verticalalignment = 'bottom' if df_category_ts[(period - 1).__str__()] <= category_value_td else 'top'
            )

            ax.axhline( category_value_td, color=(1,0,0))
            
        except:
            print(f"Period '{td_period_string}' not found on plot.")

        ax.set_title(f'Gasto mensual de: {self.dictionary.categories[category]}', pad=16.0)
        ax.set_ylabel('Gasto en PEN',labelpad=16.0)
        ax.set_xlabel('Periodos',labelpad=16.0)

        fig.autofmt_xdate()
        plt.show()

    
    def monthly_time_series(self, period: Optional[pd.Period] = None) -> None:
        """
        Plots two time series charts for daily expenses across three months:\n
        the previous, current, and next month (relative to `period`).
        - The left plot shows daily expense amounts.
        - The right plot shows the cumulative expense over time.
        If `period` is not specified, it is assumed to be the current period. 

        Highlights:
        - The current month is shown in green, others in white.
        - Today's date is marked with a vertical red line.
        - If `period` is not current period, then the vertical line is located at `period.asfreq('D') + today.days`
        - Excludes categories: 'BLIND', 'INGRESO-SOLES', 'SOLES-USD', and 'USD-SOLES'.
        """
        if period is None: 
            period = self.period

        df_year_month = self.df[~self.df.Category.isin(['BLIND','INGRESO-SOLES','SOLES-USD','USD-SOLES'])]
        df_year_month = df_year_month.groupby(df_year_month.Date.dt.to_period('D')).Amount.sum()

        dfs = [df_year_month.get((period + i).__str__(), pd.Series(dtype='float64')) for i in range (-1,2)]
        fig, ax = plt.subplots(1,2, figsize=(12,5))

        for i, dframes in enumerate(dfs):

            temp_color = (1,1,1) if i != 1 else (0,1,0)
            ax[0].plot( dframes.index.to_timestamp(), dframes.values, marker='o', color=temp_color)
            ax[1].plot( dframes.index.to_timestamp(), dframes.values.cumsum(), color= temp_color, marker='o')

        for axes in ax:
            axes.axvline( mdates.date2num(period.asfreq('D', how='start') + pd.Timestamp.today().day), color=(1,0,0))

        fig.suptitle(f'Grafico del gasto mensual centrado en {self.dictionary.months_es[period.month]} del {period.year}')

        fig.supxlabel('Periodos', y=-0.1)
        fig.supylabel('Gasto en PEN', x=0.05)

        fig.autofmt_xdate()
        plt.show()


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
