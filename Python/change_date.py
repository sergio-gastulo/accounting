import pandas as pd

csv_path = r"C:\Users\sgast\projects\Modules\accounting\files\cuentas.csv"
db_path = r"C:\Users\sgast\dbs\cuentas"


df = pd.read_csv(
    csv_path,
    header=0,
    index_col=None,
    dtype={"Category": "string","Amount":"float64","Description":"string"},
    parse_dates=["Date"],
    dayfirst=True
)

df_soles = df[~ df.Category.str.contains('USD')]
df_usd = df[df.Category.str.contains('USD')]

# df_soles.to_csv(r"files\cuentas-soles.csv",index=False)
# df_usd.to_csv(r"files\cuentas-usd.csv",index=False)
