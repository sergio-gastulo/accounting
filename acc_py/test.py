import dotenv
from main import main as debug_main

# important: fully specify src.acc_py otherwise this won't work
from src.acc_py.context.context import ctx


if __name__ == "__main__":

    config = dotenv.dotenv_values(".env")

    debug_main(
        config_path=config["CONFIG_PATH"], 
        fields_json_path=config["FIELDS_JSON_PATH"],
        flag='db',
        debug=True
    )

    from src.acc_py.utilities.core_parser import sanitize_df
    from src.acc_py.db.db_api import read
    df = read(semantic_filter="", verbose=False)
    print(df.head())
    # df.drop("date", axis=1, inplace=True)
    # df.iloc[0, 1] = -5.5
    # df.iloc[0, -1] = "HELLO-WORLD"
    df2 = sanitize_df(df, category_dict=ctx.categories_dict)