# Azure Slack Bot

## Project Description
This project is a Slack bot that integrates with ClickUp to manage tasks. It listens for commands in Slack, extracts task details, and uploads attachments to ClickUp.

## Features
- Extracts tasks and deadlines from Slack messages.
- Uploads file attachments from Slack to ClickUp.
- Sends email notifications for task updates.
- Handles multiple message events, including file shares.

## Technologies Used
- Python
- Slack SDK
- ClickUp API
- Azure App Service
- Langchain OpenAI (for AI task extraction)

## Prerequisites
- Python 3.x
- Slack Bot Token
- ClickUp API Key
- Azure Account

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd azure_slack_bot
   ```

2. **Create a virtual environment** (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the root directory and add the following:
   ```plaintext
   SLACK_BOT_TOKEN=<your-slack-bot-token>
   CLICKUP_API_KEY=<your-clickup-api-key>
   AZURE_OPENAI_API_KEY=<your-azure-openai-api-key>
   AZURE_OPENAI_API_VERSION=<your-azure-openai-api-version>
   AZURE_OPENAI_ENDPOINT=<your-azure-openai-endpoint>
   AZURE_OPENAI_DEPLOYMENT_NAME=<your-azure-openai-deployment-name>
   CLICKUP_LIST_ID=<your-clickup-list-id>
   ```

## Usage

1. **Run the application locally**:
   ```bash
   python app.py
   ```

2. **Deploy to Azure**:
   Follow the instructions in the deployment section to deploy your application to Azure App Service.

3. **Interact with the bot**:
   Use the `/task` command in your Slack workspace to create tasks and upload attachments.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments
- Slack API documentation
- ClickUp API documentation
- Azure documentation
