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
    from db.model import Conversion
    from datetime import date
    from db.db_api import write_conversion

    conv = Conversion(
        date=date(2026,4,12),
        base_currency='USD',
        base_amount=620,
        target_currency='EUR',
        target_amount=500,
        description="switie get up"
    )