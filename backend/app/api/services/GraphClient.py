from msal import ConfidentialClientApplication
from app.core.config import settings


class GraphClient:
    def __init__(self, client_id=settings.CLIENT_ID, tenant_id=settings.TENANT_ID,
                 client_secret=settings.CLIENT_SECRET, graph_api=settings.GRAPH_API):
        self.client_id = client_id
        self.tenant_id = tenant_id
        self.client_secret = client_secret
        self.graph_api = graph_api.rstrip("/")
        self._access_token = None

    def authenticate(self):
        if self._access_token:  # simple cache
            return self._access_token

        app = ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}"
        )
        token = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        if "access_token" not in token:
            raise Exception(f"Failed to acquire token: {token}")
        self._access_token = token["access_token"]
        return self._access_token

    def _headers(self):
        if not self._access_token:
            self.authenticate()
        return {"Authorization": f"Bearer {self._access_token}"}


