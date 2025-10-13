import os
import json
from datetime import datetime
from typing import Dict, Any
from app.core.config import settings
from app.api.services.GraphClient import GraphClient
from urllib.parse import quote
from io import BytesIO
import time
import requests
import pandas as pd


class FileEditor():
    def __init__(self, graph_client: 'GraphClient',
                 site_domain=settings.SITE_DOMAIN, site_name=settings.SITE_NAME,
                 sharepoint_folder_name=settings.SHAREPOINT_FOLDER_NAME,
                 sharepoint_file_name=settings.SHAREPOINT_FILE_NAME,
                 metadata_path="/app/app/sharepoint/DepotMasterMetadata.json"):
        self._client = graph_client
        self.site_domain = site_domain
        self.site_name = site_name

        self._headers = self._client._headers
        self.graph_api = self._client.graph_api
        self._drive_id = None
        self._site_id = None
        self._sharepoint_folder_name = sharepoint_folder_name
        self._sharepoint_file_name = sharepoint_file_name
        self._metadata_path = metadata_path

        # Load JSON metadata
        self.metadata = self._load_metadata()

    def _load_metadata(self):
        if not os.path.exists(self._metadata_path):
            raise FileNotFoundError(f"Metadata file not found: {self._metadata_path}")
        with open(self._metadata_path, "r") as f:
            return json.load(f)

    def get_sync_data(self):
        self.get_site_id()
        self.get_drive_id()
        encoded_file_name = quote(self._sharepoint_file_name)
        file_path = f"{self._sharepoint_folder_name}/{encoded_file_name}"
        url = f"{self.graph_api}/sites/{self._site_id}/drives/{self._drive_id}/root:/{file_path}"
        response = requests.get(url, headers=self._headers())
        response.raise_for_status()
        return response.json()

    # -----------------------
    # SharePoint helpers
    # -----------------------
    def get_site_id(self):
        if self._site_id:
            return self._site_id
        url = f"{self.graph_api}/sites/{self.site_domain}:/sites/{self.site_name}"
        response = requests.get(url, headers=self._headers())
        response.raise_for_status()
        self._site_id = response.json()["id"]
        return self._site_id

    def get_drive_id(self):
        if self._drive_id:
            return self._drive_id
        site_id = self.get_site_id()
        url = f"{self.graph_api}/sites/{site_id}/drives"
        response = requests.get(url, headers=self._headers())
        response.raise_for_status()
        drives = response.json().get("value", [])
        target_drive_name = "Documents"
        for drive in drives:
            if drive.get("name") == target_drive_name:
                self._drive_id = drive["id"]
                return self._drive_id
        raise Exception(f"Document Library (Drive) named '{target_drive_name}' not found.")

    # -----------------------
    # Read Excel
    # -----------------------
    def _download_excel(self):
        """Download workbook content from SharePoint"""
        self.get_site_id()
        self.get_drive_id()
        file_path = f"{self._sharepoint_folder_name}/{self._sharepoint_file_name}"
        # Add timestamp query to force re-download
        timestamp = int(time.time())
        url = f"{self.graph_api}/sites/{self._site_id}/drives/{self._drive_id}/root:/{file_path}:/content?ts={timestamp}"
        # url = f"{self.graph_api}/sites/{self._site_id}/drives/{self._drive_id}/root:/{file_path}:/content"
        headers = self._headers()
        response = requests.get(url, headers=headers)
        if response.status_code == 404:
            raise FileNotFoundError(f"File not found: {self._sharepoint_file_name}")
        response.raise_for_status()
        return BytesIO(response.content)

    def read_sheets_with_metadata(self, sheets_list: list[str]) -> Dict[str, pd.DataFrame]:
        """
        Read multiple sheets by names and apply metadata-based normalization.
        Returns a dictionary {sheet_name: DataFrame}.
        """
        # Download workbook once
        excel_io = self._download_excel()

        # Validate sheets exist in metadata
        valid_sheets = [s["name"] for s in self.metadata["sheets"]]
        for sheet in sheets_list:
            if sheet not in valid_sheets:
                raise ValueError(f"Sheet '{sheet}' not found in metadata.")

        # Read only requested sheets
        df_dict = pd.read_excel(excel_io, sheet_name=sheets_list, engine="openpyxl")

        result = {}
        for sheet_name, df in df_dict.items():
            # Find metadata
            sheet_meta = next((s for s in self.metadata["sheets"] if s["name"] == sheet_name), None)
            if not sheet_meta:
                continue

            # Normalize column names
            def normalize(name: str):
                return "".join(name.split()).lower()

            excel_col_map = {normalize(c): c for c in df.columns}
            final_cols = {}

            for col_meta in sheet_meta["columns"]:
                meta_name = col_meta["name"]
                meta_type = col_meta["type"]
                normalized_meta_name = normalize(meta_name)

                if normalized_meta_name not in excel_col_map:
                    print(f"Warning: Column '{meta_name}' not found in Excel. Filling with NaN.")
                    df[meta_name] = pd.NA
                    final_cols[meta_name] = meta_name
                    continue

                excel_col_name = excel_col_map[normalized_meta_name]

                # Cast types
                if meta_type == "str":
                    df[excel_col_name] = df[excel_col_name].astype(str)
                elif meta_type == "float":
                    df[excel_col_name] = pd.to_numeric(df[excel_col_name], errors="coerce")
                elif meta_type == "datetime":
                    df[excel_col_name] = pd.to_datetime(df[excel_col_name], errors="coerce")

                # Map to metadata name
                df.rename(columns={excel_col_name: meta_name}, inplace=True)
                final_cols[meta_name] = meta_name

            # Reorder columns
            ordered_cols = [c["name"] for c in sorted(sheet_meta["columns"], key=lambda x: x["position"])]
            renamed_columns = [c["formatted_name"] for c in sorted(sheet_meta["columns"], key=lambda x: x["position"])]

            name_counts = {}
            renamed_columns_duplicates = []
            for name in renamed_columns:
                if name not in name_counts:
                    name_counts[name] = 0
                    renamed_columns_duplicates.append(name)  # first occurrence, no suffix
                else:
                    name_counts[name] += 1
                    renamed_columns_duplicates.append(f"{name}_{name_counts[name]}")  # subsequent occurrences get suffix

            df = df[ordered_cols]
            df.columns = renamed_columns_duplicates
            df = df.reset_index()
            df['index'] = df['index'].astype(int)  # Ensure type consistency for DB
            df.rename(columns={'index': 'instance_id'}, inplace=True)

            # Optionally save to CSV
            # df.to_csv(f"/app/app/sharepoint/{sheet_name}.csv", index=False)
            result[sheet_name] = df

        return result
