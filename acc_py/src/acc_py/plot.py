from sqlite3 import connect
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from numpy import atleast_1d
# custom context
try:
    from .context import ctx 
except:
    from context import ctx


def darkmode() -> None:
    plt.style.use('dark_background')
    plt.rcParams['font.family'] = 'monospace'
    plt.rcParams['font.size'] = 12


def categories_per_period(period: str | pd.Period | None = None) -> None:
        """
        Plots dataframe 'df' grouped by 'category' for each 'currency' in the specified 'period' in the db. 
        period format: pandas.Period 
        """

        if period is None:
            period = ctx.period
        else: 
            period = pd.Period(period, 'M')

        with connect(ctx.db_path) as conn:
            query_totals = """
                SELECT 
                    currency, category, SUM(amount) AS total_amount
                FROM cuentas 
                WHERE 
                    date LIKE :period || '%' 
                    AND category NOT IN ('INGRESO', 'BLIND') 
                GROUP BY 
                    currency, category;
            """
            df = pd.read_sql(query_totals, conn, params={"period": str(period)})
            
            query_currencies = """
                SELECT DISTINCT currency 
                FROM cuentas 
                WHERE 
                    date LIKE :period || '%'
                    AND category NOT IN ('INGRESO', 'BLIND');
            """
            currency_list = pd.read_sql(query_currencies, conn, params={"period": str(period)})["currency"].to_list()

        bars_per_ax = []

        def core_plot_logic(df: pd.DataFrame, currency: str, ax=None, fig=None) -> None:            
            values = df.total_amount
            max_value = max(values)
            labels = [ctx.categories_dict[key] for key in df.category]
            bars = ax.barh(labels, values, height=0.8, color=(1,1,1), align='center')
            ax.tick_params(axis='y', labelsize=10.5)

            bars_per_ax.append((ax, bars, df.category.to_list(), currency))
            
            for bar in bars:
                width   = bar.get_width()
                inside  = width > max_value / 2
                xpos    = (0.5 if inside else 1.1) * width
                ypos    = bar.get_y() + bar.get_height() / 2
                color   = (0,0,0) if inside else (1,1,1)
                
                ax.text(xpos, ypos, f'{width:.2f} {currency}', 
                    va='center', ha='left', fontsize=10, color=color
                )

            ax.text(0.90, 0.95, f'{currency} {values.sum():.2f}', transform=ax.transAxes, ha="left", va="top", fontsize=12)
            fig.subplots_adjust(left=0.25, right=0.95)

        def on_click(event):
            for ax, bars, labels, currency in bars_per_ax:
                if event.inaxes == ax:
                    for bar, label in zip(bars, labels):
                        contains, _ = bar.contains(event)
                        if contains:
                            bar.set_color('red')
                            print(f"\n\nCategory: {label}, Currency {currency}\n\n")
                            with connect(ctx.db_path) as conn:
                                query = """
                                    SELECT amount, description 
                                    FROM cuentas 
                                    WHERE 
                                        date LIKE :period || '%'
                                        AND category = :category
                                        AND currency = :currency;                               
                                """
                                print(pd.read_sql(
                                    query, 
                                    conn, 
                                    params={
                                        "period": str(period), 
                                        "category": label, 
                                        "currency": currency}
                                    ).sort_values("amount", ascending=False).to_markdown())
                            ax.figure.canvas.draw()
                            return

        heights = [
            len(df.loc[df.currency == currency, 'category'].unique())
            for currency in currency_list
        ]

        fig, axs = plt.subplots(len(currency_list), 1, sharex=True, gridspec_kw={'height_ratios': heights})
        axs = atleast_1d(axs)
        for i, currency in enumerate(currency_list):
            df_currency = df.loc[df.currency == currency, ['category', 'total_amount']].sort_values('total_amount', ascending=False)
            core_plot_logic(df_currency, currency, ax=axs[i], fig=fig)
        
        fig.suptitle(f"Spendings registered on {ctx.month_es[period.month]}, {period.year}")
    
        fig.canvas.mpl_connect('button_press_event', on_click)
        plt.show()


def expenses_time_series(period: str | pd.Period | None = None) -> None:
    """
    Groups spendings by month, and plots it scattering the given 'period' in red.
    If 'period' is not specified, then it scatters the current period.
    If 'period' is specified but the month is not included in the time series, nothing is scattered.
    """

    if period is None:
        period = ctx.period
    else: 
        period = pd.Period(period, 'M')

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
        df = pd.read_sql(query, conn, parse_dates={"period": {"format": "%Y-%m"}})
        df.period = df.period.dt.to_period('M')
        query_currencies = """
            SELECT DISTINCT currency 
            FROM cuentas 
            WHERE 
                date LIKE :period || '%'
                AND category NOT IN ('INGRESO', 'BLIND');
        """
        currency_list_in_period = pd.read_sql(query_currencies, conn, params={"period": str(period)})["currency"].to_list()
        currency_list = pd.read_sql("SELECT DISTINCT currency FROM cuentas", conn)["currency"].to_list()


    def core_plot_logic(df: pd.DataFrame, currency: str, color: str, ax = None, fig = None) -> None:
        ax.plot(df.index.to_timestamp(), df.values, marker='o', color=color, label=currency)
        
        if currency in currency_list_in_period:
            scatter_value = df.loc[period, "total_amount"]
            ax.scatter(period.to_timestamp(), scatter_value, color='red', zorder=5)
            x = period.to_timestamp() + pd.Timedelta(days=10)       # x-axis + offset
            y = scatter_value * 1.05                                # y-axis * offset
            text = f'{currency} {scatter_value:.2f}'
            ax.text(x, y, s=text, size='12')
        else:
            print(f"'{currency}' is not available to be scattered.")

        ax.set_xlabel('Date', labelpad=16.0)
        fig.autofmt_xdate()


    fig, ax = plt.subplots()

    for currency, color in zip(currency_list, ctx.colors):
        df_currency = df.loc[df.currency == currency, ['period', 'total_amount']].set_index('period')
        core_plot_logic(df_currency, currency, ax=ax, fig=fig, color=color)
    
    fig.suptitle("Spendings as a Time Series per Currency")
    plt.show()


def category_time_series(category: str = None, period: str | pd.Period | None = None) -> None:
    """
    Plots a time series from the given 'category'.
    If 'period' is not specified, then it will try to scatter the current period.
    If 'period' is specified but the month is not included in the time series, a simple warning is printed.
    This is good for categories that should keep an average value: INGRESOS, CASA-ALQUILER, etc.
    """

    if category is None:
        category = ctx.selected_category
    if category not in ctx.categories_dict:
        print(f"Category '{category}' is not a valid category.")
        return
    if period is None:
        period = ctx.period
    else: 
        period = pd.Period(period, 'M')
    
    timestamp_period = period.to_timestamp()
    period_str = str(period)

    with connect(ctx.db_path) as conn:
        query_total = """
            SELECT 
                currency,
                strftime('%Y-%m', date) AS period,
                SUM(amount) as total_amount
            FROM cuentas 
            WHERE category = :category
            GROUP BY currency, period;
        """
        df = pd.read_sql(
            query_total,
            conn,
            params={"category": category},
            parse_dates={"period": {"format": "%Y-%m"}}
        )
        df.period = df.period.dt.to_period('M')

    currency_list_period = df[df.period == period_str].currency.unique()
    currency_list = df.currency.unique()

    # main plot -- not a single scatter here
    fig, ax = plt.subplots()
    for currency in currency_list:
        # https://stackoverflow.com/questions/43206554/typeerror-float-argument-must-be-a-string-or-a-number-not-period
        df_currency = df.loc[df.currency == currency, ['period', 'total_amount']].set_index('period') 
        # enumerating instead of zipping ensures that ctx.colors will be picked with no IndexErrors if len(currency_list) != len(ctx.colors)
        ax.plot(df_currency.index.to_timestamp() , df_currency.total_amount, color=ctx.colors[currency], marker='o', label=currency)

    ax.set_title(f"{category} Time Series Plot")
    ax.set_xlabel("Spendings")
    ax.set_ylabel("Dates")

    def scatter_logic(df: pd.DataFrame, currency: str, ax = None) -> None:
        # scattering red points first
        try:
            category_amount_period = df.loc[period, "total_amount"]
            ax.scatter(timestamp_period, category_amount_period, color='red', zorder=5)
            ax.axhline(category_amount_period, color='red')
            ax.text(
                timestamp_period,
                category_amount_period,
                s=f'{currency} {category_amount_period:.2f}',
                size='11',
                # I don't remember how this works, but it calibrates the placement of 'period' as a string in the plot 
                horizontalalignment = 'left' if mdates.date2num(timestamp_period) < ax.get_xlim()[1] / 2 else 'right',
                verticalalignment = 'bottom' if df["total_amount"].get(period - 1, 0) <= category_amount_period else 'top'
            )
        except KeyError:
            print(f"{currency}: Period '{period_str}' is not available for scattering in the current plot")
            return

    if len(currency_list_period) == 0:
        print(f"Period '{period_str}' does not have any records associated to {category}.")
    else:
        for currency in currency_list_period:
            df_currency = df.loc[df.currency == currency, ['period', 'total_amount']].set_index('period')
            scatter_logic(df=df_currency, currency=currency, ax=ax)  

    ax.legend()
    fig.autofmt_xdate()
    plt.show()



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
        
        dfs = [df.loc[str(ctx.period + i)] for i in range (-1,2)] # collects the three consecutive-monthly periods: [-1,0,1]
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
    ctx.period = pd.Timestamp.today().to_period('M')        
    # ctx.period = pd.Period('2025-01', 'M')                # to check a given period: pd.Period('yyyy-MM', 'M')   
    ctx.selected_category = 'INGRESO'                  # modify accordingly to fields.json
    darkmode()                                              # setting dark mode
    ctx.colors = {currency: (r / 255, g / 255, b / 255) for currency, (r, g, b) in zip(['EUR', 'USD', 'PEN'], [(128, 128, 255), (26, 255, 163), (255, 255, 255)])}

    # Uncomment the lines to run the plots
    # categories_per_period()
    # expenses_time_series()
    category_time_series(category='BLIND')
    # monthly_time_series()
    # or play with them when running python -i ...
    print("""
        functions loaded ready to be called:
            - categories_per_period()
            - expenses_time_series()
            - category_time_series()
            - monthly_time_series()
    """)