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
    
    def __init__(self, credentials_file: str = None, token_file: str = None):
        """
        Initialize the GoogleAuthManager.
        
        Args:
            credentials_file: Path to the client credentials JSON file
            token_file: Path to the token pickle file
        """
        self.credentials_file = credentials_file or self._get_default_credentials_file()
        self.token_file = token_file or self._get_default_token_file()
        self.credentials = None
        
    def _get_default_credentials_file(self) -> str:
        """Get the default credentials file path."""
        # Check if credentials file is in the config directory
        config_dir = os.path.join(os.path.expanduser("~"), ".gtasks")
        credentials_file = os.path.join(config_dir, "credentials.json")
        return credentials_file
    
    def _get_default_token_file(self) -> str:
        """Get the default token file path."""
        config_dir = os.path.join(os.path.expanduser("~"), ".gtasks")
        token_file = os.path.join(config_dir, "token.pickle")
        return token_file
    
    def authenticate(self) -> bool:
        """
        Authenticate with Google OAuth2.
        
        Returns:
            bool: True if authentication was successful, False otherwise
        """
        try:
            # Load existing credentials from file
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
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, SCOPES)
                    self.credentials = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                self._save_credentials()
            
            logger.info("Google authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def _save_credentials(self):
        """Save credentials to file."""
        try:
            with open(self.token_file, 'wb') as token:
                pickle.dump(self.credentials, token)
            logger.debug("Credentials saved successfully")
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
    
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