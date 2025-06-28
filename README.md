# Mailbot-9000

An intelligent email management system that automatically classifies incoming emails by importance level using local LLM models (ollama api) and organizes them into appropriate folders.

## Features

- **Automated Email Classification**: Uses passed in config to classify email in three categories: highly important (must be seen), medium important (should be seen; but later), low important (can be seen at spare time)
- **IMAP integration**: This is primarly designed for iCloud as Apple's iCloud email does not provide a lot of features. 
- **Caching**: Uses a local `.csv` file to store already seen emails making less calls to `llm model`
- **Configurable**: Manages everything through `.config` files

## Prerequisites

- Python 3.9 or higher
- For Ollama: A working Ollama installation (recommended for personal use. Download from: https://ollama.com)
    - ***If using Huggingface, you will need to change codebase to make this work. Currenlty, very limited support) For Hugging Face: A Hugging Face account and API token***

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/Mailbot-9000.git
   cd Mailbot-9000
   ```

2. Make the setup script executable and run it:
   ```bash
   chmod +x driver.sh
   ```

3. Configure `PROJECT_DIR` in `driver.sh` to match your directory. Directory can be found using `pwd`

4. Configure your settings:
   - Copy `mailbot/config/template_config.ini` to `mailbot/config/config.ini`
   - Edit `config.ini` with your email and AI model settings

5. Run `./driver.sh`. All outputs will be recorded on `python_run.log`

## Contributing

Contributions are welcome! Please feel free to submit pull requests.

## High level mermaid sequence diagram
```mermaid
sequenceDiagram
    participant Main as Main Process
    participant Config as ConfigParser
    participant IMAP as ImapService
    participant Cache as Cache System
    participant LLM as LLM Service
    participant Prompt as Prompt System
    participant Email as EmailWrapper

    Note over Main: System Initialization
    Main->>Config: Load config.ini
    Config-->>Main: Configuration loaded
    Main->>IMAP: Initialize IMAP connection
    IMAP->>IMAP: Create client & connect
    IMAP-->>Main: Connection established
    Main->>Cache: Initialize cache system
    Cache->>Cache: Ensure CSV file exists
    Cache-->>Main: Cache ready
    Main->>LLM: Initialize LLM (Ollama/HuggingFace)
    LLM->>LLM: Setup model & tokenizer
    LLM-->>Main: LLM ready

    Note over Main: Email Processing Loop
    Main->>IMAP: Get mailbox list
    IMAP-->>Main: List of mailboxes
    
    loop For each mailbox (excluding exceptions)
        Main->>IMAP: Fetch unread email IDs
        IMAP->>IMAP: Search for UNSEEN emails
        IMAP-->>Main: List of email IDs
        
        loop For each email ID
            Main->>IMAP: Fetch email content
            IMAP->>IMAP: Retrieve raw email data
            IMAP->>IMAP: Parse email headers & body
            IMAP->>Email: Create EmailWrapper
            Email-->>IMAP: Email object created
            IMAP-->>Main: EmailWrapper object
            
            alt Email fetch failed
                Main->>Main: Log error & skip to next email
            else Email fetched successfully
                Main->>Cache: Check if email exists
                Cache->>Cache: Hash subject & check sender
                Cache-->>Main: ImportanceLevel or None
                
                alt Email found in cache
                    Main->>IMAP: Move to appropriate folder
                    IMAP->>IMAP: Mark as unread & move
                    IMAP-->>Main: Email moved
                    Main->>Main: Log: Email already classified
                else Email not in cache
                    Main->>Prompt: Create ImportanceEvaluator
                    Prompt->>Prompt: Build classification prompt
                    Prompt-->>Main: Prompt object ready
                    
                    Main->>LLM: Generate classification
                    LLM->>LLM: Process prompt with model
                    LLM-->>Main: Classification response
                    
                    alt Valid LLM response
                        Main->>Main: Determine ImportanceLevel
                        Note over Main: 0.75+ = MOST_IMPORTANT<br/>0.4-0.75 = MEDIUM_IMPORTANT<br/>0.0-0.4 = LEAST_IMPORTANT
                        
                        Main->>Cache: Add classification record
                        Cache->>Cache: Store in CSV file
                        Cache-->>Main: Record added
                        
                        Main->>IMAP: Move to appropriate folder
                        IMAP->>IMAP: Mark as unread & move to folder
                        IMAP-->>Main: Email moved & classified
                        
                        Main->>Main: Log: Email classified & moved
                    else Invalid LLM response
                        Main->>Main: Log error & skip email
                    end
                end
            end
        end
    end
    
    Note over Main: Cleanup
    Main->>IMAP: Shutdown connection
    IMAP->>IMAP: Logout from server
    IMAP-->>Main: Connection closed
    Main->>Main: Process complete

    Note over Main,Email: Error Handling
    Note over Main: Throughout the process:<br/>- Network errors are handled gracefully<br/>- Invalid emails are skipped<br/>- Cache failures don't stop processing<br/>- LLM errors are logged and handled
```