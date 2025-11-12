import inspect
from pandas import DataFrame


def print_func_doc(func: callable) -> None:
    cyan_str = '\033[96m'
    end_str = '\033[0m'

    print(f'{cyan_str}Function name:{end_str}\n{func.__name__}\n')

    sig = inspect.signature(func)
    print(f'{cyan_str}Arguments:{end_str} {sig}\n')

    doc = func.__doc__
    print(f'{cyan_str}Documentation:{end_str}\n{doc}')



def pprint_df(
        df : DataFrame,
        header : str | None = None,
        return_flag : bool = False
) -> None | str:
    
    df.description = df.description.str[:100]
    print_df : str = df.to_markdown(
        index=True,
        tablefmt="outline"
    )
    n : int = len(print_df.partition('\n')[0])
    separator : str = "-" * n
    
    if not header:
        print_str = print_df
    else:
        print_str = (
            f"\n{separator}\n"
            f"{header}\n"
            f"{print_df}\n"
        )
        
    if return_flag:
        return print_str
    else:
        print(print_str)