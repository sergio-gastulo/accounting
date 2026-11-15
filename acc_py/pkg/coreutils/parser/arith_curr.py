import re

DEFAULT_LOWER_BOUND = 0.


def parse_arithmetic_operation (
        expr: str, 
        lbound: float | int = DEFAULT_LOWER_BOUND
) -> float | int:
    """
    Convert `expr` into a valid `float` (or `int`).
    Relies on regex to remove any python injection, checks lower bounds, 
    and evals with no builtins.

    Arguments

    expr:
        String to be parsed.
    lbound:
        Lower bound.

    Examples
--
    >>> parse_arithmetic_operation("+1+1")
    2
    >>> parse_arithmetic_operation("+5-6", -999)
    -1
    """

    # prevent python injection
    if re.match(r'.*[a-zA-Z].*', expr):
        raise ValueError(f"Input can't contain words. Got: {expr=}.")
    if len(expr) == 0:
        raise ValueError(f"Empty string.")

    # removing '=' from the beginning of the str
    if expr[0] in ['+', '=', '-']:
        expr = re.sub('^=', '', expr)
        try:
            value = eval(expr, {"__builtins__": {}})
        except SyntaxError:
            raise ValueError(f"Expression {expr} failed python parsing.")
    # assuming a simple float if above fails
    else:
        value = float(expr)  # if it fails leave it as ValueError

    if value < lbound:
        raise ValueError(f"Value {value} must be greater than {lbound=}.")
    return value


def parse_currency(currency: str) -> str:
    """
    Checks if `currency` is a 3-word-length `str` and returns it 
    in uppercase. 
    """
    currency = currency.strip().upper()
    if re.match(r'^[A-Z]{3}$', currency):
        return currency

    raise ValueError(f"{currency=} is not a valid currency.")


def parse_double_currency(
        rawinput: str, 
        default_currency: str,
        lbound: float = DEFAULT_LOWER_BOUND,
) -> tuple[float, str]:
    """
    Converts `rawinput` into a valid `(amount, currency)` pair.
    """

    tokens = rawinput.strip().split()
    if not tokens:
        raise ValueError("Empty query.")

    try:
        # check if last splitted string is currency
        currency = parse_currency(tokens[-1])
        raw_op = ' '.join(tokens[:-1])  
    except ValueError:
        # if above fails, more likely it was a single arith op
        currency = parse_currency(default_currency)
        raw_op = ' '.join(tokens)
        
    amount = parse_arithmetic_operation(raw_op, lbound)
    return amount, currency