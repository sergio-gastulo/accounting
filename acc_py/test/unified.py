from acc_py.context import ctx
from acc_py.context.main import set_context
import dotenv
from acc_py.plot.plot import darkmode


TESTING_PLOT = True
NEED_CONTEXT = True


def main() -> None:
    if NEED_CONTEXT:
        config = dotenv.dotenv_values(".env")
        set_context(
            # db_path=config["DB_TEST_PATH"], 
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
    from acc_py.plot.plot import pprint_df
    import pandas as pd
    df = pd.DataFrame({"description": list("jksla")}, index=list("abcde"))
    pprint_df(df)