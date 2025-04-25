import os
import logging
from dotenv import load_dotenv

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from listeners import register_listeners
from listeners.messages.message_listeners import register_message_listeners  # Updated import

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.DEBUG)

# Initialization
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)



# Register Command Listeners
register_listeners(app)

# Register Message Listeners
register_message_listeners(app)  # Register the message listeners



# Start Bolt app
if __name__ == "__main__":
    SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN")).start()
