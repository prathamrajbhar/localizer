"""
Request Logging Middleware
Comprehensive logging of all HTTP requests and responses
"""
import time
import json
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.server_logger import server_logger
from app.utils.logger import app_logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests and responses
    Tracks request details, response details, and performance metrics
    """
    
    def __init__(self, app, log_request_body: bool = False, log_response_body: bool = False):
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details"""
        start_time = time.time()
        request_id = None
        
        try:
            # Extract request details
            client_ip = self._get_client_ip(request)
            user_agent = request.headers.get("user-agent", "")
            method = request.method
            path = request.url.path
            query_params = str(request.query_params) if request.query_params else ""
            
            # Calculate request size
            request_size = 0
            request_body = None
            
            if self.log_request_body and method in ["POST", "PUT", "PATCH"]:
                try:
                    body = await request.body()
                    request_size = len(body)
                    if body:
                        request_body = body.decode('utf-8')[:1000]  # Limit to 1000 chars
                except Exception as e:
                    app_logger.warning(f"Failed to read request body: {e}")
            
            # Get user ID if available (from headers or auth)
            user_id = request.headers.get("x-user-id") or request.headers.get("user-id")
            
            # Log request start
            request_id = server_logger.log_request(
                method=method,
                path=path,
                client_ip=client_ip,
                user_agent=user_agent,
                request_size=request_size,
                response_size=0,  # Will be updated after response
                status_code=0,    # Will be updated after response
                processing_time=0.0,  # Will be updated after response
                request_id=request_id,
                user_id=user_id,
                query_params=query_params,
                request_body_preview=request_body
            )
            
            # Add request ID to headers for tracking
            request.state.request_id = request_id
            
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Get response details
            response_size = 0
            response_body = None
            
            if self.log_response_body:
                try:
                    # Note: This is a simplified approach. For production,
                    # you might want to use a custom response class
                    response_body = "Response body logging enabled"
                except Exception as e:
                    app_logger.warning(f"Failed to read response body: {e}")
            
            # Log request completion
            server_logger.log_request(
                method=method,
                path=path,
                client_ip=client_ip,
                user_agent=user_agent,
                request_size=request_size,
                response_size=response_size,
                status_code=response.status_code,
                processing_time=processing_time,
                request_id=request_id,
                user_id=user_id,
                query_params=query_params,
                request_body_preview=request_body,
                response_body_preview=response_body,
                completion_status="success"
            )
            
            # Log performance metrics
            server_logger.log_performance_metrics(
                metric_name="request_processing_time",
                value=processing_time,
                unit="seconds",
                context={
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "request_size": request_size,
                    "response_size": response_size
                }
            )
            
            # Add response headers for tracking
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Processing-Time"] = str(processing_time)
            
            return response
            
        except Exception as e:
            # Log error
            processing_time = time.time() - start_time
            
            server_logger.log_request(
                method=method,
                path=path,
                client_ip=client_ip,
                user_agent=user_agent,
                request_size=request_size,
                response_size=0,
                status_code=500,
                processing_time=processing_time,
                request_id=request_id,
                user_id=user_id,
                error=str(e),
                completion_status="error"
            )
            
            # Log error as server activity
            server_logger.log_server_activity(
                activity_type="error",
                description=f"Request processing error: {str(e)}",
                details={
                    "method": method,
                    "path": path,
                    "request_id": request_id,
                    "processing_time": processing_time
                },
                level="ERROR"
            )
            
            raise e
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        if hasattr(request.client, 'host'):
            return request.client.host
        
        return "unknown"
