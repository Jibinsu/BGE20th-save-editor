"""
Value validation for save file editing
"""
from typing import Any, Dict, Callable
import logging

from config import Config
from exceptions import ValueValidationError

logger = logging.getLogger(__name__)

class ValueValidator:
    """Validates values before they are saved to the file"""
    
    def __init__(self):
        self.validators: Dict[str, Callable] = {
            'credits': self._validate_credits,
            'pearls': self._validate_pearls,
            'health': self._validate_health,
            'f_sally_fric': self._validate_credits,  # Credits field
        }
    
    def validate(self, key_path: list, value: Any, value_type: str) -> Any:
        """
        Validate a value before saving
        
        Args:
            key_path: List of keys leading to this value
            value: The value to validate
            value_type: The expected type of the value
            
        Returns:
            The validated (and possibly converted) value
            
        Raises:
            ValueValidationError: If validation fails
        """
        try:
            # Convert to correct type first
            converted_value = self._cast_to_type(value, value_type)
            
            # Check if we have a specific validator for this field
            field_name = key_path[-1] if key_path else ""
            
            if field_name in self.validators:
                return self.validators[field_name](converted_value)
            
            # Generic validation based on type
            return self._validate_generic(converted_value, value_type)
            
        except Exception as e:
            raise ValueValidationError(f"Validation failed for {'.'.join(key_path)}: {e}")
    
    def _cast_to_type(self, value: Any, value_type: str) -> Any:
        """Cast value to the correct type"""
        try:
            if value_type == 'int':
                return int(value)
            elif value_type == 'float':
                return float(value)
            elif value_type == 'bool':
                if isinstance(value, str):
                    return value.lower() in ['true', '1', 'yes']
                return bool(value)
            else:
                return str(value)
        except ValueError as e:
            raise ValueValidationError(f"Cannot convert '{value}' to {value_type}: {e}")
    
    def _validate_credits(self, value: int) -> int:
        """Validate credits value"""
        limits = Config.VALIDATION_LIMITS['credits']
        if not (limits['min'] <= value <= limits['max']):
            raise ValueValidationError(
                f"Credits must be between {limits['min']} and {limits['max']}"
            )
        return value
    
    def _validate_pearls(self, value: int) -> int:
        """Validate pearls value"""
        limits = Config.VALIDATION_LIMITS['pearls']
        if not (limits['min'] <= value <= limits['max']):
            raise ValueValidationError(
                f"Pearls must be between {limits['min']} and {limits['max']}"
            )
        return value
    
    def _validate_health(self, value: float) -> float:
        """Validate health value"""
        limits = Config.VALIDATION_LIMITS['health']
        if not (limits['min'] <= value <= limits['max']):
            raise ValueValidationError(
                f"Health must be between {limits['min']} and {limits['max']}"
            )
        return value
    
    def _validate_generic(self, value: Any, value_type: str) -> Any:
        """Generic validation for common types"""
        if value_type == 'int' and isinstance(value, int):
            # Check for reasonable integer bounds
            if not (-2147483648 <= value <= 2147483647):
                raise ValueValidationError("Integer value out of reasonable range")
        
        elif value_type == 'float' and isinstance(value, float):
            # Check for reasonable float bounds
            if not (-1e10 <= value <= 1e10):
                raise ValueValidationError("Float value out of reasonable range")
        
        return value