from acc_py.interface.interface import *
from context import main as context_main
from context import ctx

def main()->None:
    context_main()
    print(ctx.engine)


if __name__ == "__main__":
    main()
    write_list()