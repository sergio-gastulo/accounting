from acc_py.write.validate import *
from context import main  as context_main


v1 = validate_arithmetic_operation
v2 = validate_currency
v3 = validate_date_operation
v4 = validate_both_double_currency


def main() -> None:
    help_str = """
    functions for help:
        v1 = validate_arithmetic_operation
        v2 = validate_currency
        v3 = validate_date_operation
        v4 = validate_both_double_currency
"""
    print(help_str)
    context_main()


if __name__ == "__main__":
    main()
    v4()