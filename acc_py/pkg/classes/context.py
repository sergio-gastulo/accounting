"""
Main data manager for acccli. Relies heavily on utilities.core.
"""
from dataclasses import dataclass
from typing import List, Optional, Any
from pathlib import Path, WindowsPath
from datetime import date

from pandas import Period
from sqlalchemy.engine.base import Engine
from sqlalchemy import create_engine

from pkg.utilities.jops import jopen, jrepr
from pkg.utilities.file import sha256, SHA256Error
from pkg.utilities.prompt import (prompt_currency,
                                  prompt_category_from_keybinds)
from pkg.utilities.currency import (check_currency_list,
                                    get_exchange_dict)
from pkg.utilities.typing import (FieldDictType,
                                  KeybindDictType,
                                  ExchangeDictType,
                                  StrDict,
                                  CurrencyColorDictionary)
from pkg.utilities.core import (APPLICATION_CACHED_DIRECTORY,
                                soft_warning,
                                confirm_action,
                                ensure,
                                import_fields,
                                check_editor,
                                check_colors,
                                pprint_categories,
                                fetch_keybind_dict,
                                fetch_category_dictionary)


#region ======================== untested utils ================================

def _set_currency_list(currencies : List[str]) -> List[str]:
    if currencies is None:
        raise ValueError(f"A list of the managed currencies must be provided.")
    return check_currency_list(currencies)


def _today_period() -> Period:
    return Period(date.today(), 'M')


def _engine(url : str | Path | None) -> Engine:
    if url is None:
        return create_engine("sqlite://")
    if 'sqlite' in url:
        return create_engine(url)
    return create_engine(f"sqlite:///{url}")


def _jsave(d : dict, p : Path) -> None:
    ensure(p, Path, WindowsPath)
    text = jrepr(d)
    p.write_text(text, encoding='utf-8')


def _path_exists(p : str | Path) -> Path:
    if isinstance(p, str):
        p = Path(p)
    if p.exists():
        return p
    raise FileNotFoundError(f"Path {p} does not exist.")


# https://stackoverflow.com/a/49782093/29272030
def _rmdir(directory : Path) -> None:
    for item in directory.iterdir():
        if item.is_dir():
            _rmdir(item)
        else:
            item.unlink()
    directory.rmdir()


def _validate_categories(categories : List[str], keybinds : StrDict) -> List[str]:
    res = [prompt_category_from_keybinds(keybinds, 
                                         category, 
                                         quiet_success=True)
           for category in categories]
    return res


def _return_dict(d : dict) -> dict:
    ensure(d, dict)
    return d


#endregion =====================================================================



@dataclass
class AccountingContext:

    #- main db configurations-
    # fetched from config.json
    config_path : Optional[Path]                = None
    fields_path : Optional[Path]                = None
    engine: Optional[Engine]                    = None
    editor : Optional[Path]                     = None
    fields : Optional[FieldDictType]            = None
    default_currency : Optional[str]            = None 
    # built at runtime if not fetched from cache
    keybinds : Optional[KeybindDictType]        = None
    categories_dict: Optional[StrDict]          = None

    #-- plot configurations, not needed for db--
    # fetched from config.json
    currency_list : Optional[List[str]]                 = None
    inflow_categories : Optional[List[str]]             = None
    # fetched but built later
    colors: Optional[CurrencyColorDictionary]           = None
    # built at runtime
    exchange_dictionary : Optional[ExchangeDictType]    = None
    period: Optional[Period]                            = None
    matplotlib : Optional[dict[str, Any]]               = None


    def load_from_cache(
            self
    ) -> None:
        """
        Loads latest `ctx.to_cache()` context from `state_path`.

        Notes
        -----
        - Checks SHA256 sum from config_path and fields_path before updating.
        """
        # load state / cache
        name        = "state.json"
        state_path  = APPLICATION_CACHED_DIRECTORY / name
        _path_exists(state_path)
        
        # compute current sha and fetch data
        cached_dict         =   jopen(state_path)
        data                =   cached_dict["data"]
        current_config_sha  =   sha256(data["config_path"])
        current_fields_sha  =   sha256(data["fields_path"])

        # ensure sha256 match
        err = []
        if current_config_sha != (expected := cached_dict["config-sha256"]):
            err.append(f"expected {expected}, got {current_config_sha}.")
        if current_fields_sha != (expected := cached_dict["fields-sha256"]):
            err.append(f"expected {expected}, got {current_fields_sha}.")
        if err:
            raise SHA256Error(f"Mismatches:\n{"\n".join(err)}.")
        
        # load to self and wrap attrs
        self.__dict__.update(data)
        self.config_path    =   Path(self.config_path)
        self.fields_path    =   Path(self.fields_path)
        self.editor         =   Path(self.editor)
        self.engine         =   _engine(self.engine)
        # overwrite period
        self.period         =   _today_period()


    def delete_cache(self):
        """Removes all files in APPLICATION_CACHED_DIRECTORY."""
        soft_warning("Warning: you will lose these files completely.")
        action = lambda : _rmdir(APPLICATION_CACHED_DIRECTORY)
        confirm_action(action)
        print(f"All files in {APPLICATION_CACHED_DIRECTORY} have been removed.")


    def set(
            self,
            config_path : Path, 
            fields_path : Path
    ) -> None:
        """Sets minimal configurations to run acccli in db mode."""
        # try to fetch from cache
        try:
            self.load_from_cache()
            print("Sucessfully loaded ctx.fields from cache.")
            return
        except (SHA256Error, FileNotFoundError) as e:
            print(
                f"Could not load from cache in '{APPLICATION_CACHED_DIRECTORY}'."
                f"{repr(e)}"
                f"Instead, re-fetching all data from standard configurations."
                f"If the configurations are loaded as expected, consider running"
                f"`ctx.to_cache()` to save changes."
            )

        config                      =   jopen(config_path)
        self.config_path            =   _path_exists(config_path)
        self.fields_path            =   _path_exists(fields_path)
        self.engine                 =   _engine(config.get('db_path'))
        self.editor                 =   check_editor(config.get("editor_path"))
        self.fields                 =   import_fields(fields_path)
        self.default_currency       =   prompt_currency(config.get('default_currency'), quiet=True)
        self.keybinds               =   fetch_keybind_dict(self.fields)
        self.categories_dict        =   fetch_category_dictionary(self.fields)


    def set_plot(self) -> None:
        """Sets plot configurations for styling."""

        # ensure that 'set' is ran before this 
        if not self.config_path and not self.fields_path:
            raise RuntimeError("Run 'set' before setting 'plot' constructor.")

        # if the attrs below exist, more likely ctx's attrs have been 
        # fetched via load_from_cache(), skipping this...
        if self.exchange_dictionary and self.period:
            msg =   "Context attributes have been fetched from cache. " \
                    "Skipping `set_plot`."
            print(msg)
            return

        # proceed to load remaining attrs 
        config                      =   jopen(self.config_path)
        self.currency_list          =   _set_currency_list(config.get('currency_list'))
        self.inflow_categories      =   _validate_categories(config.get('inflow-categories'), self.keybinds)
        self.colors                 =   check_colors(self.currency_list, config.get('rgb_colors'))
        self.exchange_dictionary    =   get_exchange_dict(self.currency_list, config.get('use_cache'), quiet=True)
        self.period                 =   _today_period()
        # NOTE: we're only checking if it's a dictionary
        # It's up to user if the configurations are actually right
        self.matplotlib             =   _return_dict(config.get("matplotlib"))


    def update_exchange(self) -> None:
        """Force updates to self.exchange_dictionary."""
        self.exchange_dictionary = get_exchange_dict(
            self.currency_list,
            use_cache=False,
            quiet=False
        )
        print(
            "If you're fine with this exchange dictionary, you might " \
            "want to run `ctx.to_cache()` in order to save changes."
        )


    def to_cache(self, path : Optional[Path] = None) -> None:
        """
        Saves current ctx state to a json file.

        Arguments
        ---------
        path
            Optional, defaults to `/APPLICATION_CACHED_DIRECTORY/state.json.`
        """
        # force all fields to be fetched before saving
        if not self.period:
            self.set_plot()

        if path is None:
            name = "state.json"
            path = APPLICATION_CACHED_DIRECTORY / name
            
        # load state
        save_dict = self.__dict__.copy()

        # manually update unserializable
        save_dict["engine"]         =   str(self.engine.url)
        save_dict["editor"]         =   str(self.editor)
        save_dict["period"]         =   str(self.period)
        save_dict["config_path"]    =   str(self.config_path)
        save_dict["fields_path"]    =   str(self.fields_path)

        save_dict = {
            "config-sha256" : sha256(self.config_path),
            "fields-sha256" : sha256(self.fields_path),
            "data" : save_dict
        }
        _jsave(save_dict, path)


    def pprint_cats(self, with_help : bool = False) -> None:
        """
        Pretty-prints categories.

        Parameters
        ----------
        with_help
            - Defaults to False. 
            - Prints each category and its description
            - If True, print with help.
        """
        pprint_categories(self.categories_dict, self.fields, with_help)



ctx = AccountingContext()