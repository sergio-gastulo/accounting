from acc_py.context.context import ctx
from acc_py.context.main import set_context
import dotenv
from acc_py.plot.plot import darkmode
from pprint import pprint


TESTING_PLOT = True
NEED_CONTEXT = True


if __name__ == "__main__":

    config = dotenv.dotenv_values(".env")

    from ..main import main as debug_main

    debug_main(
        config_path=config["CONFIG_PATH"], 
        fields_json_path=config["FIELDS_JSON_PATH"],
        plot=TESTING_PLOT
    )
