from sqlite3 import connect
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def darkmode() -> None:
    plt.style.use('dark_background')
    plt.rcParams['font.family'] = 'monospace'
    plt.rcParams['font.size'] = 12


def sql_to_pd(db_path: Path) -> pd.DataFrame:
    """
    Connects to 'db_path' and returns dataframe. Filters only by user currency for now.
    """
    with connect(db_path) as conn:
        df = pd.read_sql(
            f"SELECT * FROM cuentas;", 
            conn,
            parse_dates={"date": {"format": "%y-%m-%d"}}
        )
    return df


def categories_per_month(db_path: Path, period: pd.Period, categories: dict, months_es: dict) -> None:
        """
        Plots dataframe 'df' grouped by 'category' for each 'currency' in the specified 'period' in the db. 
        period format: pandas.Period 
        """
        
        with connect(db_path) as conn:
            query = """
                SELECT 
                    currency, category, SUM(amount) AS total_amount
                FROM cuentas 
                WHERE 
                    date LIKE :period || '%' 
                    AND (NOT category IN ('INGRESO', 'BLIND')) 
                GROUP BY 
                    currency, category;
            """

            # df structure being returned:
            #    currency   category     SUM(amount)
            # 0       EUR   HOME         420.000000
            df = pd.read_sql(
                query,
                conn,
                params={"period": str(period)}
            )
            currency_list = pd.read_sql("SELECT DISTINCT currency FROM cuentas;", conn)["currency"].tolist()


        def core_plot_logic(df: pd.DataFrame, currency: str) -> None:            
            # this uses a df whose structure goes as follows:
            #   df.index = category
            #   a single value column with floats
            fig, ax = plt.subplots()
            values = df.total_amount
            max_value = max(values)

            bars = ax.barh(
                [categories[key] for key in df.category],  
                values,  
                height=0.8,
                color=(1,1,1),
                align='center'
            )

            ax.tick_params(axis='y', labelsize=10)

            for bar in bars:
                width = bar.get_width()
                y = bar.get_y() + bar.get_height() / 2
                ax.text(
                    (0.5 if max_value / 2 < width else 1.1) * width,
                    y,
                    f'{width:.2f}',
                    va='center',
                    ha='left',
                    fontsize=10,
                    color = (0,0,0) if max_value / 2 < width else (1,1,1)
                )

            ax.set_title(
                label=f'Spending registered on {months_es[period.month]}, {period.year}:\n{currency} {sum(values):.2f}',
                pad=20,
                loc='center',
                y = 1.0
            )

            ax.set_xlabel('Spendings', labelpad=8.0)
            ax.set_ylabel('Categories', labelpad=16.0)

            fig.subplots_adjust(left=0.2, right=0.9)
            plt.show()
            
            
        for currency in currency_list:
            df_currency = df.loc[df.currency == currency, ['category', 'total_amount']]
            core_plot_logic(df_currency, currency)



def expenses_time_series(db_path: Path, period: pd.Period) -> None:
    """
    Groups spendings by month, and plots it scattering the given 'period' in red.
    If 'period' is not specified, then it scatters the current period.
    If 'period' is specified but the month is not included in the time series, nothing is scattered.
    """

    

    df_period_amount = df[~df.category.isin(['BLIND','INGRESO'])]
    df_period_amount = df_period_amount.groupby(df_period_amount.date.dt.to_period('M')).amount.sum()
    
    fig, ax = plt.subplots()
    ax.plot(df_period_amount.index.to_timestamp(), df_period_amount.values, marker='o', color=(1,1,1))
    
    try:
        scatter_value = df_period_amount[str(period)]
        ax.scatter(period.to_timestamp(), scatter_value, color=(1,0,0), zorder=5)
        ax.text(period.to_timestamp() + pd.Timedelta(days=10), 1.05 * scatter_value, s=f'PEN {scatter_value:.2f}', size='11')
        ax.axhline(scatter_value, color=(1,0,0))
    except KeyError:
        print("Period was succesfully parsed, but it is not present in the time series. Ignoring said period on the plot.")
    except Exception as e:
        print(f"Unknown error: {e}")

    ax.set_title('Spendings grouped by month', pad=20)
    ax.set_xlabel('Date', labelpad=16.0)
    ax.set_ylabel('Spendings', labelpad=16.0)
    fig.autofmt_xdate()
    plt.show()


def category_time_series(df: pd.DataFrame, period: pd.Period, category: str) -> None:
    """
    Plots a time series from the given 'category'.
    If 'period' is not specified, then it will try to scatter the current period.
    If 'period' is specified but the month is not included in the time series, a simple warning is printed.
    This is good for categories that should mantain a certain average: INGRESOS, CASA-ALQUILER, etc.
    """
    
    df_category_ts = df[df.category == category]
    df_category_ts = df_category_ts.groupby(df_category_ts.date.dt.to_period('M')).amount.sum()
    td_period_string = str(period)
    
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
            # I don't remember how it works, but it calibrates the placement of 'period' as a string within the plot 
            horizontalalignment = 'left' if mdates.date2num(period.to_timestamp()) < ax.get_xlim()[1] / 2 else 'right',
            verticalalignment = 'bottom' if df_category_ts[(period - 1).__str__()] <= category_value_td else 'top'
        )
        ax.axhline(category_value_td, color=(1,0,0))        
    except:
        print(f"Period '{td_period_string}' not found on plot.")

    ax.set_title(f'Monthly spending on: {category}', pad=16.0)
    ax.set_ylabel('Spendings in PEN',labelpad=16.0)
    ax.set_xlabel('Periods',labelpad=16.0)

    fig.autofmt_xdate()
    plt.show()


def monthly_time_series(df: pd.DataFrame, period: pd.Period, months_es: dict) -> None:
    """
    Plots two time series charts for daily expenses across three months: the previous, current, and next month (relative to 'period').
    - The left plot shows daily spendings.
    - The right plot shows the cumulative spendings over time.

    Highlights:
    - The current month is shown in green, others in white.
    - Today's date is marked with a vertical red line.
    - If 'period' is not current period, then the vertical line is calculated as 'period.asfreq('D') + today.days'
    - Excludes categories: 'BLIND', 'INGRESO'
    """


    df_year_month = df[~df.category.isin(['BLIND','INGRESO'])]
    df_year_month = df_year_month.groupby(df_year_month.date.dt.to_period('D')).amount.sum()

    # this collects the three consecutive-monthly periods: [-1,0,1]
    dfs = [df_year_month.get((period + i).__str__(), pd.Series(dtype='float64')) for i in range (-1,2)]
    fig, ax = plt.subplots(1,2, figsize=(12,5))

    for i, dframes in enumerate(dfs):
        temp_color = (1,1,1) if i != 1 else (0,1,0)
        ax[0].plot(dframes.index.to_timestamp(), dframes.values, marker='o', color=temp_color)
        ax[1].plot(dframes.index.to_timestamp(), dframes.values.cumsum(), color= temp_color, marker='o')

    for axes in ax:
        axes.axvline( mdates.date2num(period.asfreq('D', how='start') + pd.Timestamp.today().day), color=(1,0,0))

    fig.suptitle(f'Plot of monthly spending centered at {months_es[period.month]}, {period.year}')

    fig.supxlabel('Periods', y=-0.1)
    fig.supylabel('Spendings in PEN', x=0.05)
    fig.autofmt_xdate()
    plt.show()


# ------------------------------------------------------------
# Testing Instructions
#
# 1. Navigate to the acc_py directory:
#        cd acc_py
# 2. Run in interactive mode:
#        python -i ./src/acc_py/plot.py
# 3. Call plot1(), plot2(), plot3(), or plot4() — each should 
#    display the correct plot.
#
# Variables to configure:
#   * .env file
#   * period — specify as a pandas.Period expression:
#       https://pandas.pydata.org/docs/reference/api/pandas.Period.html
#   * category
# ------------------------------------------------------------


if __name__ == "__main__":
    
    from os import getenv
    from dotenv import load_dotenv
    from validate import _get_json

    load_dotenv()
    db_path = getenv("DB_PATH")
    df = sql_to_pd(db_path=db_path)
    months_es = {
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
    categories = _get_json(getenv("JSON_PATH"))

    period = pd.Timestamp.today().to_period('M')
    category = 'CASA' # modify accordingly to fields.json
    darkmode()

    print(df.head(5))
    

    # Uncomment the lines to run the plots
    plot1 = lambda : categories_per_month(db_path, period, categories=categories, months_es=months_es)
    plot2 = lambda : expenses_time_series(df, period)
    plot3 = lambda : category_time_series(df, period, category)
    plot4 = lambda : monthly_time_series(df, period, months_es=months_es)

    # or play with them when running python -i ...