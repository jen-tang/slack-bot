import listeners.commands.task_extraction_command as task_cmd
import requests
import os
from io import BytesIO 
import re
from requests.auth import AuthBase
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
class BearerAuth(AuthBase):
    """Attaches HTTP Bearer Token to each request, even on redirects."""
    def __init__(self, token):
        self.token = token
    def __call__(self, r):
        r.headers['Authorization'] = f'Bearer {self.token}'
        return r

def register_message_listeners(app):


# Handle all message events, including file shares
    @app.event("message")
    def handle_message_events(body, logger):
        logger.info(f"Received message event: {body}") 
        log_all_messages(body, logger)# Log the entire message event for debugging
        
"""     @app.message("")  # This will capture all messages
    def handle_message(message, say, logger):
        log_all_messages(message, logger) """
        
        
        
def log_all_messages(message, logger):
    global last_processed_timestamp, last_created_task_id, last_file_url, is_listening
    #logger.info(f"Checking is_listening: {is_listening}")  # Log the current state

    if message.get('subtype') == 'bot_message':
        logger.info("Ignoring bot message.")
        return  # Ignore messages from the bot

    logger.info(f"Received message: {message}")  # Log the received message
    
    #logger.info(f"New message: {message['text']}")


    # Update the last processed timestamp
    # last_processed_timestamp = message['ts']  # Update the timestamp to the current message's timestamp


    # 3. Ignore messages the bot itself posted
    if message.get('subtype') == 'bot_message':
        logger.info("Ignoring bot message.")
        return

    # 4. Log the payload for debug
    logger.info(f"Received message: {message}")

    # 5. If we’ve created a ClickUp task, look for files to attach
    if task_cmd.last_created_task_id:
        if 'files' in message['event']:
            for file_info in message['event']['files']:
                update_clickup_task_with_file(task_cmd.last_created_task_id, file_info, logger)
        else:
            logger.info("No attachments found in this message.")
    else:
        logger.info("No active task to update.")
    



def slugify_filename(name):
    base, ext = os.path.splitext(name or "")
    base = re.sub(r'[^a-z0-9_-]', '_', base.lower())
    ext = ext.lower() or ""
    return f"{base}{ext}"

def update_clickup_task_with_file(task_id, file_info, logger):
    """
    Downloads a Slack file via its private download URL (with Bearer token)
    and uploads it as an attachment to the given ClickUp task.
    """
    # 0) Env checks
    slack_token = os.environ.get("SLACK_BOT_TOKEN")
    clickup_token = os.environ.get("CLICKUP_API_KEY")
    if not slack_token or not clickup_token:
        logger.error("Missing SLACK_BOT_TOKEN or CLICKUP_API_KEY in environment")
        return

    # 1) Build URL + headers for Slack download
    download_url = file_info.get("url_private_download") or file_info.get("url_private")
    slack_headers = {
        "Authorization": f"Bearer {slack_token}"
    }

    # 2) Download the raw bytes (follow redirects with the same header)
    try:
        resp = requests.get(
            download_url,
            headers=slack_headers,
            allow_redirects=True,  # ensures redirects carry your auth header
            stream=True
        )
        resp.raise_for_status()
        file_bytes = resp.content
        content_type = resp.headers.get(
            "content-type",
            file_info.get("mimetype", "application/octet-stream")
        )
    except Exception as e:
        logger.error(f"Error downloading Slack file {file_info['id']}: {e}")
        return

    # 3) Extract filename
    cd = resp.headers.get("content-disposition", "")
    m = re.search(r'filename\*?=\s*(?:UTF-8\'\')?"?([^";]+)"?', cd)
    filename = (
        m.group(1)
        if m
        else file_info.get("name") or file_info.get("title") or file_info["id"]
    )

    # 4) Prepare for ClickUp
    bio = BytesIO(file_bytes)
    bio.seek(0)
    clickup_url = f"https://api.clickup.com/api/v2/task/{task_id}/attachment"
    files_payload = {
        "attachment": (filename, bio, content_type)
    }
    clickup_headers = {"Authorization": clickup_token}

    # 5) Upload
    try:
        upload = requests.post(clickup_url, headers=clickup_headers, files=files_payload)
        if upload.ok:
            logger.info(f"✅ Uploaded {filename} to ClickUp task {task_id}")
        else:
            logger.error(f"❌ ClickUp upload failed ({upload.status_code}): {upload.text}")
    except Exception as e:
        logger.error(f"Error uploading to ClickUp: {e}")