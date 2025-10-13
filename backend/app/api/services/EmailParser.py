import os
import json
from datetime import datetime
from typing import Dict, Any
from app.core.config import settings
import requests
import pandas as pd
from app.api.services.GraphClient import GraphClient
from bs4 import BeautifulSoup
import openai


class EmailParser():
    def __init__(self, graph_client: 'GraphClient', mail_user: str = settings.MAIL_USER):
        # Composition: The parser HAS A GraphClient
        self.client = graph_client
        self.mail_user = mail_user

        # Optional: Assign frequently used properties for cleaner method calls (Hybrid approach)
        self._headers = self.client._headers
        self.graph_api = self.client.graph_api

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
            if distribution_list and not any(distribution_list.lower() in r.lower() for r in recipients):
                continue

            filtered.append({
                "id": msg["id"],
                "subject": msg.get("subject"),
                "from": msg.get("from", {}).get("emailAddress", {}).get("address"),
                "received": msg.get("receivedDateTime"),
                "to": recipients
            })
        return filtered

    def get_email_body(self, message_id, prefer_html=False):
        url = f"{self.graph_api}/users/{self.mail_user}/messages/{message_id}"
        response = requests.get(url, headers=self._headers())
        response.raise_for_status()
        msg = response.json()

        body = msg.get("body", {}).get("content", "")
        if not body:
            return ""

        if not prefer_html:
            return BeautifulSoup(body, "html.parser").get_text(separator=" ", strip=True)
        return body

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

        # ----------------------
        # -
        # AI EXTRACTION
        # -----------------------
    def parse_with_azure_openai(self, email_text: str, attachment_text: str = ""):
        openai.api_type = "azure"
        openai.api_base = settings.AZURE_OPENAI_ENDPOINT
        openai.api_key = settings.AZURE_OPENAI_API_KEY
        openai.api_version = settings.AZURE_OPENAI_API_VERSION

        prompt = f"""
        Extract the following fields from this vendor email and attachment:
        Country, Location, Qty, Size, Condition, Specs, Price, Vendor, Availability.

        Email content:
        {email_text}

        Attachment content:
        {attachment_text}

        Return the result as a JSON object.
        """

        response = openai.ChatCompletion.create(
            engine=settings.AZURE_OPENAI_DEPLOYMENT,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

        result = response["choices"][0]["message"]["content"]

        try:
            return json.loads(result)
        except json.JSONDecodeError:
            cleaned = result.strip("` \n")
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            try:
                return json.loads(cleaned)
            except Exception as e:
                raise ValueError(f"Failed to parse LLM response as JSON. Raw: {result}") from e

    def process_inbox(self, top=5, distribution_list=None):
        """Fetch emails, parse body + attachments, send to LLM, return structured list"""
        emails = self.get_emails(top=top, distribution_list=distribution_list)
        results = []

        for mail in emails:
            message_id = mail["id"]
            body = self.get_email_body(message_id)

            attachments = self.get_attachments(message_id)
            attachment_text = ""
            for filename, content in attachments:
                if filename.endswith(".xlsx"):
                    df = pd.read_excel(BytesIO(content), engine="openpyxl")
                    attachment_text += df.to_string(index=False) + "\n"
                elif filename.endswith(".csv"):
                    df = pd.read_csv(BytesIO(content))
                    attachment_text += df.to_string(index=False) + "\n"
                elif filename.endswith(".txt"):
                    attachment_text += content.decode(errors="ignore") + "\n"

            try:
                parsed = self.parse_with_azure_openai(body, attachment_text)
                results.append({
                    "email_id": message_id,
                    "subject": mail["subject"],
                    "from": mail["from"],
                    "received": mail["received"],
                    "parsed": parsed
                })
            except Exception as e:
                results.append({
                    "email_id": message_id,
                    "subject": mail["subject"],
                    "from": mail["from"],
                    "received": mail["received"],
                    "error": str(e)
                })

        return results
