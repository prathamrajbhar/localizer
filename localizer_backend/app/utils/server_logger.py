"""
Comprehensive Server Logging System
Tracks all requests, data transfers, and server activities
"""
import json
import time
import uuid
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path
from loguru import logger
from app.core.config import get_settings

settings = get_settings()

class ServerLogger:
    """
    Comprehensive server logging system for tracking:
    - All HTTP requests and responses
    - Data transfers (file uploads, downloads, processing)
    - Server activities and performance metrics
    - Error tracking and debugging
    """
    
    def __init__(self):
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # Create specific log directories
        (self.log_dir / "requests").mkdir(exist_ok=True)
        (self.log_dir / "data_transfers").mkdir(exist_ok=True)
        (self.log_dir / "server_activities").mkdir(exist_ok=True)
        (self.log_dir / "performance").mkdir(exist_ok=True)
        
        # Initialize log files
        self._setup_log_files()
        
        # Performance tracking
        self.request_count = 0
        self.total_data_transferred = 0
        self.start_time = time.time()
        
    def _setup_log_files(self):
        """Setup log files with rotation"""
        # Request logs
        logger.add(
            self.log_dir / "requests" / "requests.log",
            rotation="100 MB",
            retention="30 days",
            compression="zip",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {message}",
            level="INFO",
            filter=lambda record: record["extra"].get("log_type") == "request"
        )
        
        # Data transfer logs
        logger.add(
            self.log_dir / "data_transfers" / "transfers.log",
            rotation="100 MB",
            retention="30 days",
            compression="zip",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {message}",
            level="INFO",
            filter=lambda record: record["extra"].get("log_type") == "data_transfer"
        )
        
        # Server activity logs
        logger.add(
            self.log_dir / "server_activities" / "activities.log",
            rotation="100 MB",
            retention="30 days",
            compression="zip",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {message}",
            level="INFO",
            filter=lambda record: record["extra"].get("log_type") == "server_activity"
        )
        
        # Performance logs
        logger.add(
            self.log_dir / "performance" / "performance.log",
            rotation="100 MB",
            retention="30 days",
            compression="zip",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {message}",
            level="INFO",
            filter=lambda record: record["extra"].get("log_type") == "performance"
        )
    
    def log_request(self, 
                   method: str, 
                   path: str, 
                   client_ip: str,
                   user_agent: str = None,
                   request_size: int = 0,
                   response_size: int = 0,
                   status_code: int = 200,
                   processing_time: float = 0.0,
                   request_id: str = None,
                   user_id: str = None,
                   **kwargs) -> str:
        """
        Log HTTP request details
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path
            client_ip: Client IP address
            user_agent: User agent string
            request_size: Request body size in bytes
            response_size: Response body size in bytes
            status_code: HTTP status code
            processing_time: Request processing time in seconds
            request_id: Unique request ID
            user_id: User ID if authenticated
            **kwargs: Additional request data
        
        Returns:
            str: Request ID for tracking
        """
        if not request_id:
            request_id = str(uuid.uuid4())
        
        self.request_count += 1
        
        request_data = {
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "method": method,
            "path": path,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "request_size_bytes": request_size,
            "response_size_bytes": response_size,
            "status_code": status_code,
            "processing_time_seconds": processing_time,
            "user_id": user_id,
            "total_requests": self.request_count,
            **kwargs
        }
        
        # Log to file
        logger.bind(log_type="request").info(
            f"REQUEST | {method} {path} | "
            f"IP: {client_ip} | "
            f"Status: {status_code} | "
            f"Time: {processing_time:.3f}s | "
            f"Size: {request_size}/{response_size} bytes | "
            f"ID: {request_id}"
        )
        
        # Log detailed data to JSON file for analysis
        self._log_to_json("requests", request_data)
        
        return request_id
    
    def log_data_transfer(self,
                         transfer_type: str,
                         file_name: str,
                         file_size: int,
                         source: str,
                         destination: str,
                         transfer_time: float,
                         status: str = "success",
                         user_id: str = None,
                         request_id: str = None,
                         **kwargs) -> str:
        """
        Log data transfer activities
        
        Args:
            transfer_type: Type of transfer (upload, download, processing)
            file_name: Name of the file
            file_size: File size in bytes
            source: Source location/path
            destination: Destination location/path
            transfer_time: Transfer time in seconds
            status: Transfer status (success, failed, partial)
            user_id: User ID if authenticated
            request_id: Associated request ID
            **kwargs: Additional transfer data
        
        Returns:
            str: Transfer ID for tracking
        """
        transfer_id = str(uuid.uuid4())
        
        self.total_data_transferred += file_size
        
        transfer_data = {
            "transfer_id": transfer_id,
            "timestamp": datetime.utcnow().isoformat(),
            "transfer_type": transfer_type,
            "file_name": file_name,
            "file_size_bytes": file_size,
            "source": source,
            "destination": destination,
            "transfer_time_seconds": transfer_time,
            "status": status,
            "user_id": user_id,
            "request_id": request_id,
            "total_data_transferred": self.total_data_transferred,
            **kwargs
        }
        
        # Log to file
        logger.bind(log_type="data_transfer").info(
            f"TRANSFER | {transfer_type.upper()} | "
            f"File: {file_name} | "
            f"Size: {file_size} bytes | "
            f"Time: {transfer_time:.3f}s | "
            f"Status: {status} | "
            f"ID: {transfer_id}"
        )
        
        # Log detailed data to JSON file
        self._log_to_json("data_transfers", transfer_data)
        
        return transfer_id
    
    def log_server_activity(self,
                           activity_type: str,
                           description: str,
                           details: Dict[str, Any] = None,
                           level: str = "INFO",
                           **kwargs):
        """
        Log server activities and events
        
        Args:
            activity_type: Type of activity (startup, shutdown, maintenance, etc.)
            description: Human-readable description
            details: Additional details dictionary
            level: Log level (INFO, WARNING, ERROR)
            **kwargs: Additional activity data
        """
        activity_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "activity_type": activity_type,
            "description": description,
            "details": details or {},
            "level": level,
            **kwargs
        }
        
        # Log to file
        logger.bind(log_type="server_activity").log(
            level,
            f"ACTIVITY | {activity_type.upper()} | {description}"
        )
        
        # Log detailed data to JSON file
        self._log_to_json("server_activities", activity_data)
    
    def log_performance_metrics(self,
                               metric_name: str,
                               value: float,
                               unit: str = "seconds",
                               context: Dict[str, Any] = None,
                               **kwargs):
        """
        Log performance metrics
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Unit of measurement
            context: Additional context
            **kwargs: Additional metric data
        """
        metric_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "metric_name": metric_name,
            "value": value,
            "unit": unit,
            "context": context or {},
            **kwargs
        }
        
        # Log to file
        logger.bind(log_type="performance").info(
            f"PERFORMANCE | {metric_name} | {value} {unit}"
        )
        
        # Log detailed data to JSON file
        self._log_to_json("performance", metric_data)
    
    def _log_to_json(self, log_type: str, data: Dict[str, Any]):
        """Log data to JSON file for structured analysis"""
        json_file = self.log_dir / log_type / f"{log_type}_{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        
        try:
            with open(json_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"Failed to write to JSON log file: {e}")
    
    def get_server_stats(self) -> Dict[str, Any]:
        """Get comprehensive server statistics"""
        uptime = time.time() - self.start_time
        
        return {
            "uptime_seconds": uptime,
            "uptime_human": str(timedelta(seconds=int(uptime))),
            "total_requests": self.request_count,
            "total_data_transferred_bytes": self.total_data_transferred,
            "total_data_transferred_mb": round(self.total_data_transferred / (1024 * 1024), 2),
            "requests_per_second": round(self.request_count / uptime, 2) if uptime > 0 else 0,
            "data_transfer_rate_mbps": round((self.total_data_transferred / (1024 * 1024)) / uptime, 2) if uptime > 0 else 0,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "current_time": datetime.utcnow().isoformat()
        }
    
    def get_recent_requests(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent requests from JSON logs"""
        return self._get_recent_logs("requests", limit)
    
    def get_recent_transfers(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent data transfers from JSON logs"""
        return self._get_recent_logs("data_transfers", limit)
    
    def get_recent_activities(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent server activities from JSON logs"""
        return self._get_recent_logs("server_activities", limit)
    
    def _get_recent_logs(self, log_type: str, limit: int) -> List[Dict[str, Any]]:
        """Get recent logs from JSON files"""
        json_file = self.log_dir / log_type / f"{log_type}_{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        
        if not json_file.exists():
            return []
        
        try:
            logs = []
            with open(json_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        logs.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue
            
            # Return most recent logs
            return logs[-limit:] if len(logs) > limit else logs
            
        except Exception as e:
            logger.error(f"Failed to read logs from {json_file}: {e}")
            return []
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up old log files"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        for log_type in ["requests", "data_transfers", "server_activities", "performance"]:
            log_dir = self.log_dir / log_type
            
            if not log_dir.exists():
                continue
            
            for file_path in log_dir.iterdir():
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_date.timestamp():
                    try:
                        file_path.unlink()
                        logger.info(f"Deleted old log file: {file_path}")
                    except Exception as e:
                        logger.error(f"Failed to delete log file {file_path}: {e}")


# Global server logger instance
server_logger = ServerLogger()
