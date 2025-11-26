from acc_py.context.context import ctx
from acc_py.context.main import set_context
import dotenv
from acc_py.plot.plot import darkmode
from pprint import pprint


TESTING_PLOT = False
NEED_CONTEXT = True


def main() -> None:
    if NEED_CONTEXT:
        config = dotenv.dotenv_values(".env")
        set_context(
            config_path=config["CONFIG_PATH"], 
            fields_json_path=config["FIELDS_JSON_PATH"],
            plot=TESTING_PLOT
        )
        if TESTING_PLOT:
            darkmode()

    else:
        print("Context has been imported but not set.")


if __name__ == "__main__":
    main()
    from acc_py.context.utils import check_colors
    colors = []
    curr_list = ["eur", "usd", "pen"]
    c = check_colors(color_list=colors,  currency_list=curr_list)
    pprint(c)