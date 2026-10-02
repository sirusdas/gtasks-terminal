import os
import pickle
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from gtasks_cli.utils.logger import setup_logger

logger = setup_logger(__name__)

class GoogleAuthManager:
    """Manages Google Tasks API authentication."""
    
    # If modifying these scopes, delete the file token.pickle.
    SCOPES = ['https://www.googleapis.com/auth/tasks']
    
    def __init__(self, credentials_file: str = None, token_file: str = None, account_name: str = None):
        """
        Initialize the auth manager.
        
        Args:
            credentials_file: Path to the credentials.json file
            token_file: Path to the token.pickle file
        """
        self.account_name = account_name
        self.credentials = None
        
        # Determine config dir for the account
        config_dir_env = os.environ.get('GTASKS_CONFIG_DIR')
        if config_dir_env:
            config_dir = config_dir_env
        else:
            if account_name:
                config_dir = os.path.join(os.path.expanduser("~"), ".gtasks", account_name)
            else:
                config_dir = os.path.join(os.path.expanduser("~"), ".gtasks")
            
        def find_creds(directory):
            c = os.path.join(directory, "credentials.json")
            if os.path.exists(c):
                return c
            for f in os.listdir(directory):
                if f.startswith("client_secret") and f.endswith(".json"):
                    return os.path.join(directory, f)
            return None
            
        found_creds = find_creds(config_dir)
        if not found_creds:
            global_dir = os.path.join(os.path.expanduser("~"), ".gtasks")
            if os.path.exists(global_dir):
                found_creds = find_creds(global_dir)
                
        self.credentials_file = credentials_file or found_creds or os.path.join(config_dir, "credentials.json")
        self.token_file = token_file or os.path.join(config_dir, "token.pickle")
        
        logger.debug(f"Auth manager initialized. Credentials: {self.credentials_file}, Token: {self.token_file}")

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
        
        c = os.path.join(config_dir, "credentials.json")
        if os.path.exists(c):
            return c
            
        for f in os.listdir(config_dir):
            if f.startswith("client_secret") and f.endswith(".json"):
                return os.path.join(config_dir, f)
                
        return c
    
    def _get_default_token_file(self) -> str:
        """Get the default token file path."""
        # Check if token file is in the config directory
        config_dir_env = os.environ.get('GTASKS_CONFIG_DIR')
        if config_dir_env:
            config_dir = config_dir_env
        else:
            config_dir = os.path.join(os.path.expanduser("~"), ".gtasks")
            
        return os.path.join(config_dir, "token.pickle")
        
    def authenticate(self, force_refresh: bool = False) -> Credentials:
        """
        Authenticate with Google Tasks API.
        
        Args:
            force_refresh: If True, force a new authentication flow
            
        Returns:
            Credentials: Authenticated Google credentials
            
        Raises:
            FileNotFoundError: If credentials.json is not found
            Exception: For other authentication errors
        """
        creds = None
        
        # The file token.pickle stores the user's access and refresh tokens
        if os.path.exists(self.token_file) and not force_refresh:
            try:
                with open(self.token_file, 'rb') as token:
                    creds = pickle.load(token)
                logger.debug("Loaded existing credentials from token file")
            except Exception as e:
                logger.warning(f"Failed to load token file: {e}")
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    logger.info("Refreshing expired credentials")
                    creds.refresh(Request())
                except Exception as e:
                    logger.warning(f"Failed to refresh credentials: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(self.credentials_file):
                    error_msg = f"Credentials file not found: {self.credentials_file}\n"
                    error_msg += "Please download your OAuth 2.0 Client ID JSON file from Google Cloud Console "
                    error_msg += "and save it to this location."
                    logger.error(error_msg)
                    raise FileNotFoundError(error_msg)
                
                try:
                    logger.info("Starting new authentication flow")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.SCOPES)
                    
                    # Run local server for the OAuth flow with fallback
                    try:
                        creds = flow.run_local_server(port=0)
                    except Exception as browser_err:
                        if "browser" in str(browser_err).lower():
                            logger.info("Could not launch browser automatically; displaying auth URL instead.")
                            creds = flow.run_local_server(port=0, open_browser=False)
                        else:
                            raise
                except Exception as e:
                    logger.error(f"Authentication flow failed: {e}")
                    raise
            
            # Save the credentials for the next run
            try:
                # Ensure directory exists before saving
                os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
                with open(self.token_file, 'wb') as token:
                    pickle.dump(creds, token)
                logger.debug(f"Saved credentials to {self.token_file}")
            except Exception as e:
                logger.warning(f"Failed to save token file: {e}")
        
        self.credentials = creds
        return creds

    def logout(self) -> bool:
        """
        Remove the stored token to force re-authentication next time.
        
        Returns:
            bool: True if token was removed, False otherwise
        """
        if os.path.exists(self.token_file):
            try:
                os.remove(self.token_file)
                logger.info("Successfully removed stored credentials")
                return True
            except Exception as e:
                logger.error(f"Failed to remove token file: {e}")
                return False
        
        logger.info("No stored credentials found")
        return True

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
