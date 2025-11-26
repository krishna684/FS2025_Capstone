"""
Tests for AI service integration
Tests the ai_client module and confidence utilities
"""
import pytest
import os
from unittest.mock import Mock, patch, mock_open
from confidence_utils import classify_confidence, should_request_feedback, get_confidence_message
from ai_client import call_ai_service


class TestConfidenceClassification:
    """Test confidence level classification"""
    
    def test_high_confidence(self):
        """Test high confidence classification (>= 0.85)"""
        assert classify_confidence(0.85) == "High Confidence"
        assert classify_confidence(0.90) == "High Confidence"
        assert classify_confidence(0.99) == "High Confidence"
        assert classify_confidence(1.0) == "High Confidence"
    
    def test_moderate_confidence(self):
        """Test moderate confidence classification (0.70 - 0.84)"""
        assert classify_confidence(0.70) == "Moderate Confidence"
        assert classify_confidence(0.75) == "Moderate Confidence"
        assert classify_confidence(0.84) == "Moderate Confidence"
    
    def test_low_confidence(self):
        """Test low confidence classification (0.50 - 0.69)"""
        assert classify_confidence(0.50) == "Low Confidence"
        assert classify_confidence(0.60) == "Low Confidence"
        assert classify_confidence(0.69) == "Low Confidence"
    
    def test_unable_to_identify(self):
        """Test unable to identify classification (< 0.50)"""
        assert classify_confidence(0.49) == "Unable to identify"
        assert classify_confidence(0.30) == "Unable to identify"
        assert classify_confidence(0.10) == "Unable to identify"
        assert classify_confidence(0.0) == "Unable to identify"
    
    def test_boundary_values(self):
        """Test exact boundary values"""
        assert classify_confidence(0.85) == "High Confidence"
        assert classify_confidence(0.8499) == "Moderate Confidence"
        assert classify_confidence(0.70) == "Moderate Confidence"
        assert classify_confidence(0.6999) == "Low Confidence"
        assert classify_confidence(0.50) == "Low Confidence"
        assert classify_confidence(0.4999) == "Unable to identify"


class TestFeedbackPrompting:
    """Test feedback prompting logic"""
    
    def test_should_request_feedback_below_threshold(self):
        """Test that feedback is requested when confidence < 0.75"""
        assert should_request_feedback(0.74) == True
        assert should_request_feedback(0.70) == True
        assert should_request_feedback(0.50) == True
        assert should_request_feedback(0.30) == True
    
    def test_should_not_request_feedback_above_threshold(self):
        """Test that feedback is not requested when confidence >= 0.75"""
        assert should_request_feedback(0.75) == False
        assert should_request_feedback(0.80) == False
        assert should_request_feedback(0.90) == False
        assert should_request_feedback(1.0) == False
    
    def test_boundary_value(self):
        """Test exact boundary value"""
        assert should_request_feedback(0.75) == False
        assert should_request_feedback(0.7499) == True


class TestConfidenceMessages:
    """Test confidence message generation"""
    
    def test_all_confidence_levels_have_messages(self):
        """Test that all confidence levels have corresponding messages"""
        levels = ["High Confidence", "Moderate Confidence", "Low Confidence", "Unable to identify"]
        for level in levels:
            message = get_confidence_message(level)
            assert message != ""
            assert isinstance(message, str)
    
    def test_unknown_level_returns_empty(self):
        """Test that unknown confidence level returns empty string"""
        assert get_confidence_message("Unknown Level") == ""


class TestAIClientSuccess:
    """Test AI client successful scenarios"""
    
    @patch('ai_client.requests.post')
    @patch('builtins.open', new_callable=mock_open, read_data=b'fake_image_data')
    def test_successful_detection(self, mock_file, mock_post):
        """Test successful pest detection"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'pest_label': 'Japanese Beetle',
            'scientific_name': 'Popillia japonica',
            'confidence': 0.92,
            'alternatives': [
                {'label': 'Aphids', 'confidence': 0.05},
                {'label': 'Spider Mites', 'confidence': 0.03}
            ],
            'processing_time_ms': 1543.2,
            'timing_breakdown': {
                'preprocessing_ms': 87.5,
                'primary_inference_ms': 1455.7,
                'fallback_inference_ms': 0,
                'total_ms': 1543.2
            },
            'fallback_used': False
        }
        mock_post.return_value = mock_response
        
        # Call AI service
        result = call_ai_service('test_image.jpg')
        
        # Verify result
        assert result['success'] == True
        assert result['pest_label'] == 'Japanese Beetle'
        assert result['scientific_name'] == 'Popillia japonica'
        assert result['confidence'] == 0.92
        assert len(result['alternatives']) == 2
        assert result['fallback_used'] == False
    
    @patch('ai_client.requests.post')
    @patch('builtins.open', new_callable=mock_open, read_data=b'fake_image_data')
    def test_detection_with_fallback(self, mock_file, mock_post):
        """Test detection that used fallback model"""
        # Mock response with fallback used
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'pest_label': 'Tomato Leafminer',
            'scientific_name': 'Tuta absoluta',
            'confidence': 0.88,
            'alternatives': [],
            'processing_time_ms': 2543.2,
            'timing_breakdown': {
                'preprocessing_ms': 87.5,
                'primary_inference_ms': 1455.7,
                'fallback_inference_ms': 1000.0,
                'total_ms': 2543.2
            },
            'fallback_used': True
        }
        mock_post.return_value = mock_response
        
        result = call_ai_service('test_image.jpg')
        
        assert result['success'] == True
        assert result['fallback_used'] == True
        assert result['confidence'] == 0.88


class TestAIClientErrors:
    """Test AI client error scenarios"""
    
    @patch('ai_client.requests.post')
    @patch('builtins.open', new_callable=mock_open, read_data=b'fake_image_data')
    def test_timeout_from_service(self, mock_file, mock_post):
        """Test timeout response from AI service (408)"""
        mock_response = Mock()
        mock_response.status_code = 408
        mock_response.json.return_value = {
            'detail': 'Analysis taking longer than expected. Please try again.'
        }
        mock_post.return_value = mock_response
        
        result = call_ai_service('test_image.jpg')
        
        assert result['success'] == False
        assert result['error_type'] == 'timeout'
        assert 'Analysis taking longer than expected' in result['error']
    
    @patch('ai_client.requests.post')
    @patch('builtins.open', new_callable=mock_open, read_data=b'fake_image_data')
    def test_request_timeout(self, mock_file, mock_post):
        """Test request timeout exception"""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout()
        
        result = call_ai_service('test_image.jpg')
        
        assert result['success'] == False
        assert result['error_type'] == 'timeout'
        assert 'Analysis taking longer than expected' in result['error']
    
    @patch('ai_client.requests.post')
    @patch('builtins.open', new_callable=mock_open, read_data=b'fake_image_data')
    def test_connection_error(self, mock_file, mock_post):
        """Test connection error to AI service"""
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError()
        
        result = call_ai_service('test_image.jpg')
        
        assert result['success'] == False
        assert result['error_type'] == 'connection_error'
        assert 'temporarily unavailable' in result['error']
    
    def test_file_not_found(self):
        """Test file not found error"""
        result = call_ai_service('nonexistent_file.jpg')
        
        assert result['success'] == False
        assert result['error_type'] == 'file_not_found'
    
    @patch('ai_client.requests.post')
    @patch('builtins.open', new_callable=mock_open, read_data=b'fake_image_data')
    def test_service_error(self, mock_file, mock_post):
        """Test AI service error response"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = '{"detail": "Internal server error"}'
        mock_response.json.return_value = {'detail': 'Internal server error'}
        mock_post.return_value = mock_response
        
        result = call_ai_service('test_image.jpg')
        
        assert result['success'] == False
        assert result['error_type'] == 'service_error'
        assert result['status_code'] == 500


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
