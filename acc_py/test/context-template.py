from acc_py.context import ctx
from acc_py.context import ctx
import acc_py.plot.validate as val
from pathlib import Path
from pandas import Timestamp

def main() -> None:

    # Paths
    ctx.db_path = Path("db_path")
    ctx.json_path = Path(r"json_path")
    
    # Variables 
    ctx.categories_dict = val._get_json(ctx.json_path)
    ctx.month_es = {
        1: "Enero",
        2: "Febrero",
        3: "Marzo",
        4: "Abril",
        5: "Mayo",
        6: "Junio",
        7: "Julio",
        8: "Agosto",
        9: "Septiembre",
        10: "Octubre",
        11: "Noviembre",
        12: "Diciembre"
        }
    ctx.period = Timestamp.today().to_period('M')        
    # ctx.period = pd.Period('2025-01', 'M')                # to check a given period: pd.Period('yyyy-MM', 'M')   
    ctx.selected_category = 'EDUCATION'                     # modify accordingly to fields.json
    ctx.colors = {currency: (r / 255, g / 255, b / 255) for currency, (r, g, b) in zip(['EUR', 'USD', 'PEN'], [(128, 128, 255), (26, 255, 163), (255, 255, 255)])}


if __name__ == "__main__":

    print(
        f"db_path: {ctx.db_path}"
        f"json_path: {ctx.json_path}"
        f"categories_dict: {ctx.categories_dict}"
        f"month_es: {ctx.month_es}"
        f"period: {ctx.period}"
        f"selected_category: {ctx.selected_category}"
        f"colors: {ctx.colors}"
    )

    main()