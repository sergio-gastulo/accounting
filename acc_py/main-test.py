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
    from pkg.interfaces.independent import fopen
    fopen("/acccli/acc_py/pkg/interfaces")
    fopen("/acc_py/pkg/interfaces")
    fopen("here")