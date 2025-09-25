from acc_py.context import ctx
from acc_py.context.main import set_context
import dotenv   
from pprint import pprint
import os
from acc_py.plot.plot import darkmode

from acc_py.plot.plot import sum_currencies

TESTING_PLOT = True
NEED_CONTEXT = True


def main() -> None:
    if NEED_CONTEXT:
        config = dotenv.dotenv_values(".env")
        set_context(
            db_path=config["DB_PATH"], 
            json_path=config["JSON_PATH"],
            plot=TESTING_PLOT
        )
        if TESTING_PLOT:
            darkmode()

    else:
        print("Context has been imported but not set.")


if __name__ == "__main__":
    main()
    c = lambda : os.system('cls')
    import numpy as np
    test = {'pen': np.float64(52.43), 'usd': np.float64(264.63), 'eur': np.float64(168.13000000000002)}
    sum_currencies(test)