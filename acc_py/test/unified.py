from acc_py.context import ctx
from acc_py.context.main import set_context
import dotenv   
from pprint import pprint
import os




# module to test
# from acc_py.db.db_api import *
from acc_py.utilities.core_parser import parse_semantic_filter
# from acc_py.utilities.miscellanea import print_func_doc
# from acc_py.plot.plot import *

TEST_PLOT = False


def main() -> None:
    config = dotenv.dotenv_values(".env")
    set_context(
        db_path=config["DB_PATH"], 
        json_path=config["JSON_PATH"],
        plot=TEST_PLOT
    )

    if TEST_PLOT:
        # darkmode()
        pass



if __name__ == "__main__":
    c = lambda : os.system('cls')
    main()