"""
Custom exceptions for BGE Save Editor
"""

class SaveFileError(Exception):
    """Base exception for save file related errors"""
    pass

class CBORParsingError(SaveFileError):
    """Raised when CBOR data cannot be parsed"""
    pass

class FileValidationError(SaveFileError):
    """Raised when save file validation fails"""
    pass

class BackupError(SaveFileError):
    """Raised when backup creation fails"""
    pass

class ValueValidationError(Exception):
    """Raised when a value fails validation"""
    pass