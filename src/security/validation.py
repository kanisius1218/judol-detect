"""Input validation dan sanitization module."""

import re
import bleach
from typing import Any, Dict, List, Optional
from functools import wraps
from flask import request

from ..exceptions import ValidationError
from ..logging_config import get_logger

logger = get_logger(__name__)


# Allowed HTML tags dan attributes (kosong = strip semua HTML)
ALLOWED_TAGS = []
ALLOWED_ATTRIBUTES = {}


class InputValidator:
    """Validator untuk berbagai jenis input."""
    
    # Regex patterns
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    PHONE_PATTERN = re.compile(r'^\+?[1-9]\d{1,14}$')  # E.164 format
    URL_PATTERN = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    
    @staticmethod
    def validate_text(text: str, 
                     min_length: int = 1, 
                     max_length: int = 10000,
                     field_name: str = "text") -> str:
        """
        Validate text input.
        
        Args:
            text: Text to validate
            min_length: Minimum length
            max_length: Maximum length
            field_name: Field name untuk error message
            
        Returns:
            Validated text
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(text, str):
            raise ValidationError(f"{field_name} must be a string")
        
        text = text.strip()
        
        if len(text) < min_length:
            raise ValidationError(
                f"{field_name} must be at least {min_length} characters"
            )
        
        if len(text) > max_length:
            raise ValidationError(
                f"{field_name} must not exceed {max_length} characters"
            )
        
        return text
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email address."""
        email = email.strip().lower()
        
        if not InputValidator.EMAIL_PATTERN.match(email):
            raise ValidationError("Invalid email address")
        
        return email
    
    @staticmethod
    def validate_phone(phone: str) -> str:
        """Validate phone number."""
        phone = re.sub(r'[\s\-\(\)]', '', phone)
        
        if not InputValidator.PHONE_PATTERN.match(phone):
            raise ValidationError("Invalid phone number")
        
        return phone
    
    @staticmethod
    def validate_url(url: str) -> str:
        """Validate URL."""
        url = url.strip()
        
        if not InputValidator.URL_PATTERN.match(url):
            raise ValidationError("Invalid URL")
        
        return url
    
    @staticmethod
    def validate_integer(value: Any, 
                        min_value: Optional[int] = None,
                        max_value: Optional[int] = None,
                        field_name: str = "value") -> int:
        """Validate integer value."""
        try:
            value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} must be an integer")
        
        if min_value is not None and value < min_value:
            raise ValidationError(
                f"{field_name} must be at least {min_value}"
            )
        
        if max_value is not None and value > max_value:
            raise ValidationError(
                f"{field_name} must not exceed {max_value}"
            )
        
        return value
    
    @staticmethod
    def validate_float(value: Any,
                      min_value: Optional[float] = None,
                      max_value: Optional[float] = None,
                      field_name: str = "value") -> float:
        """Validate float value."""
        try:
            value = float(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} must be a number")
        
        if min_value is not None and value < min_value:
            raise ValidationError(
                f"{field_name} must be at least {min_value}"
            )
        
        if max_value is not None and value > max_value:
            raise ValidationError(
                f"{field_name} must not exceed {max_value}"
            )
        
        return value
    
    @staticmethod
    def validate_list(value: Any,
                     min_items: int = 0,
                     max_items: Optional[int] = None,
                     field_name: str = "list") -> List:
        """Validate list."""
        if not isinstance(value, list):
            raise ValidationError(f"{field_name} must be a list")
        
        if len(value) < min_items:
            raise ValidationError(
                f"{field_name} must contain at least {min_items} items"
            )
        
        if max_items is not None and len(value) > max_items:
            raise ValidationError(
                f"{field_name} must not contain more than {max_items} items"
            )
        
        return value
    
    @staticmethod
    def validate_choice(value: Any,
                       choices: List[Any],
                       field_name: str = "value") -> Any:
        """Validate value is in allowed choices."""
        if value not in choices:
            raise ValidationError(
                f"{field_name} must be one of: {', '.join(map(str, choices))}"
            )
        
        return value


def sanitize_text(text: str, strip_html: bool = True) -> str:
    """
    Sanitize text input untuk prevent XSS.
    
    Args:
        text: Text to sanitize
        strip_html: Whether to strip HTML tags
        
    Returns:
        Sanitized text
    """
    if not isinstance(text, str):
        return ""
    
    # Strip HTML tags if requested
    if strip_html:
        text = bleach.clean(text, tags=ALLOWED_TAGS, 
                          attributes=ALLOWED_ATTRIBUTES, 
                          strip=True)
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Normalize whitespace
    text = ' '.join(text.split())
    
    return text


def validate_input(schema: Dict[str, Any]) -> callable:
    """
    Decorator untuk validate request input berdasarkan schema.
    
    Usage:
        @app.route('/api/predict', methods=['POST'])
        @validate_input({
            'text': {'type': 'text', 'min_length': 1, 'max_length': 5000},
            'threshold': {'type': 'integer', 'min_value': 0, 'max_value': 100, 'optional': True}
        })
        def predict():
            data = request.validated_data
            return {'result': 'ok'}
    
    Args:
        schema: Validation schema dictionary
        
    Returns:
        Decorated function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get request data
            if request.is_json:
                data = request.get_json(silent=True) or {}
            else:
                data = request.form.to_dict()
            
            validated_data = {}
            validator = InputValidator()
            
            # Validate each field
            for field_name, rules in schema.items():
                value = data.get(field_name)
                
                # Check if field is optional
                if value is None:
                    if not rules.get('optional', False):
                        raise ValidationError(f"Field '{field_name}' is required")
                    continue
                
                # Get validation type
                field_type = rules.get('type', 'text')
                
                # Validate based on type
                try:
                    if field_type == 'text':
                        validated_value = validator.validate_text(
                            value,
                            min_length=rules.get('min_length', 1),
                            max_length=rules.get('max_length', 10000),
                            field_name=field_name
                        )
                        # Sanitize if requested
                        if rules.get('sanitize', True):
                            validated_value = sanitize_text(validated_value)
                    
                    elif field_type == 'email':
                        validated_value = validator.validate_email(value)
                    
                    elif field_type == 'phone':
                        validated_value = validator.validate_phone(value)
                    
                    elif field_type == 'url':
                        validated_value = validator.validate_url(value)
                    
                    elif field_type == 'integer':
                        validated_value = validator.validate_integer(
                            value,
                            min_value=rules.get('min_value'),
                            max_value=rules.get('max_value'),
                            field_name=field_name
                        )
                    
                    elif field_type == 'float':
                        validated_value = validator.validate_float(
                            value,
                            min_value=rules.get('min_value'),
                            max_value=rules.get('max_value'),
                            field_name=field_name
                        )
                    
                    elif field_type == 'list':
                        validated_value = validator.validate_list(
                            value,
                            min_items=rules.get('min_items', 0),
                            max_items=rules.get('max_items'),
                            field_name=field_name
                        )
                    
                    elif field_type == 'choice':
                        validated_value = validator.validate_choice(
                            value,
                            choices=rules.get('choices', []),
                            field_name=field_name
                        )
                    
                    else:
                        raise ValidationError(f"Unknown validation type: {field_type}")
                    
                    validated_data[field_name] = validated_value
                
                except ValidationError as e:
                    logger.warning(f"Validation failed for field {field_name}",
                                 extra={'error': str(e), 
                                       'value': str(value)[:100]})
                    raise
            
            # Store validated data in request
            request.validated_data = validated_data
            
            logger.debug("Input validation successful",
                        extra={'fields': list(validated_data.keys())})
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator
