from acc_py.plot.plot import *
from context import main as context_main

# ------------------------------------------------------------
# Testing Instructions
#
# 1. Navigate to the package (acc_py) directory:
#        cd acc_py
# 2. Run in interactive mode with poetry:
#        poetry run pip install -e .
#        poetry run python -i ./src/acc_py/plot.py
# 3. Call the plots available.
#
# Variables to configure:
#   * period -- specify as a pandas.Period expression:
#       https://pandas.pydata.org/docs/reference/api/pandas.Period.html
#   * category
# ------------------------------------------------------------


def main() -> None:

    darkmode()
    context_main()    
    default_currency = 'EUR'

    categories_per_period()
    expenses_time_series()
    category_time_series()
    monthly_time_series(currency=default_currency)

    print("""
    functions loaded ready to be called:
    - categories_per_period(period: str | pd.Period | None = None)
    - expenses_time_series(period: str | pd.Period | None = None)
    - category_time_series(category: str = ctx.selected_category, period: str | pd.Period | None = None)
    - monthly_time_series(currency: str, period: str | pd.Period | None = None)
    """)


if __name__ == "__main__":
    main()
