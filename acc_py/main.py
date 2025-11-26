import sys
from pathlib import Path
from src.acc_py.context.context import ctx
from os import system
from src.acc_py.utilities.miscellanea import pprint_categories as pc


# populate globals accordingly
def plot(config_path : Path, field_json_path : Path) -> None:
    import src.acc_py.interface.plot_interface as pi
    globals()["p1"]  = pi.categories_per_period
    globals()["p2"]  = pi.expenses_time_series
    globals()["p3"]  = pi.category_time_series
    globals()["p4"]  = pi.monthly_time_series
    globals()["h"]   = pi.h
    pi.run(config_path=config_path, field_json_path=field_json_path) 


# populate globals accordingly
def db(config_path : Path, field_json_path : Path) -> None:
    
    import src.acc_py.interface.db_interface as dbi
    globals()["e"]  = dbi.edit
    globals()["d"]  = dbi.delete
    globals()["w"]  = dbi.write
    globals()["wl"] = dbi.write_list
    globals()["wc"] = dbi.write_conversion
    globals()["rc"] = dbi.read_conversion
    globals()["r"]  = dbi.read
    globals()["h"]  = dbi.h
    globals()["el"] = dbi.edit_list
    dbi.run(config_path=config_path, field_json_path=field_json_path)


def main(config_path : Path, field_json_path : Path, flag : str) -> None:
	
    globals()["c"] = lambda : system('cls')

    if flag == 'plot':
        plot(config_path, field_json_path)
        globals()["h_plot"] = globals()["h"]
        globals()["load_db"] = lambda : db(config_path, field_json_path)

    elif flag == 'db':
        db(config_path, field_json_path)
        globals()["h_db"] = globals()["h"]
        globals()["load_plot"] = lambda : plot(config_path, field_json_path)

    else:
        print(f"'{flag}' is not a valid interface flag.")


if __name__ == "__main__":
    
    main(
        config_path=sys.argv[1],
        field_json_path=sys.argv[2],
        flag=sys.argv[3]
    )
