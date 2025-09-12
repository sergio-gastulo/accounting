from context import ctx
from context import main as context_main
import sys
from pathlib import Path

from acc_py.utilities.core_parser import *
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from acc_py.db.model import Record


if __name__ == "__main__":
    engine = create_engine(f"sqlite:///{Path(sys.argv[1]).resolve()}")
    print(engine)
    context_main()
    stmt = select(Record).where(Record.description.regexp_match("tty"))
    with Session(engine) as session:
        res = session.execute(stmt)
        print(res.fetchone())
