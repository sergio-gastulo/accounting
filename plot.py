import matplotlib.pyplot as plt
import pandas as pd
import json
import matplotlib.dates as mdates
import sys

# Dark mode settings for matplotlib

CSVPATH = sys.argv[1]
JSONPATH = sys.argv[2]

def personal_settings()->None:
    '''
        Dark mode on matplotlib
    '''
    plt.style.use('dark_background')
    plt.rcParams['font.family'] = 'monospace'
    plt.rcParams['font.size'] = 12

# Loading json variables // Flattening?

temporaryList = []

with open(JSONPATH,'r') as file:
    for key, value in json.load(file).items():
        shortname = value.get('shortname')
        if shortname:
            temporaryList.append([shortname, value['description']])
        else: 
            temporaryList.extend(
                [[subvalue['shortname'], subvalue['description']]for subvalue in value.values()]
            )

readableJSON = dict(temporaryList)

# Dictionary for months in spanish

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

# Importing CSV file from files/cuentas.csv

rawCSV = pd.read_csv(
    CSVPATH,
    header=0,
    index_col=None,
    dtype={"Category": "string","Amount":"float64","Description":"string"},
    parse_dates=["Date"],
    dayfirst=True
    )

# Converting USD to PEN

dolarToSoles = 3.76
rawCSV.loc[rawCSV.Category == 'INGRESO-USD','Amount'] *= dolarToSoles
rawCSV.loc[rawCSV.Category == 'INGRESO-USD','Category'] = 'INGRESO-SOLES'


# Plotting categories expenses per month

def plotting_categories_per_month(year: int, month: int) -> None: 
    period = f'{year}-{month}'
    tempdf = rawCSV.groupby([rawCSV.Date.dt.to_period('M'),'Category']).Amount.sum()[period]
    tempdf = tempdf[~tempdf.index.isin(['BLIND','INGRESO-SOLES'])]
    fig, ax = plt.subplots()

    tempMax = max(tempdf.values)

    bars = ax.barh(
        [readableJSON[key] for key in tempdf.index],  
        tempdf.values,  
        height=0.8,
        color=(1,1,1)
        )

    ax.tick_params(
        axis='y',
        labelsize=10
    )

    for bar in bars:
        width = bar.get_width()
        y = bar.get_y() + bar.get_height() / 2
        ax.text(
            (0.5 if tempMax / 2 < width else 1.1) * width,
            y,
            f'{width:.2f}',
            va='center',
            ha='left',
            fontsize=10,
            color = (0,0,0) if tempMax / 2 < width else (1,1,1)
        )

    ax.set_title(
        label=f'Gastos registrados al {months_es[month]} del {year}:\nPEN {sum(tempdf.values):.2f}',
        pad=20,
        loc='center',
        y = 1.0
        )

    ax.set_xlabel('Gastos', labelpad=8.0)
    ax.set_ylabel('Categories', labelpad=16.0)

    plt.show()





def plotting_overall_expenses(year: int, month: int) -> None:
    periodString = f'{year}-{month}'
    df = rawCSV[~rawCSV.Category.isin(['BLIND','INGRESO-SOLES','SOLES-USD','USD-SOLES'])]
    temp = df.groupby(df.Date.dt.to_period('M')).Amount.sum()

    fig, ax = plt.subplots()


    ax.plot(
        temp.index.to_timestamp(), 
        temp.values, 
        marker='o',
        color=(1,1,1),
        )

    ax.scatter(
        pd.to_datetime(periodString),
        temp[periodString],
        color=(1,0,0),
        zorder=5
    )

    ax.text(
        pd.to_datetime(periodString) + pd.Timedelta(days=10),
        1.05 * temp[periodString],
        s=f'PEN {temp[periodString]:.2f}',
        size='11'
    )

    ax.axhline(
        temp[periodString],
        color=(1,0,0)
    )

    ax.set_title('Gastos realizados por mes', pad=20)
    ax.set_xlabel('Fecha', labelpad=16.0)
    ax.set_ylabel('Gastos', labelpad=16.0)

    fig.autofmt_xdate()
    plt.show()



def plot_given_category_time_series(category: str) -> None:
    temp = rawCSV[rawCSV.Category==category].groupby(rawCSV.Date.dt.to_period('M')).Amount.sum()
    fig, ax = plt.subplots()

    todayPeriod = pd.Timestamp.today().to_period('M').__str__()
    tempValues = temp.values

    line = ax.plot(
        temp.index.to_timestamp(),
        tempValues,
        color=(1,1,1),
        marker='o'
    )

    try: 
        givenValue = temp[todayPeriod]
        tempDate = pd.to_datetime(todayPeriod)

        ax.scatter(
            tempDate,
            givenValue,
            color=(1,0,0),
            zorder=5
        )

        ax.text(
            tempDate,
            givenValue,
            s=f'PEN {givenValue:.2f}',
            size='11',
            horizontalalignment='left' if mdates.date2num(tempDate) < ax.get_xlim()[1] / 2 else 'right',
            verticalalignment='bottom' if temp[(pd.Timestamp.today() - pd.DateOffset(months=1)).strftime('%Y-%m')] <= givenValue else 'top'
        )

        ax.axhline(
            givenValue,
            color=(1,0,0)
        )

        
    except:
        print(f'Period \'{todayPeriod}\' not found on plot.')



    ax.set_title(f'Gasto mensual de: {readableJSON[category]}',pad=16.0)

    ax.set_ylabel('Gasto en PEN',labelpad=16.0)
    ax.set_xlabel('Periodos',labelpad=16.0)

    fig.autofmt_xdate()
    plt.show()


def plot_consecutive_time_series()->None:
    dfYearMonth = rawCSV[
    ~rawCSV.Category.isin(['BLIND','INGRESO-SOLES','SOLES-USD','USD-SOLES'])
    ].groupby([rawCSV.Date.dt.to_period('D')]).Amount.sum()
    period = pd.Timestamp.today().to_period('M')
    dfs = [dfYearMonth.get((period + i).__str__(), pd.Series(dtype='float64')) for i in range (-1,2)]

    fig, ax = plt.subplots(1,2, figsize=(12,5))

    for i, dframes in enumerate(dfs):

        tempColor = (1,1,1) if i!=1 else (0,1,0)

        ax[0].plot(
            dframes.index.to_timestamp(),
            dframes.values,
            marker='o',
            color=tempColor,
        )

        ax[1].plot(
            dframes.index.to_timestamp(),
            dframes.values.cumsum(),
            color= tempColor,
            marker='o'
        )

    for axes in ax:
        axes.axvline(
            mdates.date2num(pd.Timestamp.today().to_period('D')),
            color=(1,0,0)
        )


    fig.suptitle(f'Grafico del gasto mensual centrado en {months_es[period.month]} del {period.year}', fontsize=12)

    fig.supxlabel('Periodos',y=-0.1)
    fig.supylabel('Gasto en PEN',x=0.05)

    fig.autofmt_xdate()
    plt.show()



if __name__ == '__main__':
    # Setting Dark mode
    personal_settings()

    # Plotting categories expenses per month
    plotting_categories_per_month(2025, 4)

    # Plotting overall expenses
    plotting_overall_expenses(2025, 4)

    # Simple CLI tool for plotting categories
    plot_given_category_time_series('BLIND')

    # Different growth of different Time Series
    plot_consecutive_time_series()