import os
import json
from datetime import datetime
from typing import Optional
import pandas as pd
from app.core.config import settings
import hashlib


ROW_HASH_FILE = "/app/app/sharepoint/sheet_row_hashes.json"
PERSISTENCE_FILE = "/app/app/sharepoint/last_synced_time.json"

def compute_row_hash(row: pd.Series) -> str:
    """Compute a stable hash for a row (fill NaNs to ensure consistency)."""
    row_bytes = ",".join(row.fillna("__NA__").astype(str)).encode("utf-8")
    return hashlib.sha256(row_bytes).hexdigest()

def load_row_hashes(file_path: str = ROW_HASH_FILE) -> dict:
    """Load previous row-hash snapshot."""
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Could not decode JSON from {file_path}. Resetting hashes.")
    return {}

def save_row_hashes(hashes: dict, file_path: str = ROW_HASH_FILE) -> None:
    """Save row-hash snapshot."""
    with open(file_path, "w") as f:
        json.dump(hashes, f, indent=4)


def _load_last_synced_time(file_key: str, file_path: str = PERSISTENCE_FILE) -> str:
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                return data.get(file_key, "1970-01-01T00:00:00Z")
        except json.JSONDecodeError:
            print(f"Warning: Could not decode JSON from {file_path}. Resetting time.")
    return "1970-01-01T00:00:00Z"

def _save_last_synced_time(file_key: str, timestamp: str, file_path: str = PERSISTENCE_FILE) -> None:
    data = {}
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            pass
    data[file_key] = timestamp
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)




class DataSyncer():
    def __init__(self, file_editor: 'FileEditor', db_client: 'DBClient'):
        self.editor = file_editor
        self.db_client = db_client
        self._sharepoint_file_name = self.editor._sharepoint_file_name

        # Get list of sheets to sync from metadata
        self.sheets_to_sync = [s["name"] for s in self.editor.metadata["sheets"]]
        self.sheets_mapping = {
            s["name"]: s["formatted_name"] for s in self.editor.metadata["sheets"]
        }

    def sync_dataframe_to_db(self, df: pd.DataFrame, table_name: str,
                             added_rows: Optional[list[int]] = None,
                             changed_rows: Optional[list[int]] = None,
                             removed_rows: Optional[list[int]] = None):
        added_rows = added_rows or []
        changed_rows = changed_rows or []
        removed_rows = removed_rows or []

        if df.empty:
            print(f"No data in dataframe for table '{table_name}'")
            return

        with self.db_client.get_connection() as conn:
            print(f"Ensuring table '{table_name}' exists...")
            self.db_client.create_table_from_dataframe(conn, table_name, df)

            rows_to_upsert = df.loc[added_rows + changed_rows] if added_rows or changed_rows else pd.DataFrame()
            if not rows_to_upsert.empty:
                print(f"Upserting {len(rows_to_upsert)} rows into '{table_name}'...")
                self.db_client.upsert_dataframe(conn, table_name, rows_to_upsert)

            if removed_rows:
                print(f"Deleting {len(removed_rows)} rows from '{table_name}'...")
                self.db_client.delete_rows(conn, table_name, removed_rows)

        print(f"✅ Sync complete for table '{table_name}'")

    def check_and_sync(self):
        """Check SharePoint workbook and sync only changed rows for all configured sheets."""
        print(f"⏰ [{datetime.now().isoformat()}] Starting scheduled check...")

        try:
            metadata = self.editor.get_sync_data()
            current_mod_time = metadata.get("lastModifiedDateTime")
            if not current_mod_time:
                raise ValueError("Could not find 'lastModifiedDateTime'.")
        except Exception as e:
            print(f"FATAL ERROR: {e}")
            return

        # Read all configured sheets at once
        try:
            dfs = self.editor.read_sheets_with_metadata(self.sheets_to_sync)
        except Exception as e:
            print(f"FATAL ERROR: {e}")
            return

        # Load previous row hashes
        old_hashes = load_row_hashes()

        for unf_sheet_name, df in dfs.items():
            sheet_name = self.sheets_mapping[unf_sheet_name]
            print(f"Processing sheet '{sheet_name}'...")

            # Load last synced time for this sheet
            last_synced_time = _load_last_synced_time(sheet_name)

            # Only sync if file changed since last sheet sync
            if current_mod_time <= last_synced_time:
                print(f"❗ No changes detected for sheet '{sheet_name}'. Last synced at {last_synced_time}.")
                continue

            # Compute row hashes
            new_hashes = {str(i): compute_row_hash(df.iloc[i]) for i in range(len(df))}
            old_sheet_hashes = old_hashes.get(sheet_name, {})

            # Detect added, changed, removed rows
            added_rows = [int(idx) for idx in new_hashes if idx not in old_sheet_hashes]
            changed_rows = [int(idx) for idx, h in new_hashes.items() if idx in old_sheet_hashes and old_sheet_hashes[idx] != h]
            removed_rows = [int(idx) for idx in old_sheet_hashes if idx not in new_hashes]

            if not added_rows and not changed_rows and not removed_rows:
                print(f"✅ No row changes detected in sheet '{sheet_name}'. Skipping DB sync.")
                # Still update last synced time
                # _save_last_synced_time(sheet_name, current_mod_time)
                continue
            print(
                f"❗ Changes detected for sheet '{sheet_name}': "
                f"Added: {len(added_rows)}, "
                f"Changed: {len(changed_rows)}, "
                f"Removed: {len(removed_rows)}"
            )
            # print(f"Added rows: {added_rows}")
            # print(f"Changed rows: {changed_rows}")
            # print(f"Removed rows: {removed_rows}")

            # Sync to DB
            self.sync_dataframe_to_db(df, sheet_name, added_rows, changed_rows, removed_rows)

            # Update hashes and last synced time per sheet
            old_hashes[sheet_name] = new_hashes
            _save_last_synced_time(sheet_name, current_mod_time)

        # Save all updated hashes
        save_row_hashes(old_hashes)
        print(f"✅ All configured sheets synced with per-sheet last synced times.")
