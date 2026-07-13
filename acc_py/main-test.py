import sys
import dotenv

from sqlalchemy import create_engine

from pkg.classes import ctx

from main import main


if __name__ == "__main__":

    config = dotenv.dotenv_values(".env")
    flag = 'plot'

    # awkward but this works so ...
    sys.argv.append(config["CONFIG_PATH"])
    sys.argv.append(config["FIELDS_JSON_PATH"])
    sys.argv.append(flag)
    main()
    ctx.engine = create_engine(config["DB_PATH"])

    from pkg.interfaces.db_api import fetch, write_record, read
    
    # df = fetch(max_lines=20)
    # df = df[df["category"].isin(ctx.categories_dict) & df["amount"] > 0].copy()
    # df["description"] += " -- test2"
    # write_record(df)
    