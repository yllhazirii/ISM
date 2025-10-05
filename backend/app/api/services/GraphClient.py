import requests
import base64
import pandas as pd
from io import BytesIO
from msal import ConfidentialClientApplication
from app.core.config import settings


class GraphClient:
    def __init__(self, client_id, tenant_id, client_secret, graph_api, mail_user, site_domain, site_name):
        self.client_id = client_id
        self.tenant_id = tenant_id
        self.client_secret = client_secret
        self.graph_api = graph_api.rstrip("/")
        self.mail_user = mail_user
        self.site_domain = site_domain
        self.site_name = site_name
        self._access_token = None
        self._drive_id = None

    # -----------------------
    # AUTH
    # -----------------------
    def authenticate(self):
        app = ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}"
        )
        token = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        if "access_token" not in token:
            raise Exception("Failed to acquire token")
        self._access_token = token["access_token"]
        return self._access_token

    def _headers(self):
        if not self._access_token:
            self.authenticate()
        return {"Authorization": f"Bearer {self._access_token}"}

    # -----------------------
    # SHAREPOINT
    # -----------------------
    def get_drive_id(self):
        if self._drive_id:
            return self._drive_id
        url = f"{self.graph_api}/sites/{self.site_domain}:/sites/{self.site_name}:/drives"
        res = requests.get(url, headers=self._headers())
        res.raise_for_status()
        drives = res.json().get("value", [])
        if not drives:
            raise ValueError("No drives found for this site")
        self._drive_id = drives[0]["id"]
        return self._drive_id

    def read_excel_from_sharepoint(self, filename, sheet_name=None):
        """Reads Excel from SharePoint without downloading to disk"""
        drive_id = self.get_drive_id()
        file_path = f"/Shared Documents/{filename}"
        url = f"{self.graph_api}/drives/{drive_id}/root:{file_path}:/content"
        response = requests.get(url, headers=self._headers())
        response.raise_for_status()

        # Read into pandas directly from memory
        excel_data = BytesIO(response.content)
        df = pd.read_excel(excel_data, sheet_name=sheet_name, engine="openpyxl")
        return df

    # -----------------------
    # EMAILS
    # -----------------------
    def get_emails(self, top=10, distribution_list=None):
        """Get latest emails, optionally filter by distribution list"""
        url = f"{self.graph_api}/users/{self.mail_user}/mailFolders/Inbox/messages"
        url += f"?$top={top}&$orderby=receivedDateTime desc"
        response = requests.get(url, headers=self._headers())
        response.raise_for_status()
        messages = response.json().get("value", [])

        filtered = []
        for msg in messages:
            recipients = [recip["emailAddress"]["address"] for recip in msg.get("toRecipients", [])]
            if distribution_list:
                if not any(distribution_list.lower() in r.lower() for r in recipients):
                    continue
            filtered.append({
                "subject": msg.get("subject"),
                "from": msg.get("from", {}).get("emailAddress", {}).get("address"),
                "received": msg.get("receivedDateTime"),
                "to": recipients,
                "id": msg["id"]
            })
        return filtered

    def get_attachments(self, message_id):
        url = f"{self.graph_api}/users/{self.mail_user}/messages/{message_id}/attachments"
        response = requests.get(url, headers=self._headers())
        response.raise_for_status()
        attachments = []
        for att in response.json().get("value", []):
            if att["@odata.type"] == "#microsoft.graph.fileAttachment":
                filename = att["name"]
                content_bytes = base64.b64decode(att["contentBytes"])
                attachments.append((filename, content_bytes))
        return attachments


# # -----------------------
# # Example Usage
# # -----------------------
# if __name__ == "__main__":
#     client = GraphClient(
#         client_id=settings.CLIENT_ID,
#         tenant_id=settings.TENANT_ID,
#         client_secret=settings.CLIENT_SECRET,
#         graph_api=settings.GRAPH_API,
#         mail_user=settings.MAIL_USER,
#         site_domain=settings.SITE_DOMAIN,
#         site_name=settings.SITE_NAME,
#     )
#
#     # Read SharePoint Excel (specific sheet)
#     df = client.read_excel_from_sharepoint(settings.SHAREPOINT_FILE_NAME, sheet_name="Sheet1")
#     print(df.head())
#
#     # Read Emails sent to Inventory DL
#     emails = client.get_emails(top=10, distribution_list="Inventory")
#     for mail in emails:
#         print(mail)
