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

    from utilities.prompt import prompt_column_value
    res = prompt_column_value(ctx.keybinds)
    print(res)