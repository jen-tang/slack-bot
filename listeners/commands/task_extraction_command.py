import json
from datetime import date
import datetime
import traceback
from logging import Logger
from slack_bolt import Ack, Respond
from langchain_openai.chat_models import AzureChatOpenAI
import requests
import pytz
# Import your AzureChatOpenAI from your Azure OpenAI client package
# e.g., from azure_openai import AzureChatOpenAI
today = date.today()
client = "viki"
def ai_extract_task_deadline(message):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    extraction_prompt = f"""You are an AI assistant that extracts a task and a deadline from a conversational message for task management purposes.

Instructions:

1. Output a valid JSON object exactly in the following format with no extra text:
   {{"task": <task description or null>, "deadline": <deadline as YYYY-MM-DD HH:mm or null>, "timeProvided": <true or false>, "details": <additional task details or null>}}

2. The "task" key should contain the extracted task description, or null if no task is found.

3. The "deadline" key should contain the computed deadline formatted as YYYY-MM-DD HH:mm, or null if no deadline is mentioned.
   - Compute the deadline using any relative date references (e.g., "tomorrow", "Friday", "next Monday") based on today's date.
   - If no explicit time is provided, use the default time of 00:00 for the computed date without adding an extra day.

4. The "timeProvided" key must be:
   - true if an explicit time is provided in the message (for example, "at 8am", "14:00", etc.).
   - false if no explicit time is provided.

5. Today's date is provided as {today}. Compute any relative dates based on this value.
6. The "details" key should contain any additional details or context about the task, or null if no additional details are present.

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
        # Hardcoded credentials with CORRECT parameter naming
        client = AzureChatOpenAI(
            api_key="8ARZDFxrDQtiv8v27HmctsxYVHcQ2CqRIYAZMtT3bbnWGv64c6KnJQQJ99BDACHYHv6XJ3w3AAABACOG6ML0",
            api_version="2024-02-15-preview",
            azure_endpoint="https://gmail-filter.openai.azure.com",
            deployment_name="gpt-4o-mini",
            temperature=0.0
        )
        
        response = client.invoke(extraction_prompt)
        
        result = json.loads(response.content)
        task = result.get("task")
        deadline_str = result.get("deadline")
        deadline = datetime.datetime.strptime(deadline_str, "%Y-%m-%d %H:%M") if deadline_str else None
        time_provided = result.get("timeProvided")
        details = result.get("details")
        return task, deadline, time_provided, details
        
    except Exception as e:
        print(f"Error in AI extraction: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return None, None, None, None

def task_extraction_command_callback(command, ack: Ack, respond: Respond, logger: Logger):
    try:
        message = command["text"]
        logger.info(f"Processing task extraction for message: {message}")
        
        task, deadline, time_provided, details = ai_extract_task_deadline(message)
        
        if task and deadline:
            response_text = f"I've extracted the following task to send to the team:\n"
            response_text += f"*Task:* {task}\n"
            response_text += f"*Deadline:* {deadline.strftime('%Y-%m-%d %H:%M')}\n"
            if details:
                response_text += f"*Details:* {details}\n"
            # Return the response as part of the acknowledgment with response_type set to "in_channel"
            ack({
                "response_type": "in_channel",
                "text": response_text
            })
        else:
            # If extraction fails, you might choose to send an ephemeral message.
            ack({
                "response_type": "ephemeral",
                "text": "I couldn't extract a clear task and deadline from your message. Please check the logs for details."
            })
            
    except Exception as e:
        logger.error(f"Error in task extraction: {e}")
        logger.error(traceback.format_exc())
        ack({
            "response_type": "ephemeral",
            "text": f"Sorry, I encountered an error while processing your message: {str(e)}"
        })
    # clickup section
    


    # Localize it to your local timezone (e.g., America/New_York)
    local_tz = pytz.timezone("America/New_York")
    deadline_local = local_tz.localize(deadline)

    # Convert to UTC correctly
    deadline_utc = deadline_local.astimezone(datetime.timezone.utc)
    # Get Unix timestamp (in seconds) as a float
    deadline_unix = deadline_utc.timestamp()*1000
    print(deadline_unix)



    url = "https://api.clickup.com/api/v2/list/901109414101/task"
    payload = {
        "name": task,
        "description": details,
        "due_date": int(deadline_unix),
        "due_date_time": True,
        "tags": [client]
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": "pk_81499542_V6BGC0JBMHU4UHRA9HPKTPCHQLT98V18"
    }

    response = requests.post(url, json=payload, headers=headers)

    print(response.text)








