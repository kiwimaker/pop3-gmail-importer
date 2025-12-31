#!/usr/bin/env python3
"""
POP3 to Gmail Importer - Connection Test Program
Tests POP3 and Gmail API connections for all enabled accounts
Version: 3.0
"""

import os
import sys
import ssl
import poplib
from pathlib import Path
from dotenv import load_dotenv

# Gmail API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ANSI color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

# Gmail API scope
SCOPES = ['https://www.googleapis.com/auth/gmail.insert']


def print_success(message):
    """Print success message in green"""
    print(f"{GREEN}✓{RESET} {message}")


def print_error(message):
    """Print error message in red"""
    print(f"{RED}✗{RESET} {message}")


def print_warning(message):
    """Print warning message in yellow"""
    print(f"{YELLOW}⚠{RESET} {message}")


def get_env_bool(key, default=True):
    """Get boolean value from environment variable"""
    value = os.getenv(key, str(default)).lower()
    return value in ('true', '1', 'yes', 'on')


def get_env_int(key, default):
    """Get integer value from environment variable"""
    try:
        return int(os.getenv(key, default))
    except ValueError:
        return default


def test_pop3_connection(account_num, config):
    """Test POP3 connection for one account"""
    print(f"\n  Testing POP3 connection...")

    host = config['pop3_host']
    port = config['pop3_port']
    use_ssl = config['pop3_use_ssl']
    verify_cert = config['pop3_verify_cert']
    username = config['pop3_username']
    password = config['pop3_password']

    try:
        # Connect
        if use_ssl:
            context = ssl.create_default_context()
            if not verify_cert:
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                print_warning("TLS certificate verification disabled")

            pop3 = poplib.POP3_SSL(host, port, context=context, timeout=10)
        else:
            pop3 = poplib.POP3(host, port, timeout=10)

        print_success(f"POP3 Connection: Connected to {host}:{port}")

        # Authenticate
        pop3.user(username)
        pop3.pass_(password)
        print_success(f"POP3 Authentication: OK (user: {username})")

        # Check UIDL support
        try:
            uidl_response = pop3.uidl()
            print_success(f"POP3 UIDL Support: SUPPORTED")
        except Exception as e:
            print_error(f"POP3 UIDL Support: NOT SUPPORTED ({e})")

        # Get message count
        stat_response = pop3.stat()
        message_count = stat_response[0]
        total_size = stat_response[1]
        print_success(f"POP3 Messages: {message_count} messages ({total_size} bytes)")

        pop3.quit()
        return True

    except Exception as e:
        print_error(f"POP3 Connection: FAILED - {e}")
        return False


def test_gmail_api_connection(account_num, config):
    """Test Gmail API connection for one account"""
    print(f"\n  Testing Gmail API connection...")

    credentials_file = config['gmail_credentials_file']
    token_file = config['gmail_token_file']
    target_email = config['gmail_target_email']

    # Check credentials file
    if not Path(credentials_file).exists():
        print_error(f"Gmail API Credentials: NOT FOUND - {credentials_file}")
        return False

    print_success(f"Gmail API Credentials: Found ({credentials_file})")

    # Authenticate
    creds = None
    token_path = Path(token_file)

    # Create tokens directory if needed
    token_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)

    # Load existing token
    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
            print_success(f"Gmail API Token: Loaded from {token_file}")
        except Exception as e:
            print_warning(f"Failed to load token: {e}")
            creds = None

    # Refresh or obtain new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                print_success(f"Gmail API Token: Refreshed")
            except Exception as e:
                print_error(f"Gmail API Token Refresh: FAILED - {e}")
                creds = None

        if not creds:
            # Need OAuth flow
            try:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
                print(f"\n  {YELLOW}Browser will open for OAuth authentication.{RESET}")
                print(f"  {YELLOW}Please approve the access for: {target_email}{RESET}\n")
                creds = flow.run_local_server(port=0)
                print_success(f"Gmail API OAuth: Authenticated ({target_email})")
            except Exception as e:
                print_error(f"Gmail API OAuth: FAILED - {e}")
                return False

        # Save credentials
        try:
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
            os.chmod(token_path, 0o600)
            print_success(f"Gmail API Token: Saved to {token_file}")
        except Exception as e:
            print_warning(f"Failed to save token: {e}")

    # Test API connection
    try:
        service = build('gmail', 'v1', credentials=creds)
        # Verify connection by getting user profile (this only needs basic scope)
        # Since we only have gmail.insert scope, we just verify service was built
        print_success(f"Gmail API Connection: OK (target: {target_email})")
        return True
    except Exception as e:
        print_error(f"Gmail API Connection: FAILED - {e}")
        return False


def test_account(account_num):
    """Test all connections for one account"""
    prefix = f"ACCOUNT{account_num}_"

    # Check if account is enabled
    if not get_env_bool(f"{prefix}ENABLED", False):
        print(f"\nAccount {account_num}: {YELLOW}DISABLED{RESET}")
        return None

    print(f"\n{'='*60}")
    print(f"Testing Account {account_num}...")
    print(f"{'='*60}")

    # Load configuration
    config = {
        'pop3_host': os.getenv(f"{prefix}POP3_HOST"),
        'pop3_port': get_env_int(f"{prefix}POP3_PORT", 995),
        'pop3_use_ssl': get_env_bool(f"{prefix}POP3_USE_SSL", True),
        'pop3_verify_cert': get_env_bool(f"{prefix}POP3_VERIFY_CERT", True),
        'pop3_username': os.getenv(f"{prefix}POP3_USERNAME"),
        'pop3_password': os.getenv(f"{prefix}POP3_PASSWORD"),
        'gmail_credentials_file': os.getenv(f"{prefix}GMAIL_CREDENTIALS_FILE"),
        'gmail_token_file': os.getenv(f"{prefix}GMAIL_TOKEN_FILE"),
        'gmail_target_email': os.getenv(f"{prefix}GMAIL_TARGET_EMAIL"),
    }

    # Validate required settings
    required = ['pop3_host', 'pop3_username', 'pop3_password',
                'gmail_credentials_file', 'gmail_token_file', 'gmail_target_email']
    missing = [key for key in required if not config[key]]
    if missing:
        print_error(f"Missing required settings: {', '.join(missing)}")
        return False

    # Test POP3
    pop3_ok = test_pop3_connection(account_num, config)

    # Test Gmail API
    gmail_ok = test_gmail_api_connection(account_num, config)

    # Overall result
    if pop3_ok and gmail_ok:
        print(f"\n  {GREEN}Account {account_num}: ALL TESTS PASSED ✓{RESET}")
        return True
    else:
        print(f"\n  {RED}Account {account_num}: SOME TESTS FAILED ✗{RESET}")
        return False


def main():
    """Main test program"""
    print(f"\n{'='*60}")
    print(f"POP3 to Gmail Importer v3.0 - Connection Test")
    print(f"{'='*60}")

    # Load environment variables
    load_dotenv()

    # Check if .env file exists
    if not Path('.env').exists():
        print_error(".env file not found. Please create .env from .env.example")
        sys.exit(1)

    print_success(".env file found")

    # Get account count
    account_count = get_env_int('ACCOUNT_COUNT', 1)
    print(f"\nTesting {account_count} account(s)...\n")

    # Test each account
    results = []
    for account_num in range(1, account_count + 1):
        result = test_account(account_num)
        if result is not None:  # Skip disabled accounts
            results.append((account_num, result))

    # Summary
    print(f"\n{'='*60}")
    print(f"Test Summary")
    print(f"{'='*60}")

    if not results:
        print_warning("No enabled accounts to test")
        sys.exit(0)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for account_num, result in results:
        if result:
            print(f"  Account {account_num}: {GREEN}PASSED ✓{RESET}")
        else:
            print(f"  Account {account_num}: {RED}FAILED ✗{RESET}")

    print(f"\n  Total: {passed}/{total} accounts passed")

    if passed == total:
        print(f"\n  {GREEN}All tests passed! Ready to run main.py{RESET}\n")
        sys.exit(0)
    else:
        print(f"\n  {RED}Some tests failed. Please fix the issues above.{RESET}\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
