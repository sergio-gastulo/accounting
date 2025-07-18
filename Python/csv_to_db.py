import pandas as pd
import sqlite3

db_path = r"C:\Users\sgast\dbs\cuentas"
conn = sqlite3.connect(db_path)

cursor = conn.cursor()

csv_path = r"C:\Users\sgast\projects\Modules\accounting\files\cuentas-usd.csv"


with open(r"C:\Users\sgast\projects\Modules\accounting\SQL\feed.sql", 'r') as file:
    sql_script = file.read()


df_usd = pd.read_csv(
    csv_path,
    names=["date", "amount", "description", "category"],
    index_col=None,
    dtype={"category": "string","amount":"float64","description":"string"},
    parse_dates=["date"]
)

cursor.executemany(
    sql_script,
    [(
        row['date'].date().isoformat(), 
        row['amount'], 
        row['description'], 
        row['category'].replace("-USD","")
        ) for _, row in df_usd.iterrows()]
)

conn.commit()
conn.close()