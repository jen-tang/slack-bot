from slack_bolt import App
from .sample_command import sample_command_callback
from .task_extraction_command import task_extraction_command_callback
import logging
import traceback
import os
from langchain_openai.chat_models import AzureChatOpenAI

logger = logging.getLogger(__name__)


def register(app: App):
#    app.command("/sample-command")(sample_command_callback)
    app.command("/task")(task_extraction_command_callback)

