import inspect
from typing import Optional

class ResumeReviewerException(Exception):
    """
    Base exception for the Resume Reviewer application.
    Automatically captures the module name where it was raised.
    """
    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        # Capture the caller's module name
        try:
            frame = inspect.currentframe().f_back
            self.module_name = frame.f_globals.get('__name__', 'Unknown Module')
        except Exception:
            self.module_name = 'Unknown Module'
            
        self.message = message
        self.original_exception = original_exception
        
        full_message = f"[{self.module_name}] {message}"
        if original_exception:
            full_message += f" | Caused by: {str(original_exception)}"
            
        super().__init__(full_message)

class ParserException(ResumeReviewerException):
    pass

class LLMException(ResumeReviewerException):
    pass

class StorageException(ResumeReviewerException):
    pass

class DataNotFoundException(ResumeReviewerException):
    pass
