import sys
import dotenv

from sqlalchemy import create_engine

from pkg.classes import ctx

from main import main


if __name__ == "__main__":

    config = dotenv.dotenv_values(".env")
    flag = 'plot'

    # awkward but this works so ...
    sys.argv.append(config["CONFIG_PATH"])
    sys.argv.append(config["FIELDS_JSON_PATH"])
    sys.argv.append(flag)
    main()
    # ctx.engine = create_engine(config["DB_PATH"])

    from pkg.interfaces.db_api import fetch
    from pkg.interfaces.plot.timeseries import plot
    from pkg.interfaces.plot.categoryts import (fetch_category_ts_data,
                                                get_freq_configs, 
                                                category_time_series)
    from pkg.interfaces.plot.savings import fetch_savings_data
    from pkg.interfaces.plot.scatter import fetch_outflow_data, scattered_outflow
    import matplotlib.pyplot as plt


    # scatter.py
    # df = fetch_outflow_data()
    # df.rename({"total_amount": "amount"})
    # df.index.rename({"period": "date"}, inplace=True)
    scattered_outflow()


    # plottable, but still needs renaming



