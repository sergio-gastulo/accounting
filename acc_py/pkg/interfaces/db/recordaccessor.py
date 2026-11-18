import pandas as pd
from sqlalchemy import update
from sqlalchemy.orm import Session

from pkg.classes.model import Record
from pkg.classes.context import ctx

from .dataframe import (has_recordid,
                        pprint_df,
                        sanitize_df,)

ACCESSOR_ALIAS = "recorddb"
OVERWRITE_DF_HAS_INDEX = True


@pd.api.extensions.register_dataframe_accessor(ACCESSOR_ALIAS)
class RecordAccessor:
    def __init__(self, pandasobj):
        self.categories = list(ctx.categories_dict.keys())
        self._obj = sanitize_df(pandasobj, self.categories)

    def write(
            self,
            *, 
            overwrite: bool = OVERWRITE_DF_HAS_INDEX
    ):
        df = self._obj
        
        if not has_recordid(df):
            df.to_sql(Record.__tablename__, ctx.engine,
                      if_exists="append",
                      index=False)
            pprint_df(df, header="Actions commited.")
            return None
        
        if not overwrite:
            raise ValueError("DataFrame contains index data. Double-check"
                             " or set overwrite to True.")
        
        if df.index.name == Record.id.key:
            df.reset_index(inplace=True)
        asdict = df.to_dict(orient='records')
        with Session(ctx.engine) as session:
            session.execute(update(Record), asdict)
            session.commit()
        pprint_df(df, header="Actions commited.")