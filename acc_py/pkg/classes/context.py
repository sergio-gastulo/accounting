"""
Main data manager for acccli. Relies heavily on coreutils
"""
from dataclasses import dataclass
from typing import List, Optional, Any
from pathlib import Path
from datetime import date

from pandas import Period
from sqlalchemy.engine.base import Engine
from sqlalchemy import create_engine

from pkg.coreutils.paths import APPLICATION_CACHED_DIRECTORY
from pkg.coreutils.typing import (FieldDictType,
                                  KeybindDictType,
                                  ExchangeDictType,
                                  StrDict,
                                  CurrencyColorDictionary)
from pkg.coreutils.jops import jopen, jdump
from pkg.coreutils.file import (SHA256Error,
                                sha256,
                                check_editor,
                                rmdir,)
from pkg.coreutils.dictops import (import_fields,
                                   pprint_categories,
                                   fetch_keybind_dict,
                                   fetch_category_dictionary,)
from pkg.coreutils.prompt import (prompt_currency,
                                  prompt_category_from_keybinds)
from pkg.coreutils.currency import (to_currency,
                                    get_exchange_dict)
from pkg.coreutils.colors import fg, check_colors


def to_engine(engineurl: str | Path | None) -> Engine:
    """
    Create engine from `engineurl`. If not provided, inmemory db is created.
    """
    if engineurl is None:
        return create_engine("sqlite://")
    if 'sqlite' in engineurl:
        return create_engine(engineurl)
    return create_engine(f"sqlite:///{engineurl}")


@dataclass
class AccountingContext:

    # main db configurations
    # fetched from config.json
    config_path: Optional[Path] = None
    fields_path: Optional[Path] = None
    engine: Optional[Engine] = None
    editor: Optional[Path] = None
    fields: Optional[FieldDictType] = None
    default_currency: Optional[str] = None 
    # built at runtime if not fetched from cache
    keybinds: Optional[KeybindDictType] = None
    categories_dict: Optional[StrDict] = None

    # plot configurations, not needed for db
    # fetched from config.json
    currency_list: Optional[List[str]] = None
    inflow_categories: Optional[List[str]] = None
    # fetched but built later
    colors: Optional[CurrencyColorDictionary] = None
    # built at runtime
    exchange_dictionary: Optional[ExchangeDictType] = None
    period: Optional[Period] = None
    matplotlib: Optional[dict[str, Any]] = None


    def __repr__(self):
        toolong = frozenset(['fields', 'keybinds', 'categories_dict'])
        strs = [
            f"{attr}:\t{val if attr not in toolong else "{...}"}"
            for attr, val in self.__dict__.items()
        ]
        return '\n'.join(strs)
    

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
        if not state_path.exists():
            raise FileNotFoundError(f"Path {state_path} does not exist.")
        
        # compute current sha and fetch data
        cached_dict = jopen(state_path)
        data = cached_dict["data"]
        current_config_sha = sha256(data["config_path"])
        current_fields_sha = sha256(data["fields_path"])

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
        self.config_path = Path(self.config_path)
        self.fields_path = Path(self.fields_path)
        self.editor = Path(self.editor)
        self.engine = to_engine(self.engine)
        
        # overwrite period, always
        self.period = Period(date.today(), 'M')


    def delete_cache(self, force: bool = False):
        """Removes all files in APPLICATION_CACHED_DIRECTORY."""
        if not force:
            warning_ = "Warning: you will lose these files completely."
            print(f"{fg.red}{warning_}{fg.reset}"
                  "In order to actually delete cache, please set force=False.")
            return None

        rmdir(APPLICATION_CACHED_DIRECTORY)
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
            return None
        except (SHA256Error, FileNotFoundError) as e:
            print(f"Could not load from cache in " 
                  f"'{APPLICATION_CACHED_DIRECTORY}'."
                  f"{repr(e)}"
                  f"Instead, re-fetching all data from standard configurations."
                  f"If the configurations are loaded as expected," 
                  f"consider running ctx.to_cache() to save changes.")

        config = jopen(config_path)

        if (path := Path(config_path)).exists():
            self.config_path = path
        else:
            raise FileNotFoundError(f"Config path: {config_path} could not be found.")
        if (path := Path(fields_path)).exists():
            self.fields_path = path
        else:
            raise FileNotFoundError(f"Fields path: {fields_path} could not be found.")

        self.engine = to_engine(config.get('db_path'))
        self.editor = check_editor(config.get("editor_path"))
        self.fields = import_fields(fields_path)
        self.default_currency = prompt_currency(config.get('default_currency'), 
                                                quiet=True)
        self.keybinds = fetch_keybind_dict(self.fields)
        self.categories_dict = fetch_category_dictionary(self.fields)


    def set_plot(self) -> None:
        """Sets plot configurations for styling."""

        # ensure that 'set' is ran before this 
        if not self.config_path and not self.fields_path:
            raise RuntimeError("Run 'set' before setting 'plot' constructor.")

        # if the attrs below exist, more likely ctx's attrs have been 
        # fetched via load_from_cache(), skipping this...
        if self.exchange_dictionary and self.period:
            print("Context attributes have been fetched from cache."
                  "Skipping `set_plot`.")
            return None

        # proceed to load remaining attrs 
        config = jopen(self.config_path)

        if currencies := config.get('currency_list') is None:
            raise ValueError(f"A list of managed currencies must be provided.")        
        self.currency_list = to_currency(currencies)

        self.inflow_categories = [prompt_category_from_keybinds(self.keybinds,
                                                                category,
                                                                quietsuccess=True)
                                  for category in config.get('inflow-categories')]
        self.colors = check_colors(self.currency_list, 
                                   config.get('rgb_colors'))
        self.exchange_dictionary = get_exchange_dict(self.currency_list, 
                                                     config.get('use_cache'), 
                                                     quiet=True)
        self.period = Period(date.today(), 'M')
        self.matplotlib = config.get("matplotlib")


    def update_exchange(self) -> None:
        """Force updates to self.exchange_dictionary."""
        self.exchange_dictionary = get_exchange_dict(self.currency_list,
                                                     use_cache=False,
                                                     quiet=False)
        print("If you're fine with this exchange dictionary, you might "
              "want to run `ctx.to_cache()` in order to save changes.")


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
        save_dict["engine"] = str(self.engine.url)
        save_dict["editor"] = str(self.editor)
        save_dict["period"] = str(self.period)
        save_dict["config_path"] = str(self.config_path)
        save_dict["fields_path"] = str(self.fields_path)

        save_dict = {
            "config-sha256" : sha256(self.config_path),
            "fields-sha256" : sha256(self.fields_path),
            "data" : save_dict
        }
        jdump(save_dict, path)


    def pprint_cats(self, help_: bool = False) -> None:
        """
        Pretty-prints categories.

        Parameters
        ----------
        with_help
            - Defaults to False. 
            - Prints each category and its description
            - If True, print with help.
        """
        pprint_categories(self.categories_dict, self.fields, help_)



ctx = AccountingContext()