import sys
import dotenv

from sqlalchemy import create_engine

from pkg.classes.context import ctx
from main import main


if __name__ == "__main__":

    config = dotenv.dotenv_values(".env")
    flag = "db"

    # awkward but this works so ...
    sys.argv.append(config["CONFIG_PATH"])
    sys.argv.append(config["FIELDS_JSON_PATH"])
    sys.argv.append(flag)
    main()
    ctx.engine = create_engine(config["DB_PATH"])  # testing

    # from pkg.classes.model import Record
    # rec = Record.get(2000)
    # rec.category = "SDFDSFDS"
    # rec.validate()

    from pkg.interfaces.db.dataframe import fetch

    df = fetch("category like %CASA%")