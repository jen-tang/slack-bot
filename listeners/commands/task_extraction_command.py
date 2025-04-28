import json
from datetime import date, datetime, timezone
import traceback
from logging import Logger
from slack_bolt import Ack, Respond
from langchain_openai import AzureChatOpenAI
import requests
import pytz
import os
#from dotenv import load_dotenv
# Import your AzureChatOpenAI from your Azure OpenAI client package
# e.g., from azure_openai import AzureChatOpenAI
from .email_service import get_gmail_service, send_task_email
import time
from threading import Thread

# Load environment variables
#load_dotenv()

today = date.today()
client = "viki"

# Global variable to store the last processed timestamp
last_processed_timestamp = None

# Global variable to store the last created task ID
last_created_task_id = None

# Global variable to control message listening
is_listening = False

def ai_extract_task_deadline(message):
    today = datetime.now().strftime("%Y-%m-%d")
    extraction_prompt = f"""You are an AI assistant whose sole job is to read a user's conversational message and output a JSON object describing:

1. **task** — the action to be done (string or `null` if none)  
2. **deadline** — the due date/time in `YYYY-MM-DD HH:mm` format (string or `null` if none)  
3. **timeProvided** — `true` if the user specified a time (e.g. "at 8 am", "14:00"), otherwise `false`  
4. **details** — any extra context, metrics, or parameters mentioned (string or `null`)

---

### Requirements

1. **JSON Output**  
   - Output exactly one JSON object in this form, with no extra text:  
   {{"task": <task description or null>, "deadline": <deadline as YYYY-MM-DD HH:mm or null>, "timeProvided": <true or false>, "details": <additional task details or null>}}

2. **task**  
   - The "task" key should contain the extracted task description. There should always be a task.

3. **deadline**  
   - Parse any explicit dates or relative expressions ("tomorrow", "next Monday", "Friday") using the provided `{today}`.  
   - Format as `YYYY-MM-DD HH:mm`.  
   - If no time is given, default to `00:00`.  
   - Use `null` if no deadline is mentioned.

4. **timeProvided**  
   - `true` only when a specific time appears in the message (e.g., "at 8 AM", "14:00"); otherwise `false`.

5. **details**  
   - Do not summarize. Capture **all** additional context other than task: numbers, metrics, deliverables, and other relevant info.  
   - Use `null` if there are no extra details.

Examples:
- Input: "Remind me to call John tomorrow" with {today} = 2025-04-08.
  - "tomorrow" computes as 2025-04-09 with default time 00:00.
  - Since no explicit time is provided, "timeProvided" is false.
  - Expected output: {{"task": "Call John", "deadline": "2025-04-09 00:00", "timeProvided": false, "details": null}}

- Input: "Remind me to call John tomorrow at 8am" with {today} = 2025-04-08.
  - "tomorrow at 8am" computes as 2025-04-09 08:00.
  - An explicit time is provided, so "timeProvided" is true.
  - Expected output: {{"task": "Call John", "deadline": "2025-04-09 08:00", "timeProvided": true, "details": null}}


Now extract the task and deadline from the following message:
\"\"\"{message}\"\"\"
"""
    
    try:
        # Use environment variables for Azure OpenAI credentials
        client = AzureChatOpenAI(
            api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
            api_version=os.environ.get("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
            deployment_name=os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME"),
            temperature=0.2
        )
        
        response = client.invoke(extraction_prompt)
        
        result = json.loads(response.content)
        print(f"AI Extraction Result: {result}")  # Log the result
        
        task = result.get("task")
        deadline_str = result.get("deadline")
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M") if deadline_str else None
        time_provided = result.get("timeProvided")
        details = result.get("details")
        return task, deadline, time_provided, details
        
    except Exception as e:
        print(f"Error in AI extraction: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return None, None, None, None


def task_extraction_command_callback(command, ack: Ack, respond: Respond, logger: Logger):
    global last_processed_timestamp, last_created_task_id, is_listening
    try:
        message = command["text"]
        logger.info(f"Processing task extraction for message: {message}")
        
        task, deadline, time_provided, details = ai_extract_task_deadline(message)
        
        if task:
            response_text = f"I've grabbed the following request to send to the team:\n"
            response_text += f"*Task:* {task}\n"
            
            if deadline:
                response_text += f"*Deadline:* {deadline.strftime('%Y-%m-%d %H:%M')}\n"
                # Localize it to your local timezone (e.g., America/New_York)
                local_tz = pytz.timezone("America/New_York")
                deadline_local = local_tz.localize(deadline)

                # Convert to UTC correctly
                deadline_utc = deadline_local.astimezone(timezone.utc)
                # Get Unix timestamp (in seconds) as a float
                deadline_unix = deadline_utc.timestamp() * 1000
            else:
                response_text += "*Deadline:* Not specified\n"  # Handle the case where deadline is None
                deadline = "Not specified"
            
            if details:
                response_text += f"*Details:* {details}\n"
            else:
                details = "Not specified"
            
            # Send email notification
            email_sent = get_gmail_service(task, deadline, details, message)
            if email_sent:
                response_text += "\nEmail notification has been sent."
            else:
                response_text += "\nFailed to send email notification."
            
            # Prepare ClickUp API payload
            payload = {
                "name": task,
                "description": details,
                "due_date": int(deadline_unix) if not isinstance(deadline, str) else None,  # Handle None deadline
                "due_date_time": time_provided,
                "tags": [client]
            }
            
            # Use environment variables for ClickUp API
            list_id = os.environ.get("CLICKUP_LIST_ID")
            url = f"https://api.clickup.com/api/v2/list/{list_id}/task"
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "Authorization": os.environ.get("CLICKUP_API_KEY")
            }

            response = requests.post(url, json=payload, headers=headers)
            json_response = json.loads(response.text)
            last_created_task_id = json_response.get("id")  # Store the task ID
            logger.info(f"Created task in ClickUp with ID: {last_created_task_id}")
            # Set the listening flag to True
            is_listening = True
            logger.info("Message listener activated after /task command.")

            # Return the response as part of the acknowledgment with response_type set to "in_channel"
            ack({
                "response_type": "in_channel",
                "text": response_text
            })

        else:
            # If extraction fails, you might choose to send an ephemeral message.
            ack({
                "response_type": "ephemeral",
                "text": "I couldn't extract a clear task from your message. Please check the logs for details."
            })
            

        
    except Exception as e:
        logger.error(f"Error in task extraction: {e}")
        logger.error(traceback.format_exc())
        ack({
            "response_type": "ephemeral",
            "text": f"Sorry, I encountered an error while processing your message: {str(e)}"
        })










