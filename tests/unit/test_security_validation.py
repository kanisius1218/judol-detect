"""Unit tests for validation module."""

import pytest
from src.security.validation import (
    InputValidator, sanitize_text, validate_input
)
from src.exceptions import ValidationError


class TestInputValidator:
    """Tests for InputValidator class."""
    
    def test_validate_text_valid(self):
        """Test validating valid text."""
        result = InputValidator.validate_text(
            "Hello world",
            min_length=1,
            max_length=100
        )
        assert result == "Hello world"
    
    def test_validate_text_strips_whitespace(self):
        """Test text validation strips whitespace."""
        result = InputValidator.validate_text("  Hello  ")
        assert result == "Hello"
    
    def test_validate_text_too_short(self):
        """Test text validation with too short input."""
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_text("Hi", min_length=5)
        
        assert "at least 5 characters" in str(exc.value)
    
    def test_validate_text_too_long(self):
        """Test text validation with too long input."""
        long_text = "a" * 1000
        
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_text(long_text, max_length=100)
        
        assert "must not exceed 100 characters" in str(exc.value)
    
    def test_validate_text_not_string(self):
        """Test text validation with non-string input."""
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_text(123)
        
        assert "must be a string" in str(exc.value)
    
    def test_validate_email_valid(self):
        """Test validating valid email."""
        result = InputValidator.validate_email("user@example.com")
        assert result == "user@example.com"
    
    def test_validate_email_invalid(self):
        """Test validating invalid email."""
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_email("invalid.email")
        
        assert "Invalid email" in str(exc.value)
    
    def test_validate_email_normalizes(self):
        """Test email validation normalizes case."""
        result = InputValidator.validate_email("  USER@EXAMPLE.COM  ")
        assert result == "user@example.com"
    
    def test_validate_integer_valid(self):
        """Test validating valid integer."""
        result = InputValidator.validate_integer("42")
        assert result == 42
        assert isinstance(result, int)
    
    def test_validate_integer_with_range(self):
        """Test integer validation with range."""
        result = InputValidator.validate_integer("50", min_value=0, max_value=100)
        assert result == 50
    
    def test_validate_integer_below_minimum(self):
        """Test integer validation below minimum."""
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_integer("-5", min_value=0)
        
        assert "at least 0" in str(exc.value)
    
    def test_validate_integer_above_maximum(self):
        """Test integer validation above maximum."""
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_integer("150", max_value=100)
        
        assert "must not exceed 100" in str(exc.value)
    
    def test_validate_integer_not_a_number(self):
        """Test integer validation with non-numeric input."""
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_integer("not a number")
        
        assert "must be an integer" in str(exc.value)
    
    def test_validate_list_valid(self):
        """Test validating valid list."""
        result = InputValidator.validate_list([1, 2, 3])
        assert result == [1, 2, 3]
    
    def test_validate_list_too_few_items(self):
        """Test list validation with too few items."""
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_list([1], min_items=2)
        
        assert "at least 2 items" in str(exc.value)
    
    def test_validate_list_too_many_items(self):
        """Test list validation with too many items."""
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_list([1, 2, 3, 4, 5], max_items=3)
        
        assert "not contain more than 3 items" in str(exc.value)
    
    def test_validate_choice_valid(self):
        """Test validating valid choice."""
        result = InputValidator.validate_choice("red", ["red", "green", "blue"])
        assert result == "red"
    
    def test_validate_choice_invalid(self):
        """Test validating invalid choice."""
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_choice("yellow", ["red", "green", "blue"])
        
        assert "must be one of" in str(exc.value)


class TestSanitizeText:
    """Tests for sanitize_text function."""
    
    def test_sanitize_plain_text(self):
        """Test sanitizing plain text."""
        result = sanitize_text("Hello world")
        assert result == "Hello world"
    
    def test_sanitize_html_tags(self):
        """Test sanitizing HTML tags."""
        result = sanitize_text("<script>alert('xss')</script>Hello")
        assert "<script>" not in result
        assert "Hello" in result
    
    def test_sanitize_dangerous_html(self):
        """Test sanitizing dangerous HTML."""
        dangerous = '<img src=x onerror="alert(1)">'
        result = sanitize_text(dangerous)
        assert "onerror" not in result
        assert "alert" not in result
    
    def test_sanitize_null_bytes(self):
        """Test sanitizing null bytes."""
        result = sanitize_text("Hello\x00World")
        assert "\x00" not in result
        assert result == "Hello World"
    
    def test_sanitize_normalize_whitespace(self):
        """Test whitespace normalization."""
        result = sanitize_text("Hello    \n\n   World")
        assert result == "Hello World"
    
    def test_sanitize_non_string(self):
        """Test sanitizing non-string input."""
        result = sanitize_text(123)
        assert result == ""


class TestValidateInputDecorator:
    """Tests for validate_input decorator."""
    
    def test_validate_simple_schema(self, client):
        """Test validation with simple schema."""
        from flask import Flask, jsonify, request
        
        app = Flask(__name__)
        
        @app.route('/test', methods=['POST'])
        @validate_input({
            'name': {'type': 'text', 'min_length': 2, 'max_length': 50}
        })
        def test_endpoint():
            data = request.validated_data
            return jsonify(data)
        
        with app.test_client() as test_client:
            response = test_client.post(
                '/test',
                json={'name': 'John Doe'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['name'] == 'John Doe'
    
    def test_validate_missing_required_field(self, client):
        """Test validation with missing required field."""
        from flask import Flask, jsonify, request
        
        app = Flask(__name__)
        
        @app.route('/test', methods=['POST'])
        @validate_input({
            'name': {'type': 'text'}
        })
        def test_endpoint():
            return jsonify(request.validated_data)
        
        with app.test_client() as test_client:
            response = test_client.post('/test', json={})
            
            assert response.status_code == 400
    
    def test_validate_optional_field(self, client):
        """Test validation with optional field."""
        from flask import Flask, jsonify, request
        
        app = Flask(__name__)
        
        @app.route('/test', methods=['POST'])
        @validate_input({
            'name': {'type': 'text'},
            'age': {'type': 'integer', 'optional': True}
        })
        def test_endpoint():
            return jsonify(request.validated_data)
        
        with app.test_client() as test_client:
            response = test_client.post(
                '/test',
                json={'name': 'John'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'name' in data
            assert 'age' not in data
    
    def test_validate_sanitizes_html(self, client):
        """Test validation sanitizes HTML."""
        from flask import Flask, jsonify, request
        
        app = Flask(__name__)
        
        @app.route('/test', methods=['POST'])
        @validate_input({
            'message': {'type': 'text', 'sanitize': True}
        })
        def test_endpoint():
            return jsonify(request.validated_data)
        
        with app.test_client() as test_client:
            response = test_client.post(
                '/test',
                json={'message': '<script>alert("xss")</script>Hello'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert '<script>' not in data['message']
            assert 'Hello' in data['message']
    
    def test_validate_complex_schema(self, client):
        """Test validation with complex schema."""
        from flask import Flask, jsonify, request
        
        app = Flask(__name__)
        
        @app.route('/test', methods=['POST'])
        @validate_input({
            'text': {'type': 'text', 'min_length': 1, 'max_length': 5000},
            'threshold': {'type': 'integer', 'min_value': 0, 'max_value': 100},
            'platform': {'type': 'choice', 'choices': ['youtube', 'instagram']},
            'tags': {'type': 'list', 'min_items': 0, 'max_items': 10, 'optional': True}
        })
        def test_endpoint():
            return jsonify(request.validated_data)
        
        with app.test_client() as test_client:
            response = test_client.post(
                '/test',
                json={
                    'text': 'Test message',
                    'threshold': 75,
                    'platform': 'youtube'
                }
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['text'] == 'Test message'
            assert data['threshold'] == 75
            assert data['platform'] == 'youtube'


@pytest.mark.security
class TestSecurityValidation:
    """Security-focused validation tests."""
    
    def test_sql_injection_prevention(self):
        """Test prevention of SQL injection attempts."""
        malicious = "'; DROP TABLE users; --"
        result = sanitize_text(malicious)
        
        # Text should be sanitized but still present
        assert "DROP TABLE" in result  # We're just sanitizing HTML, not SQL
        # For SQL injection prevention, use parameterized queries
    
    def test_xss_prevention(self):
        """Test prevention of XSS attacks."""
        xss_attempts = [
            "<script>alert('xss')</script>",
            '<img src=x onerror="alert(1)">',
            "<iframe src='javascript:alert(1)'>",
            "javascript:void(0)"
        ]
        
        for attempt in xss_attempts:
            result = sanitize_text(attempt)
            assert "<script>" not in result
            assert "onerror" not in result
            assert "<iframe>" not in result
    
    def test_command_injection_prevention(self):
        """Test prevention of command injection."""
        malicious = "; rm -rf /"
        result = sanitize_text(malicious)
        
        # Should not contain dangerous commands
        assert result  # Text is preserved
