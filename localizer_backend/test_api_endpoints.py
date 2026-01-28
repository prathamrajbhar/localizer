#!/usr/bin/env python3
"""
Comprehensive API Endpoint Testing Script
Indian Language Localizer Backend - Complete Test Suite

This script tests all endpoints documented in API_ENDPOINTS.md
Run with: python test_api_endpoints.py
"""

import requests
import json
import time
import os
from typing import Dict, List, Optional, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class APITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, response: Optional[requests.Response] = None, error: Optional[str] = None):
        """Log test results"""
        result = {
            'test_name': test_name,
            'success': success,
            'timestamp': time.time(),
            'error': error
        }
        
        if response:
            result.update({
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'response_size': len(response.content) if response.content else 0
            })
        
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
        if error:
            logger.error(f"Error: {error}")
    
    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
    
    def create_test_files(self):
        """Set up test files from testing_files directory"""
        self.test_files = {}
        testing_files_dir = os.path.join(os.path.dirname(__file__), 'testing_files')
        
        # Use real test files from testing_files directory
        self.test_files['pdf'] = os.path.join(testing_files_dir, 'demo.pdf')
        self.test_files['mp3'] = os.path.join(testing_files_dir, 'domo.mp3')
        self.test_files['mp4'] = os.path.join(testing_files_dir, 'demo.mp4')
        self.test_files['mp4_alt'] = os.path.join(testing_files_dir, 'demo1.mp4')
        self.test_files['json'] = os.path.join(testing_files_dir, 'sample_quiz.json')
        
        # Verify files exist
        for file_type, file_path in self.test_files.items():
            if not os.path.exists(file_path):
                logger.warning(f"Test file not found: {file_path}")
            else:
                logger.info(f"Using test file: {file_type} -> {file_path}")
    
    def cleanup_test_files(self):
        """Clean up test files (no cleanup needed for real files)"""
        # No cleanup needed since we're using real test files
        pass
    
    # ==================== HEALTH & MONITORING TESTS ====================
    
    def test_health_check(self):
        """Test basic health check endpoint"""
        try:
            response = self.make_request('GET', '/')
            success = response.status_code == 200
            if success:
                data = response.json()
                success = data.get('status') == 'healthy'
            self.log_test("Health Check", success, response)
        except Exception as e:
            self.log_test("Health Check", False, error=str(e))
    
    def test_detailed_health_check(self):
        """Test detailed health check endpoint"""
        try:
            response = self.make_request('GET', '/health/detailed')
            success = response.status_code == 200
            if success:
                data = response.json()
                success = 'system' in data and 'services' in data
            self.log_test("Detailed Health Check", success, response)
        except Exception as e:
            self.log_test("Detailed Health Check", False, error=str(e))
    
    def test_system_info(self):
        """Test system information endpoint"""
        try:
            response = self.make_request('GET', '/system/info')
            success = response.status_code == 200
            if success:
                data = response.json()
                success = 'system' in data and 'environment' in data
            self.log_test("System Info", success, response)
        except Exception as e:
            self.log_test("System Info", False, error=str(e))
    
    def test_performance_metrics(self):
        """Test performance metrics endpoint"""
        try:
            response = self.make_request('GET', '/performance')
            success = response.status_code == 200
            if success:
                data = response.json()
                success = 'metrics' in data
            self.log_test("Performance Metrics", success, response)
        except Exception as e:
            self.log_test("Performance Metrics", False, error=str(e))
    
    # ==================== CONTENT MANAGEMENT TESTS ====================
    
    def test_supported_languages(self):
        """Test supported languages endpoint"""
        try:
            response = self.make_request('GET', '/supported-languages')
            success = response.status_code == 200
            if success:
                data = response.json()
                success = 'supported_languages' in data and 'total_count' in data
            self.log_test("Supported Languages", success, response)
        except Exception as e:
            self.log_test("Supported Languages", False, error=str(e))
    
    def test_file_upload(self):
        """Test file upload with text extraction"""
        try:
            with open(self.test_files['pdf'], 'rb') as f:
                files = {'file': f}
                data = {
                    'domain': 'general',
                    'source_language': 'en'
                }
                response = self.make_request('POST', '/content/upload', files=files, data=data)
            
            success = response.status_code == 200
            if success:
                data = response.json()
                success = 'id' in data and 'extracted_text' in data
                self.uploaded_file_id = data.get('id')
            self.log_test("File Upload with Text Extraction", success, response)
        except Exception as e:
            self.log_test("File Upload with Text Extraction", False, error=str(e))
    
    def test_simple_upload(self):
        """Test simple upload endpoint"""
        try:
            with open(self.test_files['pdf'], 'rb') as f:
                files = {'file': f}
                response = self.make_request('POST', '/upload', files=files)
            
            success = response.status_code == 200
            if success:
                data = response.json()
                success = 'file_id' in data and 'extracted_text' in data
            self.log_test("Simple Upload", success, response)
        except Exception as e:
            self.log_test("Simple Upload", False, error=str(e))
    
    def test_list_files(self):
        """Test list files endpoint"""
        try:
            response = self.make_request('GET', '/content/files?skip=0&limit=10')
            success = response.status_code == 200
            if success:
                data = response.json()
                success = isinstance(data, list)
            self.log_test("List Files", success, response)
        except Exception as e:
            self.log_test("List Files", False, error=str(e))
    
    def test_get_file_details(self):
        """Test get file details endpoint"""
        if hasattr(self, 'uploaded_file_id'):
            try:
                response = self.make_request('GET', f'/content/files/{self.uploaded_file_id}')
                success = response.status_code == 200
                if success:
                    data = response.json()
                    success = 'id' in data and 'filename' in data
                self.log_test("Get File Details", success, response)
            except Exception as e:
                self.log_test("Get File Details", False, error=str(e))
        else:
            self.log_test("Get File Details", False, error="No uploaded file ID available")
    
    # ==================== TRANSLATION SERVICES TESTS ====================
    
    def test_detect_language(self):
        """Test language detection endpoint"""
        try:
            data = {"text": "Hello, how are you?"}
            response = self.make_request('POST', '/detect-language', json=data)
            
            success = response.status_code == 200
            if success:
                data = response.json()
                success = 'detected_language' in data and 'confidence' in data
            self.log_test("Detect Language", success, response)
        except Exception as e:
            self.log_test("Detect Language", False, error=str(e))
    
    def test_translate_text(self):
        """Test text translation endpoint"""
        try:
            data = {
                "text": "Hello, welcome to our vocational training program",
                "source_language": "en",
                "target_languages": ["hi", "bn"],
                "domain": "education",
                "apply_localization": True
            }
            response = self.make_request('POST', '/translate', json=data)
            
            success = response.status_code == 200
            if success:
                data = response.json()
                success = 'results' in data and len(data['results']) > 0
            self.log_test("Translate Text", success, response)
        except Exception as e:
            self.log_test("Translate Text", False, error=str(e))
    
    def test_translate_file(self):
        """Test file translation endpoint"""
        if hasattr(self, 'uploaded_file_id'):
            try:
                data = {
                    "file_id": self.uploaded_file_id,
                    "source_language": "en",
                    "target_languages": ["hi"],
                    "domain": "general",
                    "apply_localization": True
                }
                response = self.make_request('POST', '/translate', json=data)
                
                success = response.status_code == 200
                if success:
                    data = response.json()
                    success = 'results' in data
                self.log_test("Translate File", success, response)
            except Exception as e:
                self.log_test("Translate File", False, error=str(e))
        else:
            self.log_test("Translate File", False, error="No uploaded file ID available")
    
    def test_localize_context(self):
        """Test context localization endpoint"""
        try:
            data = {
                "text": "Safety equipment is mandatory",
                "source_language": "en",
                "target_language": "hi",
                "domain": "construction"
            }
            response = self.make_request('POST', '/localize/context', json=data)
            
            success = response.status_code == 200
            if success:
                data = response.json()
                success = 'localized_text' in data
            self.log_test("Localize Context", success, response)
        except Exception as e:
            self.log_test("Localize Context", False, error=str(e))
    
    def test_translation_stats(self):
        """Test translation statistics endpoint"""
        try:
            response = self.make_request('GET', '/stats')
            success = response.status_code == 200
            if success:
                data = response.json()
                success = 'total_translations' in data
            self.log_test("Translation Stats", success, response)
        except Exception as e:
            self.log_test("Translation Stats", False, error=str(e))
    
    def test_translation_history(self):
        """Test translation history endpoint"""
        if hasattr(self, 'uploaded_file_id'):
            try:
                response = self.make_request('GET', f'/history/{self.uploaded_file_id}')
                success = response.status_code == 200
                if success:
                    data = response.json()
                    success = 'file_id' in data
                self.log_test("Translation History", success, response)
            except Exception as e:
                self.log_test("Translation History", False, error=str(e))
        else:
            self.log_test("Translation History", False, error="No uploaded file ID available")
    
    # ==================== SPEECH PROCESSING TESTS ====================
    
    def test_text_to_speech(self):
        """Test text-to-speech endpoint"""
        try:
            data = {
                "text": "स्वागत है व्यावसायिक प्रशिक्षण में",
                "language": "hi",
                "voice_speed": 1.0,
                "output_format": "mp3"
            }
            response = self.make_request('POST', '/speech/tts', json=data)
            
            success = response.status_code == 200
            if success:
                data = response.json()
                success = 'output_file' in data
            self.log_test("Text-to-Speech", success, response)
        except Exception as e:
            self.log_test("Text-to-Speech", False, error=str(e))
    
    def test_generate_subtitles(self):
        """Test subtitle generation endpoint"""
        try:
            with open(self.test_files['mp3'], 'rb') as f:
                files = {'file': f}
                data = {
                    'language': 'en',
                    'format': 'srt'
                }
                response = self.make_request('POST', '/speech/subtitles', files=files, data=data)
            
            success = response.status_code == 200
            if success:
                data = response.json()
                success = 'output_file' in data
            self.log_test("Generate Subtitles", success, response)
        except Exception as e:
            self.log_test("Generate Subtitles", False, error=str(e))
    
    # ==================== VIDEO LOCALIZATION TESTS ====================
    
    def test_video_localize_fast(self):
        """Test optimized video localization endpoint"""
        try:
            with open(self.test_files['mp4'], 'rb') as f:
                files = {'file': f}
                data = {
                    'target_language': 'hi',
                    'domain': 'general',
                    'include_subtitles': 'true',
                    'quality_preference': 'fast'
                }
                response = self.make_request('POST', '/video/localize-fast', files=files, data=data)
            
            success = response.status_code == 200
            if success:
                data = response.json()
                success = 'outputs' in data
            self.log_test("Video Localize Fast", success, response)
        except Exception as e:
            self.log_test("Video Localize Fast", False, error=str(e))
    
    def test_extract_audio(self):
        """Test audio extraction from video endpoint"""
        try:
            with open(self.test_files['mp4_alt'], 'rb') as f:
                files = {'file': f}
                data = {'output_format': 'wav'}
                response = self.make_request('POST', '/video/extract-audio', files=files, data=data)
            
            success = response.status_code == 200
            if success:
                data = response.json()
                success = 'audio_file' in data
            self.log_test("Extract Audio from Video", success, response)
        except Exception as e:
            self.log_test("Extract Audio from Video", False, error=str(e))
    
    # ==================== ASSESSMENT TRANSLATION TESTS ====================
    
    def test_validate_assessment(self):
        """Test assessment validation endpoint"""
        try:
            with open(self.test_files['json'], 'rb') as f:
                files = {'file': f}
                response = self.make_request('POST', '/assessment/validate', files=files)
            
            success = response.status_code == 200
            if success:
                data = response.json()
                success = 'status' in data
            self.log_test("Validate Assessment", success, response)
        except Exception as e:
            self.log_test("Validate Assessment", False, error=str(e))
    
    def test_translate_assessment(self):
        """Test assessment translation endpoint"""
        try:
            with open(self.test_files['json'], 'rb') as f:
                files = {'file': f}
                data = {
                    'target_language': 'hi',
                    'domain': 'education'
                }
                response = self.make_request('POST', '/assessment/translate', files=files, data=data)
            
            success = response.status_code == 200
            if success:
                data = response.json()
                success = 'output_file' in data
            self.log_test("Translate Assessment", success, response)
        except Exception as e:
            self.log_test("Translate Assessment", False, error=str(e))
    
    def test_sample_assessment_formats(self):
        """Test sample assessment formats endpoint"""
        try:
            response = self.make_request('GET', '/assessment/sample-formats')
            success = response.status_code == 200
            if success:
                data = response.json()
                success = 'json_sample' in data
            self.log_test("Sample Assessment Formats", success, response)
        except Exception as e:
            self.log_test("Sample Assessment Formats", False, error=str(e))
    
    # ==================== JOB MANAGEMENT TESTS ====================
    
    def test_trigger_model_retraining(self):
        """Test model retraining trigger endpoint"""
        try:
            response = self.make_request('POST', '/jobs/retrain?domain=healthcare&model_type=indicTrans2&epochs=1')
            success = response.status_code == 200
            if success:
                data = response.json()
                success = 'job_id' in data
                self.retraining_job_id = data.get('job_id')
            self.log_test("Trigger Model Retraining", success, response)
        except Exception as e:
            self.log_test("Trigger Model Retraining", False, error=str(e))
    
    def test_list_jobs(self):
        """Test list active jobs endpoint"""
        try:
            response = self.make_request('GET', '/jobs')
            success = response.status_code == 200
            if success:
                data = response.json()
                success = 'jobs' in data
            self.log_test("List Jobs", success, response)
        except Exception as e:
            self.log_test("List Jobs", False, error=str(e))
    
    def test_get_job_status(self):
        """Test get job status endpoint"""
        if hasattr(self, 'retraining_job_id'):
            try:
                response = self.make_request('GET', f'/jobs/{self.retraining_job_id}')
                success = response.status_code == 200
                if success:
                    data = response.json()
                    success = 'job_id' in data
                self.log_test("Get Job Status", success, response)
            except Exception as e:
                self.log_test("Get Job Status", False, error=str(e))
        else:
            self.log_test("Get Job Status", False, error="No retraining job ID available")
    
    # ==================== LMS INTEGRATION TESTS ====================
    
    def test_integration_upload(self):
        """Test LMS integration upload endpoint"""
        try:
            with open(self.test_files['pdf'], 'rb') as f:
                files = {'file': f}
                data = {
                    'target_languages': 'hi,bn',
                    'content_type': 'document',
                    'domain': 'general',
                    'partner_id': 'test_partner_123',
                    'priority': 'normal'
                }
                response = self.make_request('POST', '/integration/upload', files=files, data=data)
            
            success = response.status_code == 200
            if success:
                data = response.json()
                success = 'job_id' in data
                self.integration_job_id = data.get('job_id')
            self.log_test("Integration Upload", success, response)
        except Exception as e:
            self.log_test("Integration Upload", False, error=str(e))
    
    def test_integration_status(self):
        """Test integration service status endpoint"""
        try:
            response = self.make_request('GET', '/integration/status')
            success = response.status_code == 200
            if success:
                data = response.json()
                success = 'service_status' in data
            self.log_test("Integration Status", success, response)
        except Exception as e:
            self.log_test("Integration Status", False, error=str(e))
    
    # ==================== FEEDBACK SYSTEM TESTS ====================
    
    def test_submit_feedback(self):
        """Test submit feedback endpoint"""
        try:
            data = {
                "rating": 4,
                "comments": "Translation quality is very good for technical content"
            }
            response = self.make_request('POST', '/feedback', json=data)
            
            success = response.status_code == 200
            if success:
                data = response.json()
                success = 'feedback_id' in data
            self.log_test("Submit Feedback", success, response)
        except Exception as e:
            self.log_test("Submit Feedback", False, error=str(e))
    
    def test_list_feedback(self):
        """Test list feedback endpoint"""
        try:
            response = self.make_request('GET', '/feedback?skip=0&limit=10')
            success = response.status_code == 200
            if success:
                data = response.json()
                success = isinstance(data, list)
            self.log_test("List Feedback", success, response)
        except Exception as e:
            self.log_test("List Feedback", False, error=str(e))
    
    # ==================== LOG MANAGEMENT TESTS ====================
    
    def test_server_stats(self):
        """Test server statistics endpoint"""
        try:
            response = self.make_request('GET', '/logs/server-stats')
            success = response.status_code == 200
            if success:
                data = response.json()
                success = 'server_stats' in data
            self.log_test("Server Stats", success, response)
        except Exception as e:
            self.log_test("Server Stats", False, error=str(e))
    
    def test_recent_requests(self):
        """Test recent requests endpoint"""
        try:
            response = self.make_request('GET', '/logs/requests?limit=10&hours=24')
            success = response.status_code == 200
            if success:
                data = response.json()
                success = 'requests' in data
            self.log_test("Recent Requests", success, response)
        except Exception as e:
            self.log_test("Recent Requests", False, error=str(e))
    
    def test_recent_transfers(self):
        """Test recent data transfers endpoint"""
        try:
            response = self.make_request('GET', '/logs/transfers?limit=10&hours=12')
            success = response.status_code == 200
            if success:
                data = response.json()
                success = 'transfers' in data
            self.log_test("Recent Transfers", success, response)
        except Exception as e:
            self.log_test("Recent Transfers", False, error=str(e))
    
    def test_recent_activities(self):
        """Test recent server activities endpoint"""
        try:
            response = self.make_request('GET', '/logs/activities?limit=10&hours=6')
            success = response.status_code == 200
            if success:
                data = response.json()
                success = 'activities' in data
            self.log_test("Recent Activities", success, response)
        except Exception as e:
            self.log_test("Recent Activities", False, error=str(e))
    
    def test_active_transfers(self):
        """Test active transfers endpoint"""
        try:
            response = self.make_request('GET', '/logs/active-transfers')
            success = response.status_code == 200
            if success:
                data = response.json()
                success = 'active_transfers' in data
            self.log_test("Active Transfers", success, response)
        except Exception as e:
            self.log_test("Active Transfers", False, error=str(e))
    
    def test_performance_metrics_logs(self):
        """Test performance metrics from logs endpoint"""
        try:
            response = self.make_request('GET', '/logs/performance?hours=24')
            success = response.status_code == 200
            if success:
                data = response.json()
                success = 'performance_metrics' in data
            self.log_test("Performance Metrics Logs", success, response)
        except Exception as e:
            self.log_test("Performance Metrics Logs", False, error=str(e))
    
    def test_logs_summary(self):
        """Test comprehensive logs summary endpoint"""
        try:
            response = self.make_request('GET', '/logs/summary?hours=24')
            success = response.status_code == 200
            if success:
                data = response.json()
                success = 'summary' in data
            self.log_test("Logs Summary", success, response)
        except Exception as e:
            self.log_test("Logs Summary", False, error=str(e))
    
    # ==================== CLEANUP TESTS ====================
    
    def test_delete_file(self):
        """Test delete file endpoint"""
        if hasattr(self, 'uploaded_file_id'):
            try:
                response = self.make_request('DELETE', f'/content/files/{self.uploaded_file_id}')
                success = response.status_code == 204
                self.log_test("Delete File", success, response)
            except Exception as e:
                self.log_test("Delete File", False, error=str(e))
        else:
            self.log_test("Delete File", False, error="No uploaded file ID available")
    
    def test_cancel_job(self):
        """Test cancel job endpoint"""
        if hasattr(self, 'retraining_job_id'):
            try:
                response = self.make_request('DELETE', f'/jobs/{self.retraining_job_id}')
                success = response.status_code == 200
                self.log_test("Cancel Job", success, response)
            except Exception as e:
                self.log_test("Cancel Job", False, error=str(e))
        else:
            self.log_test("Cancel Job", False, error="No retraining job ID available")
    
    # ==================== MAIN TEST RUNNER ====================
    
    def run_all_tests(self):
        """Run all API endpoint tests"""
        logger.info("🚀 Starting Comprehensive API Endpoint Testing")
        logger.info(f"Testing against: {self.base_url}")
        logger.info("=" * 60)
        
        # Create test files
        self.create_test_files()
        
        try:
            # Health & Monitoring Tests
            logger.info("📊 Testing Health & Monitoring Endpoints...")
            self.test_health_check()
            self.test_detailed_health_check()
            self.test_system_info()
            self.test_performance_metrics()
            
            # Content Management Tests
            logger.info("📁 Testing Content Management Endpoints...")
            self.test_supported_languages()
            self.test_file_upload()
            self.test_simple_upload()
            self.test_list_files()
            self.test_get_file_details()
            
            # Translation Services Tests
            logger.info("🌐 Testing Translation Services Endpoints...")
            self.test_detect_language()
            self.test_translate_text()
            self.test_translate_file()
            self.test_localize_context()
            self.test_translation_stats()
            self.test_translation_history()
            
            # Speech Processing Tests
            logger.info("🗣️ Testing Speech Processing Endpoints...")
            self.test_text_to_speech()
            self.test_generate_subtitles()
            
            # Video Localization Tests
            logger.info("🎥 Testing Video Localization Endpoints...")
            self.test_video_localize_fast()
            self.test_extract_audio()
            
            # Assessment Translation Tests
            logger.info("📚 Testing Assessment Translation Endpoints...")
            self.test_validate_assessment()
            self.test_translate_assessment()
            self.test_sample_assessment_formats()
            
            # Job Management Tests
            logger.info("⚙️ Testing Job Management Endpoints...")
            self.test_trigger_model_retraining()
            self.test_list_jobs()
            self.test_get_job_status()
            
            # LMS Integration Tests
            logger.info("🏢 Testing LMS Integration Endpoints...")
            self.test_integration_upload()
            self.test_integration_status()
            
            # Feedback System Tests
            logger.info("💬 Testing Feedback System Endpoints...")
            self.test_submit_feedback()
            self.test_list_feedback()
            
            # Log Management Tests
            logger.info("📊 Testing Log Management Endpoints...")
            self.test_server_stats()
            self.test_recent_requests()
            self.test_recent_transfers()
            self.test_recent_activities()
            self.test_active_transfers()
            self.test_performance_metrics_logs()
            self.test_logs_summary()
            
            # Cleanup Tests
            logger.info("🧹 Testing Cleanup Endpoints...")
            self.test_delete_file()
            self.test_cancel_job()
            
        finally:
            # Clean up test files
            self.cleanup_test_files()
        
        # Generate test report
        self.generate_test_report()
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("=" * 60)
        logger.info("📋 TEST REPORT SUMMARY")
        logger.info("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"✅ Passed: {passed_tests}")
        logger.info(f"❌ Failed: {failed_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            logger.info("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    logger.info(f"  - {result['test_name']}: {result.get('error', 'Unknown error')}")
        
        # Calculate average response time
        response_times = [r.get('response_time', 0) for r in self.test_results if r.get('response_time')]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            logger.info(f"\n⏱️ Average Response Time: {avg_response_time:.3f}s")
        
        # Save detailed report to file
        report_file = f"api_test_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'summary': {
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': failed_tests,
                    'success_rate': (passed_tests/total_tests)*100,
                    'average_response_time': avg_response_time if response_times else 0
                },
                'test_results': self.test_results
            }, f, indent=2)
        
        logger.info(f"\n📄 Detailed report saved to: {report_file}")
        logger.info("🎉 API Testing Complete!")


def main():
    """Main function to run the API tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Indian Language Localizer API Endpoints')
    parser.add_argument('--base-url', default='http://localhost:8000', 
                       help='Base URL of the API server (default: http://localhost:8000)')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and run API tester
    tester = APITester(args.base_url)
    tester.run_all_tests()


if __name__ == "__main__":
    main()
