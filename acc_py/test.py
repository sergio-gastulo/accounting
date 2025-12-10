import dotenv
from main import main as debug_main

# important: fully specify src.acc_py otherwise this won't work
from src.acc_py.context.context import ctx


if __name__ == "__main__":

    config = dotenv.dotenv_values(".env")

    debug_main(
        config_path=config["CONFIG_PATH"], 
        fields_json_path=config["FIELDS_JSON_PATH"],
        flag='plot'
    )

    from src.acc_py.plot.plot import monthly_time_series
    monthly_time_series(currency='EUR')