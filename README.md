# Mailbot-9000

A smart email management bot that can automatically remove spam emails. It supports both Hugging Face models and Ollama for local inference.

## Features

- Automated email processing and response generation
- Support for both Hugging Face and Ollama AI models
- Configurable IMAP settings for different email providers
- Spam folder management
- Customizable AI model parameters

## Prerequisites

- Python 3.9 or higher
- For Ollama: A working Ollama installation (recommended for personal use)
- (If using Huggingface, you will need to change codebase to make this work. Currenlty, very limited support) For Hugging Face: A Hugging Face account and API token

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/Mailbot-9000.git
   cd Mailbot-9000
   ```

2. Make the setup script executable and run it:
   ```bash
   chmod +x setup.sh
   source setup.sh
   ```

3. Configure your settings:
   - Copy `mailbot/config/template_config.ini` to `mailbot/config/config.ini`
   - Edit `config.ini` with your email and AI model settings

## Configuration

### Email Settings (IMAP)
In your `config.ini`, configure the following IMAP settings:
```ini
[IMAP]
server = your.email.server  # e.g., imap.gmail.com
port = your_port           # e.g., 993
username = your_email
password = your_password
spam_folder = Junk        # or your spam folder name
```

### AI Model Setup

#### Option 1: Ollama (Recommended for Personal Use)
1. Install Ollama from [ollama.ai](https://ollama.ai)
2. Configure Ollama settings in `config.ini`:
   ```ini
   [OLLAMA]
   ollama_base_url = http://localhost:11434/api
   stream = false
   keep_alive = 5
   think = false
   ```
3. Make sure you have the desired model installed in Ollama

#### Option 2: Hugging Face
1. Create a Hugging Face account and get your API token
2. Configure Hugging Face settings in `config.ini`:
   ```ini
   [HUGGINGFACE]
   token = your_huggingface_token
   max_new_tokens = 500
   ```

## Usage

After configuration:

1. Make sure your virtual environment is activated:
   ```bash
   source mailbot9000/bin/activate
   ```

2. Run the main script:
   ```bash
   python __init__.py
   ```

## Contributing

Contributions are welcome! Please feel free to submit pull requests.

## Usecases
1. When to notify users
2. Less spam emails 