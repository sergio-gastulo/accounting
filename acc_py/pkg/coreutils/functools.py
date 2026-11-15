from functools import wraps
from typing import get_type_hints

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


def type_check(argnames: list[str] | None = None):
    """Raise TypeError if `argname` argument is not of it's respective type.
    
    Notes
    -----
    * Ignores parametrized generics
    """
    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            typehints = get_type_hints(func)
            inorder = list(typehints.keys())
            iterator = argnames if argnames else inorder
            if argnames is None:
                iterator.remove("return")
            for argname in iterator:
                idx = inorder.index(argname)
                try:
                    iscorrect = isinstance(args[idx], typehints[argname])
                except TypeError as e:
                    if "isinstance() argument" in str(e):
                        pass
                    else:
                        raise e
                except IndexError:  # TODO: test this
                    pass  # default values are not passed in *args -> ignoring
                else:
                    if not iscorrect:
                        raise TypeError(
                            f"Argument {argname=!r} is not of type `str`.")
            res = func(*args, **kwargs)
            return res
        return wrapped
    return decorator
