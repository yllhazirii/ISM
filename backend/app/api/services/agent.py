from fastapi import FastAPI
from app.core.config import settings
from app.services.graph_client import GraphClient
import pandas as pd
from io import BytesIO
import openai
import json

app = FastAPI()

# Initialize GraphClient
client = GraphClient(
    client_id=settings.CLIENT_ID,
    tenant_id=settings.TENANT_ID,
    client_secret=settings.CLIENT_SECRET,
    graph_api=settings.GRAPH_API,
    mail_user=settings.MAIL_USER,
    site_domain=settings.SITE_DOMAIN,
    site_name=settings.SITE_NAME,
)

# Azure OpenAI setup
openai.api_type = "azure"
openai.api_base = settings.AZURE_OPENAI_ENDPOINT
openai.api_key = settings.AZURE_OPENAI_API_KEY
openai.api_version = settings.AZURE_OPENAI_API_VERSION


def parse_with_azure_openai(email_text: str, attachment_text: str = ""):
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
    return json.loads(result)


@app.get("/agent/parse-latest")
def run_agent(top: int = 5):
    emails = client.get_emails(top=top)
    results = []

    for email in emails:
        message_id = email["id"]
        attachments = client.get_attachments(message_id)

        # Placeholder: you can add get_email_body() if needed
        email_body = f"Subject: {email['subject']}\nFrom: {email['from']}\nReceived: {email['received']}"

        attachment_text = ""
        for filename, content in attachments:
            if filename.endswith(".xlsx"):
                df = pd.read_excel(BytesIO(content), engine="openpyxl")
                attachment_text += df.to_string(index=False)

        # Decision logic
        if attachment_text:
            source = "attachment"
        elif "availability" in email_body.lower():
            source = "body"
        else:
            source = "both"

        parsed = parse_with_azure_openai(
            email_text=email_body if source in ["body", "both"] else "",
            attachment_text=attachment_text if source in ["attachment", "both"] else ""
        )

        results.append({
            "email_id": message_id,
            "vendor": email["from"],
            "parsed": parsed
        })

    return {"parsed_emails": results}
