from acc_py.utilities.prompt import *
from context import main  as context_main
from context import ctx

def main() -> None:
    context_main()

if __name__ == "__main__":
    main()
    prompt_record_by_id(ctx.engine)