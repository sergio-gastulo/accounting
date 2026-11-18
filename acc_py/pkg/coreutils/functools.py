from functools import wraps
from typing import get_type_hints, get_origin

from .colors import fg


DEFAULT_ARGUMENT_EARLY_RETURN_CHECK = 0


def success(*s: str) -> None:
    """Quick success printer that wraps `repr` on every string in `s`."""
    res = s[0] if len(s) == 1 else ', '.join(map(repr, s)) 
    print(f"{fg.green}Success: {res}.{fg.reset}")


def softerror(e: Exception) -> None:
    """Prints `e` without raising it."""
    print(f"{fg.red}{type(e).__name__}: {e}.{fg.reset}")


def early_return(
        classinfo,
        narg: int = DEFAULT_ARGUMENT_EARLY_RETURN_CHECK
):
    """Return narg-th argument directly if `isinstance(., classinfo)` 
    evaluates to `True`."""
    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            arg = args[narg]
            if isinstance(arg, classinfo):
                return arg
            res = func(*args, **kwargs)
            return res
        return wrapped
    return decorator


def type_check(
        argnames: list[str] | None = None
) -> None:
    """Raise TypeError if `argname` argument is not of it's respective type.
    
    Notes
    -----
    * Typechecks parametrized generics origin only.
    """
    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            typehints = get_type_hints(func)
            if not typehints:
                return func(*args, **kwargs)
            inorder = list(typehints.keys())
            iterator = argnames if argnames else inorder
            if "return" in iterator:
                iterator.remove("return")  # return type is not checked
            for argname in iterator:
                idx = inorder.index(argname)
                classinfo = typehints[argname]
                # Default values are not passed in *args
                # It requires a typing.bing_args call
                # But, if someone passes / defines a default, it's *OBVIOUS*
                # that they know what they're doing 
                # ---> no typecheck
                if idx >= len(args):
                    continue
                if origin := get_origin(classinfo):
                    classinfo = origin
                if not isinstance(args[idx], classinfo):
                    raise TypeError(f"Argument {argname!r} is not of type"
                                    f" {classinfo!r}.")
            return func(*args, **kwargs)
        return wrapped
    return decorator