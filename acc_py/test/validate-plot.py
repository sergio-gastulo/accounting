from context import main as cmain
from context import ctx
import acc_py.plot.validate as val

def main() -> None:
    instructions = """
        [TEST MODE]
        'ctx.categories' variable loaded.
        'ctx.period' variable loaded.
        Functions available in validadte.py:
            - val._get_json(json_path: Path) -> dict[str, str]
            - val._get_period(default_period: Period) -> Period
            - val._get_category(dict_cat: dict[str, str])
            - val._doc_printer(func: callable) -> None
"""
    cmain() # setting variables
    print(
        "Arguments waiting for validation:"
        f"json_path: {ctx.json_path}"
        f"period: {ctx.period}"
        f"categories_dict: {ctx.categories_dict}"
        f"{instructions}"
    )

if __name__ == "__main__":
    main()