import sys
from pathlib import Path
from src.acc_py.context.context import ctx
from os import system


def plot(db_path : Path, json_path : Path) -> None:
    import src.acc_py.interface.plot_interface as pi
    globals()["p1"]  = pi.categories_per_period
    globals()["p2"]  = pi.expenses_time_series
    globals()["p3"]  = pi.category_time_series
    globals()["p4"]  = pi.monthly_time_series
    globals()["h"]   = pi.h
    pi.run(db_path=db_path, json_path=json_path) 


def db(db_path : Path, json_path : Path) -> None:
    import src.acc_py.interface.db_interface as dbi
    globals()["e"]  = dbi.edit
    globals()["d"]  = dbi.delete
    globals()["w"]  = dbi.write
    globals()["wl"] = dbi.write_list
    globals()["r"]  = dbi.read
    globals()["h"]  = dbi.h
    globals()["el"]  = dbi.edit_list
    dbi.run(db_path=db_path, json_path=json_path)


def main(db_path : Path, json_path : Path, flag : str) -> None:
	
    globals()["c"] = system('cls')

    if flag == 'plot':
        plot(db_path, json_path)
        globals()["db"] = lambda : db(db_path, json_path)

    elif flag == 'db':
        db(db_path, json_path)
        globals()["plot"] = lambda : plot(db_path, json_path)

    else:
        print(f"'{flag}' is not a valid interface flag.")


if __name__ == "__main__":
    
    main(
        db_path=sys.argv[1],
        json_path=sys.argv[2],
        flag=sys.argv[3]
    )
