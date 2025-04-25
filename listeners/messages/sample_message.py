from logging import Logger

from slack_bolt import BoltContext, Say


def sample_message_callback(context: BoltContext, say: Say, logger: Logger):
    try:
        greeting = context["matches"][0]
        say(f"{greeting}, how are you?")

        # Example: If you want to include a file URL in the response
        # Assuming you have a way to retrieve the last file URL (e.g., from a global variable)
        last_file_url = context.get("last_file_url")  # Retrieve the last file URL from context or a global variable
        if last_file_url:
            say(f"Here is the last file shared: {last_file_url}")
    except Exception as e:
        logger.error(e)
