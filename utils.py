import re
import pandas as pd

from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime
)

def sanitize_column_name(col_name):
    return re.sub(r"\W+", "_", col_name).lower()

def map_dtype(dtype):
    if pd.api.types.is_integer_dtype(dtype):
        return Integer
    elif pd.api.types.is_float_dtype(dtype):
        return Float
    elif pd.api.types.is_bool_dtype(dtype):
        return Boolean
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return DateTime
    else:
        return String

def create_table_from_dataframe(
    df: pd.DataFrame, table_name: str, engine, metadata_obj
):
    sanitized_columns = {col: sanitize_column_name(col) for col in df.columns}
    df = df.rename(columns=sanitized_columns)

    columns = [
        Column(col, map_dtype(dtype))
        for col, dtype in zip(df.columns, df.dtypes)
    ]

    table = Table(table_name, metadata_obj, *columns)
    metadata_obj.create_all(engine)

    with engine.connect() as conn:
        for _, row in df.iterrows():
            insert_stmt = table.insert().values(**row.to_dict())
            conn.execute(insert_stmt)
        conn.commit()