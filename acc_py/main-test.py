import sys
import dotenv

from pkg.classes.context import ctx
from sqlalchemy import create_engine

from main import main


if __name__ == "__main__":

    config = dotenv.dotenv_values(".env")
    flag = 'db'

    # awkward but this works so ...
    sys.argv.append(config["CONFIG_PATH"])
    sys.argv.append(config["FIELDS_JSON_PATH"])
    sys.argv.append(flag)
    main()
    ctx.engine = create_engine(config["DB_PATH"])  # testing


    from pkg.interfaces.db_api import fetch
    from sqlalchemy import select
    from pkg.interfaces.db.sql import parse_semantic_query
    from sqlalchemy.dialects import sqlite
    from pkg.classes.model import Record

    kw = dict(dialect=sqlite.dialect(),
              compile_kwargs={"literal_binds": True})
    expected = select(Record).where(Record.description.like('%uten%'))
    ecompiled = str(expected.compile(**kw))
    df = fetch("description like %uten%")
    df.head(5)