import dotenv
from main import main as debug_main
from context.context import ctx


if __name__ == "__main__":

    config = dotenv.dotenv_values(".env")

    debug_main(
        config_path=config["CONFIG_PATH"], 
        fields_json_path=config["FIELDS_JSON_PATH"],
        flag='db',
        debug=True
    )

    from utilities.parser import cast_csv_types
    import pandas as pd

    df, dfe, _ =  (
                "category, description\n",
                pd.DataFrame({
                    "category" : [],
                    "description" : []
                }),
                "empty df"
            )

    df = cast_csv_types(df)
