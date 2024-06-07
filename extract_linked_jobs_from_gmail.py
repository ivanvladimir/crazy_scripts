#  Check emails to extract information form linkedin offerts
#
#

from __future__ import print_function
from rich.prompt import Prompt
from rich import print
from rich.markdown import Markdown
import os
import os.path

import base64
from parsel import Selector

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

directory = os.path.expanduser(
    Prompt.ask("Which directory to use?", default="~/Downloads")
)

options = [
    f
    for f in os.listdir(directory)
    if f.endswith(".json") and f.startswith("client_secret")
]
options.sort()

credentials_file = Prompt.ask(
    "Select file with credentials", choices=options, default=options[-1]
)


def connect_to_service(directory, file):
    """Consults gmail for certain query"""
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                os.path.join(directory, file), SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API
        service = build("gmail", "v1", credentials=creds)
        return service

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f"An error occurred: {error}")


def get_jobs(str):
    pass


service = connect_to_service(directory, credentials_file)

results = (
    service.users()
    .messages()
    .list(userId="me", q="from:jobs-listings@linkedin.com")
    .execute()
)
mails = results.get("messages", [])

for mail in mails:
    msg = service.users().messages().get(userId="me", id=mail["id"]).execute()
    payload = msg["payload"]
    parts = payload.get("parts")
    body_html = None

    for part in parts:
        body = part.get("body")
        data = body.get("data")
        mimeType = part.get("mimeType")

        # with attachment
        if mimeType == "multipart/alternative":
            subparts = part.get("parts")
            for p in subparts:
                body = p.get("body")
                data = body.get("data")
                mimeType = p.get("mimeType")
                if mimeType == "text/plain":
                    body_message = base64.urlsafe_b64decode(data)
                elif mimeType == "text/html":
                    body_html = base64.urlsafe_b64decode(data)

        # without attachment
        elif mimeType == "text/plain":
            body_message = base64.urlsafe_b64decode(data)
        elif mimeType == "text/html":
            body_html = base64.urlsafe_b64decode(data)
            selector = Selector(text=str(body_html, "utf-8"))
            jobs = []
            for row in selector.xpath('//table[contains(@role, "presentation")]'):
                # title
                title = row.xpath('tbody/tr/td[contains(@class, "pb-0")]')
                if not title:
                    continue
                jobs.append({})
                jobs[-1]["description"] = title.xpath("a/text()").get(0).strip()
                jobs[-1]["url"] = (
                    title.xpath("a/@href")
                    .get()
                    .strip()
                    .split("/?track", 1)[0]
                    .replace("/comm", "")
                )
                # Extra
                extra = row.xpath('tbody/tr/td[contains(@class, "pb-0")]')
                jobs[-1]["place"] = extra.xpath("p/text()").get(1).strip()

lines = []
for job in jobs:
    lines.append(f"* {job['description']}, {job['place']}:  {job['url']}")

md = Markdown("\n".join(lines))

print(md)
print()
