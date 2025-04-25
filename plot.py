import matplotlib.pyplot as plt
import pandas as pd
import json
import matplotlib.dates as mdates

# Dark mode settings for matplotlib

def personal_settings()->None:
    '''
        Dark mode on matplotlib
    '''
    plt.style.use('dark_background')
    plt.rcParams['font.family'] = 'monospace'
    plt.rcParams['font.size'] = 12

# Loading json variables // Flattening?

temporaryList = []

with open(r'.\files\fields.json','r') as file:
    for key, value in json.load(file).items():
        shortname = value.get('shortname')
        if shortname:
            temporaryList.append([shortname, value['description']])
        else: 
            temporaryList.extend(
                [[subvalue['shortname'], subvalue['description']]for subvalue in value.values()]
            )

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
    r'.\files\cuentas.csv',
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

def plotting_categories_per_month():
    pass

def plotting_overall_expenses():
    pass

def plot_given_category_time_series():
    pass

if __name__ == '__main__':
    # Setting Dark mode
    personal_settings()

    # Plotting categories expenses per month
    plotting_categories_per_month()

    # Plotting overall expenses
    plotting_overall_expenses()

    # Simple CLI tool for plotting categories
    plot_given_category_time_series()


