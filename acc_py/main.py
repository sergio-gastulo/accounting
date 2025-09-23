import sys
from pathlib import Path
from src.acc_py.context.context import ctx


def main(db_path : Path, json_path : Path, flag : str) -> None:

    if flag == 'plot':
        import src.acc_py.interface.plot_interface as pi
        globals()["p1"]  = pi.categories_per_period
        globals()["p2"]  = pi.expenses_time_series
        globals()["p3"]  = pi.category_time_series
        globals()["p4"]  = pi.monthly_time_series
        globals()["h"]   = pi.h
        pi.run(db_path=db_path, json_path=json_path) 

    elif flag == 'db':
        import src.acc_py.interface.db_interface as dbi
        globals()["e"]  = dbi.edit
        globals()["d"]  = dbi.delete
        globals()["w"]  = dbi.write
        globals()["wl"] = dbi.write_list
        globals()["r"]  = lambda *n_lines, **kwargs : dbi.read(*n_lines, **kwargs)
        globals()["h"]  = dbi.h
        globals()["el"]  = dbi.edit_list
        dbi.run(db_path=db_path, json_path=json_path)

    else:
        print(f"'{flag}' is not a valid interface flag.")


if __name__ == "__main__":
    
    main(
        db_path=sys.argv[1],
        json_path=sys.argv[2],
        flag=sys.argv[3]
    )