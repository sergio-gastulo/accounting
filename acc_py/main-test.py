import dotenv
from main import main
from pkg.classes import ctx, Record
import sys
from tests._shared import mem_engine, TODAY
from pkg.utilities.parser import parse_record_from_id


if __name__ == "__main__":

    config = dotenv.dotenv_values(".env")
    flag = 'plot'

    # awkward but it works
    sys.argv.append(config["CONFIG_PATH"])
    sys.argv.append(config["FIELDS_JSON_PATH"])
    sys.argv.append(flag)
    main()

    engine = mem_engine()

    record = Record(date=TODAY,
                    amount=0.65,
                    currency="foo",
                    description="foo",
                    category = "foo")
    record.write(engine, quiet=True)

    uinput = 1
    res = parse_record_from_id(uinput, engine, Record)
    res == record