import re
from typing import Callable, TypeVar

from sqlalchemy import (TextClause,
                        Engine,
                        true, 
                        and_,
                        select,
                        text,)
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from pkg.classes.model import Record

from .dates import parse_date


T = TypeVar(name="T")

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
}


class ParseSQLError(Exception):
    pass


def ordering_filter(
        filter_: str,
        map_: Callable = float,
) -> ColumnElement[bool]:
    """
    Converts a totally ordered column sql and returns it parsed into a valid 
    SQLAlchemy query.
    
    Arguments
    ---------
    filter
        String to be converted into a valid SQLAlchemy query.
    map_
        Map that converts non-column values into a valid Python expressions.
    """

    s = filter_.strip().lower()
    betweenpattern = re.compile(r"(?P<leftvalue>.+?)[\s]*"
                                r"(?P<leftsign>[<>=]+|between)"
                                r"[\s]*(?P<middlevalue>.+?)[\s]*"
                                r"(?:(?P<rightsign>[<>=]+|and)"
                                r"[\s]*(?P<rightvalue>.+?))?")

    if not (m := betweenpattern.fullmatch(s)):
        raise ParseSQLError(f"Argument '{s}' is not an ordering parsable query.")

    if m["leftsign"] == "between":  # between-like query
        try:
            column: ColumnElement = getattr(Record, m["leftvalue"])
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
        # invertings since a sign x -> x ~sign a
        leftsign = INVERTED_SIGN[leftsign]  
        try:
            column: ColumnElement = getattr(Record, m["middlevalue"])
        except AttributeError:
            raise ParseSQLError(f"Not a ordering query: '{s}'.")
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



def string_filter(
        filter_: str,
        colname: str,
) -> ColumnElement[bool]:
    """Filter a string column, including wildcards (% %) and regex."""

    column: ColumnElement = getattr(Record, colname)
    match filter_.split():
        case [colname, "like", *wildcard]:
            wildcard = (' '.join(wildcard)
                        .replace("'", "")
                        .replace('"', ''))
            return column.like(wildcard)
        
        case [colname, "=" | "equal" | "equals" | "eq", elem] | [colname, elem]:
            return column == elem

        case [colname, "r" | "regex" | "regexp", *regex]:
            regex = ' '.join(regex)
            return column.regexp_match(regex)

        case _:
            raise ValueError(
                f"Could not understand string filter: {filter_=!r}.")


def date_filter(
        filter_: str,
        colname: str
) -> ColumnElement[bool]:
    """Filter by date, as a string or with datetime arithmetic."""
    filterfuncs = ((ordering_filter, {"map_": parse_date}),
                   (string_filter, {}))

    for func, kwargs in filterfuncs:
        try:
            boolcol = func(filter_, colname, **kwargs)
        except ValueError:
            continue
        else:
            return boolcol

    raise ValueError(f"Could not parse date query: {filter_=!r}.")



def sql_filter(filter_: str):
    """
    Parses a single sql statement into a semantically-valid SQL query 
    and returns it. The query is not validated, only parsed.
    """
    if Record.date.key in filter_:
        return date_filter(filter_, Record.date.key)
    if Record.amount.key in filter_:
        return ordering_filter(filter_, Record.amount.key, float)
    
    match filter_.split():
        case [Record.description.key | 
              Record.currency.key | 
              Record.category.key] as colname, *_:
            return string_filter(filter_, colname)
        case Record.id.key as colname, *_:
            return ordering_filter(filter_, colname, int)
        case [ ] | "true" | "True":
            return true()
        case _:
            raise ValueError(
                f"Could not understand query: {filter_=!r}.")


def parse_semantic_filter(filter_: str) -> TextClause:
    """
    Takes a string filter and
        * splits it by `&&` and parses it, given that `&&` is in `filter_`,
        * replaces every `[...]` by parsing the content with `sql_filter` 
        and returns a `text` sql statement.
    """
    if "&&" in filter_:
        sql_ = [sql_filter(stmt) for stmt in filter_.split("&&")]
        return select(Record).where(*sql_)

    p = re.compile(r"\[(.*?)\]")
    def repl(m: re.Match):
        return sql_filter(m.group(0))
    
    return text(p.sub(repl, filter_))


def parse_record_from_id(
        id_: str | int,
        engine: Engine,
        entity: T
) -> T:
    """Takes str | int and returns a record from it."""
    if not isinstance(id_, str | int):
        raise TypeError(f"Argument {id_=} must be String or Numeric type.")
    id_ = int(id_)

    with Session(engine) as session:
        entity = session.get(entity, id_)
    if entity is None:
        raise ValueError(f"Can't get entity with {id_=}.")
    return entity