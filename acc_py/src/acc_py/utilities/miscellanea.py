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
        header : str
):
    print_df : str = df.to_markdown(
        index='id',
        tablefmt="outline"
        )
    
    n : int = len(print_df.partition('\n')[0])
    separator : str = "-" * n

    print(
        f"\n{separator}\n"
        f"{header}\n"
        f"{print_df}\n"
    )