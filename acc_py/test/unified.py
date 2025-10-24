from acc_py.context import ctx
from acc_py.context.main import set_context
import dotenv
from acc_py.plot.plot import darkmode
from acc_py.db.db_api import read

TESTING_PLOT = False
NEED_CONTEXT = True


def main() -> None:
    if NEED_CONTEXT:
        config = dotenv.dotenv_values(".env")
        set_context(
            # db_path=config["DB_TEST_PATH"], 
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
    read()