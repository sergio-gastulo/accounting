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


class ParseSQLQueryError(ValueError):
    pass


T = TypeVar(name="T")


def range_filter(
        filter_: str,
        colname: str,
        map_: Callable,
) -> ColumnElement[bool]:
    """Filter a numeric-like sql query. Returns parsed SQLAlchemy query."""

    column: ColumnElement = getattr(Record, colname)
    
    repatterns = [
        re.compile(f"{colname} between (?P<lower>.+?) and (?P<upper>.+?)"),
        re.compile(f"(?P<lower>.+?) <=? {colname} <=? (?P<upper>.+?)"),
        re.compile(f"(?P<upper>.+?) >=? {colname} >=? (?P<lower>.+?)"),
    ]
    s = filter_.strip()
    for pattern in repatterns:
        if m := pattern.fullmatch(s):
            lower, upper = map(map_, [m["lower"], m["upper"]])
            return and_(lower <= column, column <= upper) 

    repatterns = [
        re.compile(f"(?P<lower>.+?) <=? {colname}"),
        re.compile(f"{colname} >=? (?P<lower>.+?)"),
    ]
    for pattern in repatterns:
        if m := pattern.fullmatch(s):
            return column >= map_(m["lower"])

    repatterns = [
        re.compile(f"(?P<upper>.+?) >=? {colname}"),
        re.compile(f"{colname} <=? (?P<upper>.+?)"),
    ]
    for pattern in repatterns:
        if m := pattern.fullmatch(s):
            return column >= map_(m["upper"])
        
    raise ParseSQLQueryError(
        f"Could not understand range filter: {filter_=!r}.")


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
            raise ParseSQLQueryError(
                f"Could not understand string filter: {filter_=!r}.")


def date_filter(
        filter_: str,
        colname: str
) -> ColumnElement[bool]:
    """Filter by date, as a string or with datetime arithmetic."""
    filterfuncs = ((range_filter, {"mapper": parse_date}),
                   (string_filter, {}))

    for func, kwargs in filterfuncs:
        try:
            boolcol = func(filter_, colname, **kwargs)
        except ParseSQLQueryError:
            continue
        else:
            return boolcol

    raise ParseSQLQueryError(f"Could not parse date query: {filter_=!r}.")



def sql_filter(filter_: str):
    """
    Parses a single sql statement into a semantically-valid SQL query 
    and returns it. The query is not validated, only parsed.
    """
    if Record.date.key in filter_:
        return date_filter(filter_, Record.date.key)
    if Record.amount.key in filter_:
        return range_filter(filter_, Record.amount.key)
    
    match filter_.split():
        case [Record.description.key | 
              Record.currency.key | 
              Record.category.key] as colname, *_:
            return string_filter(filter_, colname)
        case Record.id.key as colname, *_:
            return range_filter(filter_, colname, int)
        case [ ] | "true" | "True":
            return true()
        case _:
            raise ParseSQLQueryError(
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