import re
from typing import Callable, TypeVar

from sqlalchemy import (TextClause,
                        true, 
                        and_,
                        select,
                        text,)
from sqlalchemy.sql.elements import BinaryExpression
from sqlalchemy.dialects import sqlite

from pkg.classes.model import Record
from pkg.coreutils.parser.dates import parse_date


T = TypeVar(name="T")
DEFAULT_SEPARATOR = "&&"

SIGNS = {
    "<": "__lt__",
    ">": "__gt__",
    ">=": "__ge__",
    "<=": "__le__",
    "=": "__eq__",
    "==": "__eq__"
}
INVERTED_SIGN = {
    "__lt__": "__gt__",
    "__gt__": "__lt__",
    "__ge__": "__le__",
    "__le__": "__ge__",
    "__eq__": "__eq__"
}


class ParseSQLError(Exception):
    pass


def ordering_query(
        query: str,
        map_: Callable = float,
) -> BinaryExpression:
    """
    Converts a totally ordered sql column and returns it parsed into a valid 
    SQLAlchemy query.
    
    Arguments
    ---------
    query
        String to be converted into a valid SQLAlchemy query.
    `map_`
        Map that converts non-column values into a valid Python expressions.
        Whenever `map_` fails, it is recommended that it fails with
        `ValueError`.
    """

    s = query.strip().lower()
    betweenpattern = re.compile(r"(?P<leftvalue>.+?)[\s]*"
                                r"(?P<leftsign>[<>=]+|between)"
                                r"[\s]*(?P<middlevalue>.+?)[\s]*"
                                r"(?:(?P<rightsign>[<>=]+|and)"
                                r"[\s]*(?P<rightvalue>.+?))?")

    if not (m := betweenpattern.fullmatch(s)):
        raise ParseSQLError(f"Argument '{s}' is not an ordering parsable query.")

    if m["leftsign"] == "between":  # between-like query
        try:
            column: BinaryExpression = getattr(Record, m["leftvalue"])
        except AttributeError:
            raise ParseSQLError(f"Not a between-like query: '{s}'.")
        left = map_(m["middlevalue"])
        right = map_(m["rightvalue"])
        return column.between(left, right)

    if (leftsign := m["leftsign"]) not in SIGNS:  # between query handled above
        raise ParseSQLError(f"Not a valid sign: '{m["leftsign"]}'.")
    leftsign = SIGNS[leftsign]

    if (rightsign := m["rightsign"]):  # a sign x sign b
        if rightsign not in SIGNS:
            raise ParseSQLError(f"Sign '{rightsign}' is not valid.")
        rightsign = SIGNS[rightsign]
        # inverting sign since "a sign x" -> "x ~sign a"
        leftsign = INVERTED_SIGN[leftsign]
        try:
            column: BinaryExpression = getattr(Record, m["middlevalue"])
        except AttributeError:
            raise ParseSQLError(f"Not an ordering query: '{s}'.")
        left = map_(m["leftvalue"])
        right = map_(m["rightvalue"])
        # int.__lt__(Record.column) fails with NotImplemented
        leftcol = getattr(column, leftsign)(left)
        rightcol = getattr(column, rightsign)(right)
        return and_(leftcol, rightcol)

    if m["rightvalue"]:
        raise ParseSQLError(f"Not a valid query: '{s}'.")

    # case x sign a or a sign x
    if hasattr(Record, colname := m["leftvalue"]):  # x > a
        column = getattr(Record, colname)
        left = map_(m["middlevalue"])
    elif hasattr(Record, colname := m["middlevalue"]):  # a < x
        column = getattr(Record, colname)
        left = map_(m["leftvalue"])
        leftsign = INVERTED_SIGN[leftsign]  # a sign x -> x ~sign a
    else:
        raise ParseSQLError(f"No valid column found in '{s}'.")

    return getattr(column, leftsign)(left)


def cleanstr(s: str | list[str]) -> str:
    """Remove quotes from text and strip it."""
    p = re.compile(r"['\"]")
    if isinstance(s, str):
        return p.sub("", s).strip()
    return p.sub("", ' '.join(s)).strip()

def string_query(
        query: str,
) -> BinaryExpression:
    """
    Converts a string-like query and returns it parsed into a valid 
    SQLAlchemy query.
    
    Arguments
    ---------
    query
        String to be converted into a valid SQLAlchemy query.
    """

    s = query.strip().split()
    colname, s = s[0], s[1:]
    try:
        column: BinaryExpression = getattr(Record, colname.lower())
    except AttributeError:
        raise ParseSQLError(f"Column {colname=!r} does not exist.")

    match s:
        case ["like" | "wildcard", *wildcard] if wildcard:
            wildcard = cleanstr(wildcard)
            return column.like(wildcard)
        
        case ["regex" | "regexp", *regex] if regex:
            regex = cleanstr(regex)
            return column.regexp_match(regex)

        case ["=" | "==" | "equal" | "equals" | "eq", *elem] if elem:
            elem = cleanstr(elem)
            return column == elem

        case [elem] if not re.match(r"(?:like|wildcard|regexp?|==?|eq(?:ual(?:s)?)?)", elem):
            elem = cleanstr(elem)
            return column == elem

        case _:
            raise ParseSQLError(
                f"Could not understand string filter: {query=!r}.")


def date_query(
        query: str
) -> BinaryExpression:
    """
    Converts a date-like query and returns it parsed into a valid 
    SQLAlchemy query.
    
    Arguments
    ---------
    query
        String to be converted into a valid SQLAlchemy query.

    Notes
    -----
    * First `ordering_query` is tried. If it fails, it goes to `string_query`.
    * Queries matching the pattern `date [= | ==] datearg` are parsed
    to `parse_date`. To pass the query as string-like, consider `[eq | equal]` 
    instead.
    """
    filterfuncs = ((ordering_query, {"map_": parse_date}),
                   (string_query, {}))

    for func, kwargs in filterfuncs:
        try:
            boolcol = func(query, **kwargs)
        except ParseSQLError:
            continue
        else:
            return boolcol

    raise ParseSQLError(f"Could not parse date query: {query=!r}.")


def sql_query(query: str):
    """
    Converts `query` into a valid SQLAlchemy query. 
    
    Arguments
    ---------
    query
        String to be converted to SQLAlchemy query.
    
    Notes
    -----
    * Depending on which keywords are found in `query`, the parsing is 
    delegated to `(?:date|ordering|string)_query`.
    * Empty and "all" | "true" like statements evaluate to true().
    """
    if Record.date.key in query:
        return date_query(query)
    if re.match(f"{Record.amount.key}|{Record.id.key}", query):
        return ordering_query(query)
    
    match query.split():
        case _, *res if res:
            return string_query(query)
        case [truelike] if re.match(r"^(?i:all|true)$", truelike) :
            return true()
        case [ ]:
            return true()
        case _:
            raise ParseSQLError(f"Could not parse {query=!r}.")


def parse_semantic_query(
        query: str,
        *,
        separator: str = DEFAULT_SEPARATOR
) -> TextClause:
    """
    Converts `query` into a valid `select * from table where ...` 
    SQLAlchemy query or plain SQL text. 
    
    Arguments
    ---------
    query
        String to be converted to SQLAlchemy query.
    separator
        Respect to what characters to split `query`. The concatenation after
        parsing is `and_`.

    Notes
    -----
    * If no `separator` is found in `query`, it will replace every `[...]`
    via `sql_query`. Then `text` is called. This is passed literally as:
    `select(Record).where(text(string))`.
    """

    if "[" in query:
        p = re.compile(r"\[(?P<insqbrackets>.*?)\]")
        dialect = sqlite.dialect()
        kwargs = dict(literal_binds=True)
        def repl(m: re.Match):
            sql = sql_query(m["insqbrackets"])
            compiled = sql.compile(dialect=dialect,
                                compile_kwargs=kwargs)
            return str(compiled)
        return select(Record).where(text(p.sub(repl, query)))
    
    pattern = re.compile(rf"[\s]*{separator}[\s]*")
    sql = (sql_query(stmt) for stmt in pattern.split(query.strip()))
    return select(Record).where(*sql)