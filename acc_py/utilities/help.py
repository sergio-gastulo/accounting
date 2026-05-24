def acccli():
    """
    Interactive REPL Python-backed.

    Independently, the following file-based operations and miscellanea has been
    loaded:
    [now, fexport, fimport, fopen, pdate]

    The available DB management functions are available:
        "br": da.build_record,
        "bc": da.build_conversion,
        "bdf": da.build_df,
        "e": da.edit,
        "fetch": da.fetch,
        "d": da.delete,
        "r": da.read,
        "w": da.write_record,
        "gr": da.get_record,
        "wc": da.write_conversion,
        "wdf": da.write_df,
        "Record": Record,
        "Conversion": Conversion,
    
    The available plotting functions are available:
        "p1": pp.categories_per_period, 
        "p2": pp.expenses_time_series, 
        "p3": pp.category_time_series, 
        "sp": pp.savings_plot, 

    * Depending on the loaded module, "load" will import it's complement if 
    required.
    * To check which functions you have available, feel free to evaluate 
    get_globals().
    * Evaluate acccli() to print this message again.
    """
    print(acccli.__doc__)