import base64
from email.message import EmailMessage
import os
from dotenv import load_dotenv
import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import os
import pickle
# Gmail API utils
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
# for encoding/decoding messages in base64
from base64 import urlsafe_b64decode, urlsafe_b64encode
# for dealing with attachement MIME types
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from mimetypes import guess_type as guess_mime_type

# Load environment variables
load_dotenv()


our_email = "jennifer.tang@directagents.com"
def send_message(service, destination, obj, body, attachments=[]):
    return service.users().messages().send(
      userId="me",
      body=build_message(destination, obj, body, attachments)
    ).execute()

def build_message(destination, obj, body, attachments=[]):
    if not attachments: # no attachments given
        message = MIMEText(body)
        message['to'] = destination
        message['from'] = our_email
        message['subject'] = obj
    else:
        message = MIMEMultipart()
        message['to'] = destination
        message['from'] = our_email
        message['subject'] = obj
        message.attach(MIMEText(body))
        for filename in attachments:
            add_attachment(message, filename)
    return {'raw': urlsafe_b64encode(message.as_bytes()).decode()}

# Adds the attachment with the given filename to the given message
def add_attachment(message, filename):
    content_type, encoding = guess_mime_type(filename)
    if content_type is None or encoding is not None:
        content_type = 'application/octet-stream'
    main_type, sub_type = content_type.split('/', 1)
    if main_type == 'text':
        fp = open(filename, 'rb')
        msg = MIMEText(fp.read().decode(), _subtype=sub_type)
        fp.close()
    elif main_type == 'image':
        fp = open(filename, 'rb')
        msg = MIMEImage(fp.read(), _subtype=sub_type)
        fp.close()
    elif main_type == 'audio':
        fp = open(filename, 'rb')
        msg = MIMEAudio(fp.read(), _subtype=sub_type)
        fp.close()
    else:
        fp = open(filename, 'rb')
        msg = MIMEBase(main_type, sub_type)
        msg.set_payload(fp.read())
        fp.close()
    filename = os.path.basename(filename)
    msg.add_header('Content-Disposition', 'attachment', filename=filename)
    message.attach(msg)

def send_task_email(task, deadline, details, recipient_email=None):
    """
    Send an email with task details using Gmail API
    
    Args:
        task (str): The task description
        deadline (datetime): The task deadline
        details (str): Additional task details
        recipient_email (str, optional): Email recipient. If None, uses default from env.
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    # Use provided recipient or default from environment
    if recipient_email is None:
        recipient_email = os.environ.get("EMAIL_RECIPIENT")
    
    if not recipient_email:
        print("Missing recipient email. Please set EMAIL_RECIPIENT environment variable.")
        return False
    
    try:
        # Get credentials from environment
        creds, _ = google.auth.default()
        
        # Create Gmail API client
        service = build("gmail", "v1", credentials=creds)
        
        # Create email message
        message = EmailMessage()
        
        # Email body
        body = f"""
        <h2>New Task Created</h2>
        <p><strong>Task:</strong> {task}</p>
        <p><strong>Deadline:</strong> {deadline.strftime('%Y-%m-%d %H:%M')}</p>
        """
        
        if details:
            body += f"<p><strong>Details:</strong> {details}</p>"
        
        message.set_content(body, subtype='html')
        
        # Set email headers
        message["To"] = recipient_email
        message["Subject"] = f"New Task: {task}"
        
        # Encode message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        # Create message object
        create_message = {"raw": encoded_message}
        
        # Send message
        send_message = (
            service.users()
            .messages()
            .send(userId="me", body=create_message)
            .execute()
        )
        
        print(f'Message Id: {send_message["id"]}')
        return True
        
    except HttpError as error:
        print(f"An error occurred: {error}")
        return False
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
#SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
SCOPES = ["https://mail.google.com/"]

def gmail_authenticate():
    creds = None
    # the file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # if there are no (valid) credentials availablle, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

# get the Gmail API service
def get_gmail_service(task, deadline, details, original):
    service = gmail_authenticate()
    header = task + " - CONFIRMATION"
    body = "Task: " + task + "\n" + "Deadline: " + deadline + "\n" + "Details: " + details + "\n\n\n" + "Original Request: " + original
    send_message(service, "jennifer.tang@directagents.com", header, body, [])
    if send_message:
        return True
    else:
        return False
    

def main():
  """Shows basic usage of the Gmail API.
  Lists the user's Gmail labels.
  """
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
          "/Users/jennifertang/azure_slack_bot/credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    # Call the Gmail API
    service = build("gmail", "v1", credentials=creds)
    results = service.users().labels().list(userId="me").execute()
    labels = results.get("labels", [])

    if not labels:
      print("No labels found.")
      return
    print("Labels:")
    for label in labels:
      print(label["name"])

  except HttpError as error:
    # TODO(developer) - Handle errors from gmail API.
    print(f"An error occurred: {error}")


if __name__ == "__main__":
  main()