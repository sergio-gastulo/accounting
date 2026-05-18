import dotenv
from main import main
from context.context import ctx
import sys

if __name__ == "__main__":

    config = dotenv.dotenv_values(".env")
    flag = 'plot'

    # awkward but it works
    sys.argv.append(config["CONFIG_PATH"])
    sys.argv.append(config["FIELDS_JSON_PATH"])
    sys.argv.append(flag)
    main()

    from db.db_api import _render_template
    fixed_fields = {
        "date" : "foobarbaz",
        "category": "anotherfoo",
        "currency": "usd"
    }
    print(_render_template(**fixed_fields))