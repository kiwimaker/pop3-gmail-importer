# POP3 to Gmail Importer v3.0

A production-ready email import daemon that imports emails from multiple POP3 accounts directly into Gmail using the Gmail API. By using Gmail API's native import functionality, this completely avoids SPF/DKIM/DMARC issues.

## What's New in v3.0

- **Gmail API Integration**: Direct email import using `messages.import()` API
- **SMTP Issues Eliminated**: Completely bypasses SPF/DKIM/DMARC validation failures
- **Gmail Native Processing**: Imported emails go through Gmail's spam filter and inbox classification
- **OAuth 2.0 Authentication**: Secure token-based authentication
- **Original Email Preservation**: Completely retains all headers, attachments, and metadata
- **Unread & Inbox Placement**: `labelIds` specification ensures emails are placed in inbox as unread

## Features

- **Multiple Account Support**: Import from up to 5 POP3 accounts to multiple Gmail accounts
- **Gmail API Import**: Uses `messages.import()` to preserve original email dates and headers
- **Duplicate Prevention**: UIDL-based tracking prevents duplicate imports even after crashes
- **Automatic Backup**: Optional email archive with configurable retention period
- **Secure Connections**: Full TLS/SSL support for POP3 with certificate verification
- **Safe Shutdown**: Safely handles Ctrl+C interrupts without data loss
- **Debug Mode**: Process only the latest 5 emails for testing (when deletion disabled)
- **Crash Recovery**: Atomic operations ensure no state loss during power outages or crashes

## Requirements

- **Python 3.9 or higher**
- POP3 email account with UIDL support
- **Gmail account** for email import
- **Google Cloud project** with Gmail API enabled (free to create)

## Quick Start

### 1. Google Cloud Setup

Before running the program, you need to set up Gmail API access:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable Gmail API:
   - Navigate to "APIs & Services" → "Library"
   - Search for "Gmail API" and enable it
4. Create OAuth 2.0 credentials:
   - Navigate to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - If prompted, configure OAuth consent screen:
     - User Type: External
     - App name: "POP3 to Gmail Importer" (or any name)
     - Add your Gmail address to Test users
     - Scope: Add `https://www.googleapis.com/auth/gmail.insert`
   - Application type: "Desktop app"
   - Download the JSON file
5. Rename the downloaded file to `credentials.json`
6. Place `credentials.json` in the project root directory

### 2. Initial Setup

1. Download or clone this project
2. Copy the sample configuration:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` file with your settings (see Configuration section)
4. Install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

### 3. Test Connections

Run the connection test program:

```bash
python test_connection.py
```

This will:
- Test POP3 connection
- Perform OAuth authentication (browser will open on first run)
- Save authentication tokens for future use
- Verify Gmail API access

**Important**: On first run, a browser will open for each Gmail account to authorize access. Click "Allow" to grant POP3 to Gmail Importer permission to import emails.

### 4. Run

Start the email importer:

```bash
python main.py
```

The program will:
- Check for new emails every 5 minutes (configurable)
- Import new emails via Gmail API
- Save local backups (if enabled)
- Log all activity to `logs/pop3_gmail_importer.log`

### 5. Stop

Press `Ctrl+C` to safely stop the program. The importer will complete processing the current email before exiting.

## Configuration

Edit the `.env` file to configure your email accounts.

### Global Settings

```bash
ACCOUNT_COUNT=5              # Number of accounts to configure (1-5)
CHECK_INTERVAL=300           # Check interval in seconds (300 = 5 minutes)
MAX_EMAILS_PER_LOOP=100      # Max emails to process per account per loop

# Log Settings
LOG_LEVEL=INFO               # DEBUG, INFO, WARNING, ERROR
LOG_FILE=logs/pop3_gmail_importer.log
LOG_MAX_BYTES=10485760       # 10MB per log file
LOG_BACKUP_COUNT=5           # Keep 5 rotated log files
```

### Per-Account Settings

For each account (replace `ACCOUNT1_` with `ACCOUNT2_`, `ACCOUNT3_`, etc.):

```bash
# Enable/disable this account
ACCOUNT1_ENABLED=true

# POP3 Settings (source email account)
ACCOUNT1_POP3_HOST=pop.example.com
ACCOUNT1_POP3_PORT=995                # Usually 995 for SSL/TLS
ACCOUNT1_POP3_USE_SSL=true
ACCOUNT1_POP3_VERIFY_CERT=true        # Recommended: true
ACCOUNT1_POP3_USERNAME=user@example.com
ACCOUNT1_POP3_PASSWORD=your_password_here

# Gmail API Settings (destination Gmail account)
ACCOUNT1_GMAIL_CREDENTIALS_FILE=credentials.json           # OAuth credentials
ACCOUNT1_GMAIL_TOKEN_FILE=tokens/token_account1.json       # Token storage
ACCOUNT1_GMAIL_TARGET_EMAIL=your-gmail@gmail.com           # Import destination
ACCOUNT1_GMAIL_LABEL_IDS=Label_123456                      # Optional: Gmail label IDs

# Deletion Settings
ACCOUNT1_DELETE_AFTER_FORWARD=false   # Debug: false, Production: true

# Backup Settings
ACCOUNT1_BACKUP_ENABLED=true
ACCOUNT1_BACKUP_DIR=backup/account1
ACCOUNT1_BACKUP_RETENTION_DAYS=90
```

### Important Notes

- **credentials.json**: Shared by all accounts (one file for the entire application)
- **Token files**: One per destination Gmail account
  - Example: If Account 1 and Account 3 both import to `your-gmail@gmail.com`, they can share the same token file:
    ```bash
    ACCOUNT1_GMAIL_TOKEN_FILE=tokens/token_gmail_a.json
    ACCOUNT3_GMAIL_TOKEN_FILE=tokens/token_gmail_a.json
    ```
- **DELETE_AFTER_FORWARD=false**: Debug mode - process only latest 5 emails, don't delete from server
- **DELETE_AFTER_FORWARD=true**: Production mode - delete from POP3 server after successful import

## Gmail Labels (Optional)

You can automatically apply Gmail labels to imported emails by setting `GMAIL_LABEL_IDS` per account. This is useful when importing from multiple POP3 accounts into the same Gmail, so you can tell which source each email came from.

### Finding your Gmail Label IDs

Gmail labels have internal IDs (e.g. `Label_123456`) that differ from the display name. To find them:

1. Go to the [Gmail API labels.list reference](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.labels/list)
2. Click **"Try this method"** (right-side panel)
3. In the `userId` field, type `me`
4. Click **"Execute"**
5. Authorize with your Gmail account when prompted
6. The response will list all your labels with their IDs:

```json
{
  "labels": [
    { "id": "INBOX", "name": "INBOX", "type": "system" },
    { "id": "Label_5", "name": "Work", "type": "user" },
    { "id": "Label_12", "name": "Personal", "type": "user" }
  ]
}
```

7. Copy the `id` value for the labels you want (e.g. `Label_5`)

### Configuration

Set the label ID(s) in your `.env` file:

```bash
# Single label
ACCOUNT1_GMAIL_LABEL_IDS=Label_5

# Multiple labels (comma-separated)
ACCOUNT1_GMAIL_LABEL_IDS=Label_5,Label_12
```

### Example: Multiple accounts with different labels

```bash
ACCOUNT_COUNT=3

# Personal email → labeled "Personal"
ACCOUNT1_GMAIL_LABEL_IDS=Label_12

# Work email → labeled "Work"
ACCOUNT2_GMAIL_LABEL_IDS=Label_5

# Newsletter account → labeled "Newsletters"
ACCOUNT3_GMAIL_LABEL_IDS=Label_28
```

If `GMAIL_LABEL_IDS` is empty or not set, emails are imported with just `INBOX` and `UNREAD` (default behavior).

## How It Works

1. **POP3 Retrieval**: Connect to POP3 server and retrieve new emails
2. **UIDL Tracking**: Check UIDL state to skip already-processed emails
3. **Local Backup**: Save email as `.eml` file (if enabled)
4. **Gmail API Import**: Call `messages.import()` with original RFC 822 email
   - **labelIds specification**: `['INBOX', 'UNREAD']` places email in inbox as unread
   - Without labelIds specification, emails will be imported as archived and read
5. **UIDL Recording**: Mark email as processed immediately after successful import
6. **Server Deletion**: Delete from POP3 server (production mode only)
7. **Cleanup**: Delete old backups and UIDL records (default 90 days)

## OAuth Authentication Details

### First Run
- Browser opens automatically
- Sign in with Gmail account
- Grant email import permission
- Token saved to `tokens/token_accountN.json`

### Subsequent Runs
- Token loaded automatically
- Auto-refresh when expired
- No browser interaction needed

### Multiple Gmail Destinations
When importing to multiple Gmail accounts, the OAuth flow runs once for each unique destination email.

## Troubleshooting

### "credentials.json not found"
- Download OAuth credentials from Google Cloud Console
- Rename to `credentials.json`
- Place in project root directory

### "OAuth authentication failed"
- Verify Gmail address is added to Test Users in Google Cloud Console
- Verify OAuth scope is correct: `https://www.googleapis.com/auth/gmail.insert`
- Try deleting token file and re-authenticating

### "Gmail API error: 403"
- Gmail address is not in the test users list
- Add it in Google Cloud Console → OAuth consent screen → Test users

### "POP3 connection failed"
- Verify host, port, username, and password
- Verify POP3 is enabled in your email provider
- Some providers require "app passwords" instead of regular passwords

## Security

- OAuth tokens stored with `600` permissions (owner read/write only)
- Passwords never saved in logs (masked with `***`)
- Email addresses partially masked in logs (`u***@example.com`)
- `.gitignore` configured to exclude all sensitive files:
  - `.env`
  - `credentials.json`
  - `tokens/`
  - `state/`
  - `backup/`

## Logs

Logs are saved to `logs/pop3_gmail_importer.log` with automatic rotation:
- Max size: 10MB per file
- Retention: 5 rotated files
- Format: `YYYY-MM-DD HH:MM:SS - LEVEL - Message`

## File Structure

```
pop3_gmail_importer/
├── .env                     # Configuration file (not in git)
├── .env.example             # Configuration template
├── credentials.json         # OAuth credentials (not in git)
├── main.py                  # Main program
├── test_connection.py       # Connection tester
├── requirements.txt         # Python dependencies
├── README.md                # This file (Japanese)
├── README_EN.md             # English README
├── tokens/                  # OAuth tokens (not in git)
│   ├── token_account1.json
│   └── token_account2.json
├── state/                   # UIDL state files (not in git)
│   ├── account1_uidl.jsonl
│   └── account2_uidl.jsonl
├── backup/                  # Email backups (not in git)
│   ├── account1/
│   └── account2/
└── logs/                    # Log files (not in git)
    └── pop3_gmail_importer.log
```

## License

This project is provided "as is" for personal use.

## Support

For issues or questions, please refer to:
1. This README
2. `requirements.md` for detailed specifications
3. Log file at `logs/pop3_gmail_importer.log`
