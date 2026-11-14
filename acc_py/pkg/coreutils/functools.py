from functools import wraps
from .colors import fg


def success(*s: str) -> None:
    """Quick success printer that wraps `repr` on every string in `s`."""
    res = s[0] if len(s) == 1 else ', '.join(map(repr, s)) 
    print(f"{fg.green}Success: {res}.{fg.reset}")


def softerror(e: Exception) -> None:
    """Prints `e` without raising it."""
    print(f"{fg.red}{type(e).__name__}: {e}.{fg.reset}")


def early_return(classinfo):
    """Return first argument directly if `isinstance(., classinfo)` 
    evaluates to `True`."""
    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            first_arg = args[0]
            if isinstance(first_arg, classinfo):
                return first_arg
            res = func(*args, **kwargs)
            return res
        return wrapped
    return decorator


def type_check(classinfo, *, narg: int = 0):
    """Raise TypeError if `n`th argument is not of type `classinfo`."""
    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            first_arg = args[narg]
            if not isinstance(first_arg, classinfo):
                raise TypeError(
                    f"Argument '{first_arg}' is not of type `str`.")
            res = func(*args, **kwargs)
            return res
        return wrapped
    return decorator
