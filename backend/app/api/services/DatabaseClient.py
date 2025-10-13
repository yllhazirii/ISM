import pandas as pd
from sqlalchemy import create_engine, text, Table, Column, Integer, String, Float, DateTime, MetaData
from sqlalchemy.engine import Connection
from app.core.config import settings
import uuid
from sqlalchemy.engine import Engine

class DatabaseClient:
    """
    Manages MSSQL connection, table creation, and bulk upserts using row index as PK.
    """

    def __init__(self):
        DB_URL = settings.SQLALCHEMY_DATABASE_URI
        self.engine: Engine = create_engine(DB_URL)

    def get_connection(self) -> Connection:
        """Opens and returns a new connection."""
        return self.engine.connect()

    def create_table_from_dataframe(self, conn: Connection, table_name: str, df: pd.DataFrame):
        """Create table if it doesn't exist, with instance_id as primary key."""
        metadata = MetaData()

        columns = [Column("instance_id", Integer, primary_key=True, autoincrement=False)]
        for col_name, dtype in zip(df.columns, df.dtypes):
            if col_name == "instance_id":
                continue
            if pd.api.types.is_integer_dtype(dtype):
                columns.append(Column(col_name, Integer))
            elif pd.api.types.is_float_dtype(dtype):
                columns.append(Column(col_name, Float))
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                columns.append(Column(col_name, DateTime))
            else:
                columns.append(Column(col_name, String(512)))

        # Create the table in dbo schema
        table = Table(table_name, metadata, *columns, extend_existing=True, schema="dbo")
        metadata.create_all(self.engine)
        print(f"Table '{table_name}' created in schema 'dbo' successfully!")


    def upsert_dataframe(self, conn: Connection, table_name: str, df: pd.DataFrame):
        """
        Bulk upsert using a staging table and MERGE, based on instance_id as primary key.
        """
        if df.empty:
            print(f"No rows to upsert for {table_name}.")
            return

        # Generate a unique staging table name
        staging_table = f"{table_name}_staging_{uuid.uuid4().hex[:8]}"

        # ✅ Write to staging table
        df.to_sql(staging_table, con=self.engine, if_exists='replace', index=False, schema="dbo")

        quoted_table = f"[dbo].[{table_name}]"
        quoted_staging = f"[dbo].[{staging_table}]"

        # Generate the column sets
        columns = [c for c in df.columns if c != "instance_id"]
        set_stmt = ", ".join([f"target.[{c}] = source.[{c}]" for c in columns])
        insert_cols = ", ".join(["instance_id"] + [f"[{c}]" for c in columns])
        insert_vals = ", ".join(["source.instance_id"] + [f"source.[{c}]" for c in columns])

        merge_sql = f"""
        MERGE {quoted_table} AS target
        USING {quoted_staging} AS source
        ON target.instance_id = source.instance_id
        WHEN MATCHED THEN
            UPDATE SET {set_stmt}
        WHEN NOT MATCHED BY TARGET THEN
            INSERT ({insert_cols})
            VALUES ({insert_vals});
        """

        # ✅ Execute inside a transaction
        with conn.begin():
            conn.execute(text(merge_sql))
            conn.execute(text(f"DROP TABLE {quoted_staging};"))

        print(f"Upserted {len(df)} rows into {quoted_table}.")

    def delete_rows(self, conn: Connection, table_name: str, row_indices: list[int]):
        """
        Delete rows from the table based on instance_id.
        """
        if not row_indices:
            return

        quoted_table = f"[{table_name}]"
        indices_str = ", ".join(map(str, row_indices))
        sql = f"DELETE FROM {quoted_table} WHERE instance_id IN ({indices_str});"
        conn.execute(text(sql))
        print(f"Deleted {len(row_indices)} rows from {quoted_table}.")

# # Usage example
# db = DatabaseClient()
# df = pd.DataFrame({
#     "Depot Name": ["Depot1", "Depot2"],
#     "City": ["City1", "City2"],
#     "Fab/Split": ["Yes", "No"]
# })
# df["instance_id"] = df.index
# 
# df1 = pd.DataFrame({
#     "instance_id": [0,2,1],
#     "Depot Name": ["Depot3", "Depot3", "Depot4"],
#     "City": ["City1", "City2",  "City2"],
#     "Fab/Split": ["Yes", "No", "Yes"]
# })
# 
# with db.get_connection() as conn:
#     print("HERE")
#     db.create_table_from_dataframe(conn, "Depot", df)
#     db.upsert_dataframe(conn, "Depot", df1)
