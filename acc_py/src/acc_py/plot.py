from sqlite3 import connect
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
# custom context
try:
    from .context import ctx 
except:
    from context import ctx


def darkmode() -> None:
    plt.style.use('dark_background')
    plt.rcParams['font.family'] = 'monospace'
    plt.rcParams['font.size'] = 12


def categories_per_month() -> None:
        """
        Plots dataframe 'df' grouped by 'category' for each 'currency' in the specified 'period' in the db. 
        period format: pandas.Period 
        """
        
        with connect(ctx.db_path) as conn:
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
                params={"period": str(ctx.period)}
            )


        def core_plot_logic(df: pd.DataFrame, currency: str) -> None:            
            # this uses a df whose structure goes as follows:
            #   df.index = category
            #   a single value column with floats
            fig, ax = plt.subplots()
            values = df.total_amount
            max_value = max(values)

            bars = ax.barh(
                [ctx.categories_dict[key] for key in df.category],  
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
                label=f'Spending registered on {ctx.month_es[ctx.period.month]}, {ctx.period.year}:\n{currency} {sum(values):.2f}',
                pad=20,
                loc='center',
                y = 1.0
            )

            ax.set_xlabel('Spendings', labelpad=8.0)
            ax.set_ylabel('Categories', labelpad=16.0)

            fig.subplots_adjust(left=0.2, right=0.9)
            plt.show()
            
            
        for currency in ctx.currency_list:
            df_currency = df.loc[df.currency == currency, ['category', 'total_amount']]
            core_plot_logic(df_currency, currency)



def expenses_time_series() -> None:
    """
    Groups spendings by month, and plots it scattering the given 'period' in red.
    If 'period' is not specified, then it scatters the current period.
    If 'period' is specified but the month is not included in the time series, nothing is scattered.
    """

    with connect(ctx.db_path) as conn:
        query = """
            SELECT 
                currency,
                strftime('%Y-%m', date) AS period,
                SUM(amount) AS total_amount
            FROM cuentas
            WHERE NOT (category IN ('INGRESO', 'BLIND')) 
            GROUP BY currency, strftime('%Y-%m',date);
        """
        df = pd.read_sql(
            query,
            conn,
            parse_dates={"period": {"format": "%Y-%m"}}
        )
        df.period = df.period.dt.to_period('M')

    def core_plot_logic(df: pd.DataFrame, currency: str) -> None:
        fig, ax = plt.subplots()
        ax.plot(df.index.to_timestamp(), df.values, marker='o', color=(1,1,1))
        
        try:
            scatter_value = df.loc[ctx.period, "total_amount"]
            ax.scatter(ctx.period.to_timestamp(), scatter_value, color=(1,0,0), zorder=5)
            ax.text(ctx.period.to_timestamp() + pd.Timedelta(days=10), 1.05 * scatter_value, s=f'{currency} {scatter_value:.2f}', size='11')
            ax.axhline(scatter_value, color=(1,0,0))
        except KeyError:
            print(f"'{str(ctx.period)}' is not part of the index of df. Ignoring said period on the plot.")

        ax.set_title(f"Spendings through the months and years in {currency}", pad=20)
        ax.set_xlabel('Date', labelpad=16.0)
        ax.set_ylabel(f"Spendings in {currency}", labelpad=16.0)
        fig.autofmt_xdate()
        plt.show()

    for currency in ctx.currency_list:
        df_currency = df.loc[df.currency == currency, ['period', 'total_amount']].set_index('period')
        core_plot_logic(df_currency, currency)



def category_time_series() -> None:
    """
    Plots a time series from the given 'category'.
    If 'period' is not specified, then it will try to scatter the current period.
    If 'period' is specified but the month is not included in the time series, a simple warning is printed.
    This is good for categories that should mantain a certain average: INGRESOS, CASA-ALQUILER, etc.
    """

    with connect(ctx.db_path) as conn:
        query = """
            SELECT 
                currency,
                strftime('%Y-%m', date) AS period,
                SUM(amount) as total_amount 
            FROM cuentas 
            WHERE category = :category
            GROUP BY currency, period;
        """
        df = pd.read_sql(
            query,
            conn,
            params={"category": ctx.selected_category},
            parse_dates={"period": {"format": "%Y-%m"}}
        )
        df.period = df.period.dt.to_period('M')

    period = str(ctx.period)
    timestamp_period = ctx.period.to_timestamp()

    def core_plot_logic(df: pd.DataFrame, currency: str) -> None:
        fig, ax = plt.subplots()
        ax.plot(df.index.to_timestamp(), df.values, color=(1,1,1), marker='o')

        try:
            category_value_td = df.loc[ctx.period, "total_amount"]
            ax.scatter(timestamp_period, category_value_td, color=(1,0,0), zorder=5)

            ax.text(
                timestamp_period,
                category_value_td,
                s=f'{currency} {category_value_td:.2f}',
                size='11',
                # I don't remember how it works, but it calibrates the placement of 'period' as a string in the plot 
                horizontalalignment = 'left' if mdates.date2num(timestamp_period) < ax.get_xlim()[1] / 2 else 'right',
                verticalalignment = 'bottom' if df[(ctx.period - 1).__str__()] <= category_value_td else 'top'
            )
            ax.axhline(category_value_td, color=(1,0,0))        
        except:
            print(f"'{str(period)}' wasn't found on 'df' index.")

        ax.set_title(f"{ctx.selected_category.upper()}, currency: {currency}", pad=16.0)
        ax.set_ylabel(f"Spendings in {currency}",labelpad=16.0)
        ax.set_xlabel('Periods',labelpad=16.0)
        fig.autofmt_xdate()
        plt.show()
    
    for currency in ctx.currency_list:
        df_currency = df.loc[df.currency == currency, ['period', 'total_amount']].set_index('period')
        core_plot_logic(df_currency, currency)



def monthly_time_series() -> None:
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

    # it's the exact df as in expenses_time_series, worth executing it only once?
    with connect(ctx.db_path) as conn:
        query = """
            SELECT 
                currency,
                strftime('%Y-%m-%d', date) AS period,
                SUM(amount) AS total_amount
            FROM cuentas
            WHERE NOT (category IN ('INGRESO', 'BLIND')) 
            GROUP BY 
                currency, 
                strftime('%Y-%m-%d', date);
        """
        df = pd.read_sql(
            query,
            conn,
            parse_dates={"period": {"format": "%Y-%m-%d"}}
        )
        df.period = df.period.dt.to_period('D')

    def core_plot_logic(df: pd.DataFrame, currency: str) -> None:
        # this collects the three consecutive-monthly periods: [-1,0,1]
        dfs = [df.loc[str(ctx.period + i)] for i in range (-1,2)]
        fig, ax = plt.subplots(1,2, figsize=(12,5))

        for i, dframes in enumerate(dfs):
            color = (1,1,1) if i != 1 else (0,1,0)
            ax[0].plot(dframes.index.to_timestamp(), dframes.values, marker='o', color=color)
            ax[1].plot(dframes.index.to_timestamp(), dframes.values.cumsum(), color=color, marker='o')

        for axes in ax:
            axes.axvline(mdates.date2num(ctx.period.asfreq('D', how='start') + pd.Timestamp.today().day), color=(1,0,0))

        fig.suptitle(f'Monthly spendings centered at {ctx.month_es[ctx.period.month]}, {ctx.period.year} in {currency}')
        fig.supxlabel('Periods', y=-0.1)
        fig.supylabel(f"Spendings in {currency}", x=0.05)
        fig.autofmt_xdate()
        plt.show()

    for currency in ctx.currency_list:
        df_currency = df.loc[df.currency == currency, ['period', 'total_amount']].set_index('period')
        try: 
            core_plot_logic(df_currency, currency)
        except KeyError:
            print(f"{currency} omitted here. Few entries available.")


# ------------------------------------------------------------
# Testing Instructions
#
# 1. Navigate to the acc_py directory:
#        cd acc_py
# 2. Run in interactive mode:
#        python -i ./src/acc_py/plot.py
# 3. Call plot1(), plot2(), plot3(), or plot4() -- each should 
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
    ctx.db_path = getenv("DB_PATH")
    # df = sql_to_pd(db_path=ctx.db_path)
    ctx.month_es = {
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
    ctx.categories_dict = _get_json(getenv("JSON_PATH"))
    ctx.currency_list = ['EUR', 'USD', 'PEN']
    ctx.period = pd.Timestamp.today().to_period('M')
    ctx.selected_category = 'COMIDA-GROCERIES' # modify accordingly to fields.json
    darkmode()

    # Uncomment the lines to run the plots
    # categories_per_month()
    # expenses_time_series()
    category_time_series()
    # monthly_time_series()
    # or play with them when running python -i ...
    print("""
        functions loaded ready to be called:
            - categories_per_month()
            - expenses_time_series()
            - category_time_series()
            - monthly_time_series()
    """)