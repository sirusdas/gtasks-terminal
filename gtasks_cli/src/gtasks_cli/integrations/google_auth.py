"""
Google OAuth2 authentication for Google Tasks CLI.
"""

import os
import pickle
import logging
from typing import Optional
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from gtasks_cli.utils.logger import setup_logger

logger = setup_logger(__name__)

# Google Tasks API scope
SCOPES = ['https://www.googleapis.com/auth/tasks']


class GoogleAuthManager:
    """Manages Google OAuth2 authentication for Google Tasks API."""
    
    def __init__(self, credentials_file: str = None, token_file: str = None, account_name: str = None):
        """
        Initialize the GoogleAuthManager.
        
        Args:
            credentials_file: Path to the client credentials JSON file
            token_file: Path to the token pickle file
            account_name: Name of the account for multi-account support
        """
        self.account_name = account_name
        
        if account_name:
            # For multi-account support, use account-specific paths
            config_dir_env = os.environ.get('GTASKS_CONFIG_DIR')
            if config_dir_env:
                config_dir = config_dir_env
            else:
                config_dir = os.path.join(os.path.expanduser("~"), ".gtasks", account_name)
            
            # Ensure the directory exists
            os.makedirs(config_dir, exist_ok=True)
            
            self.credentials_file = credentials_file or os.path.join(config_dir, "credentials.json")
            self.token_file = token_file or os.path.join(config_dir, "token.pickle")
        else:
            # Default behavior
            self.credentials_file = credentials_file or self._get_default_credentials_file()
            self.token_file = token_file or self._get_default_token_file()
            
        self.credentials = None
        
    def _get_default_credentials_file(self) -> str:
        """Get the default credentials file path."""
        # Check if credentials file is in the config directory
        config_dir_env = os.environ.get('GTASKS_CONFIG_DIR')
        if config_dir_env:
            config_dir = config_dir_env
        else:
            config_dir = os.path.join(os.path.expanduser("~"), ".gtasks")
            
        # Ensure the directory exists
        os.makedirs(config_dir, exist_ok=True)
        credentials_file = os.path.join(config_dir, "credentials.json")
        return credentials_file
    
    def _get_default_token_file(self) -> str:
        """Get the default token file path."""
        config_dir_env = os.environ.get('GTASKS_CONFIG_DIR')
        if config_dir_env:
            config_dir = config_dir_env
        else:
            config_dir = os.path.join(os.path.expanduser("~"), ".gtasks")
            
        # Ensure the directory exists
        os.makedirs(config_dir, exist_ok=True)
        token_file = os.path.join(config_dir, "token.pickle")
        return token_file
    
    def _save_credentials(self):
        """Save credentials to file."""
        try:
            # Ensure the directory exists before saving
            os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
            with open(self.token_file, 'wb') as token:
                pickle.dump(self.credentials, token)
            logger.debug(f"Saved credentials to {self.token_file}")
            logger.info(f"Credentials saved successfully at {self.token_file}")
        except Exception as e:
            logger.error(f"Error saving credentials: {e}")
            raise  # Re-raise the exception for better traceability
    
    def authenticate(self):
        """Authenticate with Google and return credentials."""
        try:
            # The file token.json stores the user's access and refresh tokens.
            if os.path.exists(self.token_file):
                with open(self.token_file, 'rb') as token:
                    self.credentials = pickle.load(token)
            
            # If there are no (valid) credentials available, let the user log in
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    logger.info("Refreshing expired credentials")
                    self.credentials.refresh(Request())
                else:
                    logger.info("Starting new authentication flow")
                    if not os.path.exists(self.credentials_file):
                        logger.error(f"Credentials file not found: {self.credentials_file}")
                        logger.error("Please download the OAuth2 credentials file from the Google Cloud Console")
                        return None
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, SCOPES)
                    self.credentials = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                self._save_credentials()
            
            logger.info("Google authentication successful")
            return self.credentials
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return None
    
    def get_service(self):
        """
        Get the Google Tasks API service object.
        
        Returns:
            googleapiclient.discovery.Resource: The Google Tasks API service
        """
        if not self.credentials:
            if not self.authenticate():
                return None
        
        try:
            service = build('tasks', 'v1', credentials=self.credentials)
            logger.debug("Google Tasks API service created")
            return service
        except Exception as e:
            logger.error(f"Failed to create Google Tasks API service: {e}")
            return None
    
    def clear_credentials(self):
        """Clear stored credentials."""
        if os.path.exists(self.token_file):
            os.remove(self.token_file)
            logger.info("Stored credentials cleared")