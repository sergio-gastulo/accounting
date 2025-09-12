from acc_py.db.write import *
import datetime
from decimal import Decimal
from context import main as context_main

from sqlalchemy.orm import Session
from sqlalchemy import text

context_main()

with Session(ctx.engine) as session:
    record = Record(
        date = datetime.date(2025,9,29),
        amount=Decimal("123.54"),
        currency="EUR",
        description="foo barsdfdsfds",
        category="EXCHANGE"
    )

    session.add(record)
    session.commit()
    print("log?????")
    result = session.execute(text("SELECT * FROM cuentas WHERE date LIKE '2025-09%'"))
    print(result.all())