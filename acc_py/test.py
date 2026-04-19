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

    from utilities.core_parser import *
    parse_valid_element_list(
        user_input = "value",
        keybinds = {
            "key" : "value",
            "key2" : "value2",
            "weird" : "weird value"
        }
    )