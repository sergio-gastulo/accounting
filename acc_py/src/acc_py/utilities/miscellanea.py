import inspect
from pandas import DataFrame
import socket
import json
from ..context.context import ctx


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


# https://stackoverflow.com/a/33117579/29272030
def has_internet(host="8.8.8.8", port=443, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        print(ex)
        return False


# function that prints the entire categories_dict nicely
# if help specified, it should print help for all available 
def pprint_categories(
        help : bool = False
) -> None:

    if not help:
        print(json.dumps(ctx.categories_dict, indent=4))
        return

    with open(ctx.field_json_path, 'r') as file:
        full_category_list = json.load(file)
    
    print_dict = {}

    for category_item in full_category_list:
        subcategory_item = category_item.get('subcategories')
        if not subcategory_item:
            print_dict.update(
                { category_item['shortname'] : category_item['help']}
            )
        else:
            for item in subcategory_item:
                print_dict.update(
                    { item['shortname'] : item['help']}
                )
    print(json.dumps(print_dict, indent=4))
