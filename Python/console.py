import sys
import pandas as pd
import json
import matplotlib.pyplot as plt

def set_darkmode() -> None:
    plt.style.use('dark_background')
    plt.rcParams['font.family'] = 'monospace'
    plt.rcParams['font.size'] = 12


def load_json(json_path: str) -> dict[str, str]:
    """
    Loads JSON from `path` and returns the JSON parsed as follows:
    * The pattern `key: {sname, description}` is mapped to `sname: description`
    * The pattern `key: {skey1: {sname, desc}, skey2: {sname, desc}}` is mapped to `sname1: desc1, sname2, desc2` (flattened)
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


def load_csv(csv_path: str) -> pd.DataFrame:
    """
    Loads a dataframe from `path`. 
    """
    usd_pen = 3.67
    raw_csv = pd.read_csv(
        csv_path,
        header=0,
        index_col=None,
        dtype={"Category": "string","Amount":"float64","Description":"string"},
        parse_dates=["Date"],
        dayfirst=True
        )
    raw_csv.loc[raw_csv.Category == 'INGRESO-USD','Amount'] *= usd_pen
    raw_csv.loc[raw_csv.Category == 'INGRESO-USD','Category'] = 'INGRESO-SOLES'

    return raw_csv


# 
# Main script
# 

if __name__ == "__main__":
        try:
            csv_path = sys.argv[1]
        except IndexError:
            print("Something went wrong during the csv_path call.")
            print("Enter the path (if possible, non-relative) of the CSV: ")
            csv_path = input()
    
        df = load_csv(csv_path)

        try: 
            json_path = sys.argv[2]
        except IndexError:
            print("Something went wrong during the json_path call.")
            print("Enter the path (if possible, non relative) of the JSON")
            json_path = input()

        categories = load_json(json_path)

        print("The variables 'df' and 'categories' were loaded to kernel. Feel free to filter and play as desired.")

