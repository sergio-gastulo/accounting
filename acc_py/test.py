import dotenv
from main import main as debug_main

# important: fully specify src.acc_py otherwise this won't work
from src.acc_py.context.context import ctx


if __name__ == "__main__":

    config = dotenv.dotenv_values(".env")

    debug_main(
        config_path=config["CONFIG_PATH"], 
        fields_json_path=config["FIELDS_JSON_PATH"],
        flag='plot',
        debug=True
    )

    from src.acc_py.db.db_api import *

    # print(sum_currencies({
    #     "pen" : 5.6,
    #     "usd" : 894
    # }))