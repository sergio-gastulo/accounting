import dotenv
from main import main
from pkg.classes.context import ctx
import sys

if __name__ == "__main__":

    config = dotenv.dotenv_values(".env")
    flag = 'plot'

    # awkward but it works
    sys.argv.append(config["CONFIG_PATH"])
    sys.argv.append(config["FIELDS_JSON_PATH"])
    sys.argv.append(flag)
    main()
    from pkg.interfaces.plot.barchart import fetch_barchart_data
    from pkg.interfaces.plot.barchart import barchart_by_datefilter
    from datetime import date
    date1 = date(2020, 10, 12)
    date2 = date(2020, 11, 12)
    res = fetch_barchart_data([date1, date2])
    # barchart_by_datefilter()