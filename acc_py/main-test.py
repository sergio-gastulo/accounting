import sys
import dotenv

from pkg.classes.context import ctx

from main import main


if __name__ == "__main__":

    config = dotenv.dotenv_values(".env")
    flag = 'db'

    # awkward but this works so ...
    sys.argv.append(config["CONFIG_PATH"])
    sys.argv.append(config["FIELDS_JSON_PATH"])
    sys.argv.append(flag)
    main()
    # ctx.engine = create_engine(config["DB_PATH"])