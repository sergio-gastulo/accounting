from context import ctx
from context import main as context_main
import sys
from pathlib import Path

from acc_py.utilities.core_parser import *
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from acc_py.db.model import Record


if __name__ == "__main__":
    df = parse_csv_record(Path(sys.argv[1]))
    print(df.head())