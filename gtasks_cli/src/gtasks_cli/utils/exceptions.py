"""
Custom exceptions for the Google Tasks CLI application.
"""


class GTasksError(Exception):
    """Base exception for all gtasks errors"""
    pass


class AuthenticationError(GTasksError):
    """OAuth or authentication failures"""
    pass


class APIError(GTasksError):
    """Google API errors"""
    def __init__(self, message, status_code=None, response=None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class TaskNotFoundError(GTasksError):
    """Task doesn't exist"""
    pass


class ValidationError(GTasksError):
    """Invalid input data"""
    pass


class SyncError(GTasksError):
    """Synchronization failures"""
    pass


class ConfigError(GTasksError):
    """Configuration issues"""
    pass