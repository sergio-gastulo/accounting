import dotenv
from main import main as debug_main
from context.context import ctx


if __name__ == "__main__":

    config = dotenv.dotenv_values(".env")

    debug_main(
        config_path=config["CONFIG_PATH"], 
        fields_path=config["FIELDS_JSON_PATH"],
        flag='db',
    )
    
    # from db.model import Record
    # from sqlalchemy import select
    # from sqlalchemy.orm import Session

    # query = select(Record.date).limit(10)
    # with Session(ctx.engine) as session:
    #     dates = session.scalars(query)
    # for date in dates:
    #     print(f"{type(date)}: {date}") 

    from plot.plot import categories_per_period
    categories_per_period()