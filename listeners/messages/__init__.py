import re

from slack_bolt import App
from .message_listeners import register_message_listeners  # Import the message listener registration



# To receive messages from a channel or dm your app must be a member!
def register(app: App):
    register_message_listeners(app)

