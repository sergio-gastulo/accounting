import matplotlib.pyplot as plt
import pandas as pd
import json
import matplotlib.dates as mdates
import sys


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
        
        templist = []

        with open(path,'r') as file:
            for key, value in json.load(file).items():
                shortname = value.get('shortname')
                if shortname:
                    templist.append([shortname, value['description']])
                else: 
                    templist.extend(
                        [[subvalue['shortname'], subvalue['description']] for subvalue in value.values()]
                    )

        return dict(templist)


class DataPlotter:

    def __init__(self, path: str, dictionary: CustomDictionaries):
        self.df = self.load_csv(path)
        self.period = pd.Timestamp.today().to_period('M')
        self.dictionary = dictionary 

        # Calling dark mode for plotting
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


    def categories_per_month(self) -> None:
        
        df_grouped_period = self.df.groupby([self.df.Date.dt.to_period('M'),'Category']).Amount.sum()[self.period.__str__()] 
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
            label=f'Gastos registrados al {self.dictionary.months_es[self.period.month]} del {self.period.year}:\nPEN {sum(df_grouped_period.values):.2f}',
            pad=20,
            loc='center',
            y = 1.0
            )

        ax.set_xlabel('Gastos', labelpad=8.0)
        ax.set_ylabel('Categories', labelpad=16.0)

        fig.subplots_adjust(left=0.2, right=0.9)
        plt.show()

    
    def expenses_time_series(self) -> None:
        
        df_period_amount = self.df[~self.df.Category.isin(['BLIND','INGRESO-SOLES','SOLES-USD','USD-SOLES'])]
        df_period_amount = df_period_amount.groupby(df_period_amount.Date.dt.to_period('M')).Amount.sum()
        scatter_value = df_period_amount[self.period.__str__()]

        fig, ax = plt.subplots()
        
        ax.plot( df_period_amount.index.to_timestamp(),  df_period_amount.values,  marker='o', color=(1,1,1))
            
        ax.scatter( self.period.to_timestamp(), scatter_value, color=(1,0,0), zorder=5)

        ax.text(
            self.period.to_timestamp() + pd.Timedelta(days=10),
            1.05 * scatter_value,
            s=f'PEN {scatter_value:.2f}',
            size='11'
        )

        ax.axhline(scatter_value,color=(1,0,0))

        ax.set_title('Gastos realizados por mes', pad=20)
        ax.set_xlabel('Fecha', labelpad=16.0)
        ax.set_ylabel('Gastos', labelpad=16.0)

        fig.autofmt_xdate()
        plt.show()
    

    def category_time_series(self, category: str) -> None:
        
        df_category_ts = self.df[self.df.Category == category]
        df_category_ts = df_category_ts.groupby(df_category_ts.Date.dt.to_period('M')).Amount.sum()
        td_period_string = self.period.__str__()
        
        fig, ax = plt.subplots()
        ax.plot(df_category_ts.index.to_timestamp(), df_category_ts.values, color=(1,1,1), marker='o')

        try: 
            category_value_td = df_category_ts[td_period_string]
            ax.scatter(self.period.to_timestamp(), category_value_td, color=(1,0,0), zorder=5)

            ax.text(
                self.period.to_timestamp(),
                category_value_td,
                s=f'PEN {category_value_td:.2f}',
                size='11',
                horizontalalignment = 'left' if mdates.date2num(self.period.to_timestamp()) < ax.get_xlim()[1] / 2 else 'right',
                verticalalignment = 'bottom' if df_category_ts[(self.period - 1).__str__()] <= category_value_td else 'top'
            )

            ax.axhline( category_value_td, color=(1,0,0))
            
        except:
            print(f'Period \'{td_period_string}\' not found on plot.')

        ax.set_title(f'Gasto mensual de: {self.dictionary.categories[category]}', pad=16.0)
        ax.set_ylabel('Gasto en PEN',labelpad=16.0)
        ax.set_xlabel('Periodos',labelpad=16.0)

        fig.autofmt_xdate()
        plt.show()

    
    def monthly_time_series(self) -> None:

        df_year_month = self.df[~self.df.Category.isin(['BLIND','INGRESO-SOLES','SOLES-USD','USD-SOLES'])]
        df_year_month = df_year_month.groupby(df_year_month.Date.dt.to_period('D')).Amount.sum()

        dfs = [df_year_month.get((self.period + i).__str__(), pd.Series(dtype='float64')) for i in range (-1,2)]
        fig, ax = plt.subplots(1,2, figsize=(12,5))

        for i, dframes in enumerate(dfs):

            temp_color = (1,1,1) if i != 1 else (0,1,0)
            ax[0].plot( dframes.index.to_timestamp(), dframes.values, marker='o', color=temp_color)
            ax[1].plot( dframes.index.to_timestamp(), dframes.values.cumsum(), color= temp_color, marker='o')

        for axes in ax:
            axes.axvline( mdates.date2num(pd.Timestamp.today().to_period('D')), color=(1,0,0))

        fig.suptitle(f'Grafico del gasto mensual centrado en {self.dictionary.months_es[self.period.month]} del {self.period.year}')

        fig.supxlabel('Periodos', y=-0.1)
        fig.supylabel('Gasto en PEN', x=0.05)

        fig.autofmt_xdate()
        plt.show()



def main_interface()->None:
    pass



if __name__ == '__main__':
    
    try: 
        json_path = sys.argv[2]
    except IndexError:
        print("Something went wrong during the json_path call.")
        json_path = input("Enter the path (if possible, non relative) of the JSON")

    try:
        csv_path = sys.argv[1]
    except IndexError:
        print("Something went wrong during the csv_path call.")
        csv_path = input("Enter the path (if possible, non-relative) of the CSV: ")

    csv_plot = DataPlotter(csv_path, CustomDictionaries(json_path))

    main_interface()    
