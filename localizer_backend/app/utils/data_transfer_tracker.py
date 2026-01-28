"""
Data Transfer Tracking System
Tracks all file uploads, downloads, and processing activities
"""
import os
import time
from typing import Dict, Any, Optional
from pathlib import Path
from app.utils.server_logger import server_logger
from app.utils.logger import app_logger


class DataTransferTracker:
    """
    Tracks all data transfer activities including:
    - File uploads
    - File downloads
    - File processing
    - Translation operations
    - Audio/video processing
    """
    
    def __init__(self):
        self.active_transfers = {}
    
    def start_upload_tracking(self, 
                            file_name: str, 
                            file_size: int, 
                            user_id: str = None,
                            request_id: str = None) -> str:
        """Start tracking a file upload"""
        transfer_id = server_logger.log_data_transfer(
            transfer_type="upload_start",
            file_name=file_name,
            file_size=file_size,
            source="client",
            destination="server",
            transfer_time=0.0,
            status="started",
            user_id=user_id,
            request_id=request_id
        )
        
        self.active_transfers[transfer_id] = {
            "type": "upload",
            "file_name": file_name,
            "file_size": file_size,
            "start_time": time.time(),
            "user_id": user_id,
            "request_id": request_id,
            "status": "in_progress"
        }
        
        app_logger.info(f"Started tracking upload: {file_name} ({file_size} bytes)")
        return transfer_id
    
    def complete_upload_tracking(self, 
                               transfer_id: str, 
                               destination_path: str,
                               status: str = "success") -> Dict[str, Any]:
        """Complete upload tracking"""
        if transfer_id not in self.active_transfers:
            app_logger.warning(f"Upload tracking ID not found: {transfer_id}")
            return {}
        
        transfer_info = self.active_transfers[transfer_id]
        transfer_time = time.time() - transfer_info["start_time"]
        
        # Log completion
        server_logger.log_data_transfer(
            transfer_type="upload_complete",
            file_name=transfer_info["file_name"],
            file_size=transfer_info["file_size"],
            source="client",
            destination=destination_path,
            transfer_time=transfer_time,
            status=status,
            user_id=transfer_info["user_id"],
            request_id=transfer_info["request_id"],
            transfer_id=transfer_id
        )
        
        # Update status
        transfer_info["status"] = status
        transfer_info["end_time"] = time.time()
        transfer_info["destination_path"] = destination_path
        
        # Remove from active transfers
        del self.active_transfers[transfer_id]
        
        app_logger.info(f"Completed upload tracking: {transfer_info['file_name']} in {transfer_time:.2f}s")
        return transfer_info
    
    def start_download_tracking(self, 
                              file_name: str, 
                              file_size: int,
                              source_path: str,
                              user_id: str = None,
                              request_id: str = None) -> str:
        """Start tracking a file download"""
        transfer_id = server_logger.log_data_transfer(
            transfer_type="download_start",
            file_name=file_name,
            file_size=file_size,
            source=source_path,
            destination="client",
            transfer_time=0.0,
            status="started",
            user_id=user_id,
            request_id=request_id
        )
        
        self.active_transfers[transfer_id] = {
            "type": "download",
            "file_name": file_name,
            "file_size": file_size,
            "source_path": source_path,
            "start_time": time.time(),
            "user_id": user_id,
            "request_id": request_id,
            "status": "in_progress"
        }
        
        app_logger.info(f"Started tracking download: {file_name} ({file_size} bytes)")
        return transfer_id
    
    def complete_download_tracking(self, 
                                 transfer_id: str,
                                 status: str = "success") -> Dict[str, Any]:
        """Complete download tracking"""
        if transfer_id not in self.active_transfers:
            app_logger.warning(f"Download tracking ID not found: {transfer_id}")
            return {}
        
        transfer_info = self.active_transfers[transfer_id]
        transfer_time = time.time() - transfer_info["start_time"]
        
        # Log completion
        server_logger.log_data_transfer(
            transfer_type="download_complete",
            file_name=transfer_info["file_name"],
            file_size=transfer_info["file_size"],
            source=transfer_info["source_path"],
            destination="client",
            transfer_time=transfer_time,
            status=status,
            user_id=transfer_info["user_id"],
            request_id=transfer_info["request_id"],
            transfer_id=transfer_id
        )
        
        # Update status
        transfer_info["status"] = status
        transfer_info["end_time"] = time.time()
        
        # Remove from active transfers
        del self.active_transfers[transfer_id]
        
        app_logger.info(f"Completed download tracking: {transfer_info['file_name']} in {transfer_time:.2f}s")
        return transfer_info
    
    def track_file_processing(self, 
                            file_name: str,
                            file_size: int,
                            processing_type: str,
                            source_path: str,
                            destination_path: str = None,
                            user_id: str = None,
                            request_id: str = None,
                            **kwargs) -> str:
        """Track file processing operations"""
        start_time = time.time()
        
        transfer_id = server_logger.log_data_transfer(
            transfer_type=f"processing_{processing_type}",
            file_name=file_name,
            file_size=file_size,
            source=source_path,
            destination=destination_path or "processing",
            transfer_time=0.0,
            status="started",
            user_id=user_id,
            request_id=request_id,
            processing_type=processing_type,
            **kwargs
        )
        
        self.active_transfers[transfer_id] = {
            "type": "processing",
            "processing_type": processing_type,
            "file_name": file_name,
            "file_size": file_size,
            "source_path": source_path,
            "destination_path": destination_path,
            "start_time": start_time,
            "user_id": user_id,
            "request_id": request_id,
            "status": "in_progress",
            **kwargs
        }
        
        app_logger.info(f"Started tracking {processing_type} processing: {file_name}")
        return transfer_id
    
    def complete_file_processing(self, 
                               transfer_id: str,
                               output_size: int = None,
                               status: str = "success",
                               **kwargs) -> Dict[str, Any]:
        """Complete file processing tracking"""
        if transfer_id not in self.active_transfers:
            app_logger.warning(f"Processing tracking ID not found: {transfer_id}")
            return {}
        
        transfer_info = self.active_transfers[transfer_id]
        processing_time = time.time() - transfer_info["start_time"]
        
        # Log completion
        server_logger.log_data_transfer(
            transfer_type=f"processing_{transfer_info['processing_type']}_complete",
            file_name=transfer_info["file_name"],
            file_size=transfer_info["file_size"],
            source=transfer_info["source_path"],
            destination=transfer_info["destination_path"],
            transfer_time=processing_time,
            status=status,
            user_id=transfer_info["user_id"],
            request_id=transfer_info["request_id"],
            transfer_id=transfer_id,
            output_size=output_size,
            **kwargs
        )
        
        # Update status
        transfer_info["status"] = status
        transfer_info["end_time"] = time.time()
        transfer_info["output_size"] = output_size
        transfer_info.update(kwargs)
        
        # Remove from active transfers
        del self.active_transfers[transfer_id]
        
        app_logger.info(f"Completed {transfer_info['processing_type']} processing: {transfer_info['file_name']} in {processing_time:.2f}s")
        return transfer_info
    
    def track_translation_operation(self, 
                                  text_length: int,
                                  source_language: str,
                                  target_languages: list,
                                  domain: str = None,
                                  user_id: str = None,
                                  request_id: str = None) -> str:
        """Track translation operations"""
        start_time = time.time()
        
        transfer_id = server_logger.log_data_transfer(
            transfer_type="translation",
            file_name=f"text_translation_{len(target_languages)}_languages",
            file_size=text_length,
            source=source_language,
            destination=",".join(target_languages),
            transfer_time=0.0,
            status="started",
            user_id=user_id,
            request_id=request_id,
            source_language=source_language,
            target_languages=target_languages,
            domain=domain,
            text_length=text_length
        )
        
        self.active_transfers[transfer_id] = {
            "type": "translation",
            "text_length": text_length,
            "source_language": source_language,
            "target_languages": target_languages,
            "domain": domain,
            "start_time": start_time,
            "user_id": user_id,
            "request_id": request_id,
            "status": "in_progress"
        }
        
        app_logger.info(f"Started tracking translation: {source_language} -> {target_languages}")
        return transfer_id
    
    def complete_translation_operation(self, 
                                     transfer_id: str,
                                     results_count: int = 0,
                                     status: str = "success",
                                     **kwargs) -> Dict[str, Any]:
        """Complete translation operation tracking"""
        if transfer_id not in self.active_transfers:
            app_logger.warning(f"Translation tracking ID not found: {transfer_id}")
            return {}
        
        transfer_info = self.active_transfers[transfer_id]
        processing_time = time.time() - transfer_info["start_time"]
        
        # Log completion
        server_logger.log_data_transfer(
            transfer_type="translation_complete",
            file_name=f"translation_{transfer_info['source_language']}_to_{len(transfer_info['target_languages'])}_languages",
            file_size=transfer_info["text_length"],
            source=transfer_info["source_language"],
            destination=",".join(transfer_info["target_languages"]),
            transfer_time=processing_time,
            status=status,
            user_id=transfer_info["user_id"],
            request_id=transfer_info["request_id"],
            transfer_id=transfer_id,
            results_count=results_count,
            **kwargs
        )
        
        # Update status
        transfer_info["status"] = status
        transfer_info["end_time"] = time.time()
        transfer_info["results_count"] = results_count
        transfer_info.update(kwargs)
        
        # Remove from active transfers
        del self.active_transfers[transfer_id]
        
        app_logger.info(f"Completed translation: {transfer_info['source_language']} -> {transfer_info['target_languages']} in {processing_time:.2f}s")
        return transfer_info
    
    def get_active_transfers(self) -> Dict[str, Dict[str, Any]]:
        """Get all currently active transfers"""
        return self.active_transfers.copy()
    
    def get_transfer_stats(self) -> Dict[str, Any]:
        """Get transfer statistics"""
        active_count = len(self.active_transfers)
        active_by_type = {}
        
        for transfer in self.active_transfers.values():
            transfer_type = transfer.get("type", "unknown")
            active_by_type[transfer_type] = active_by_type.get(transfer_type, 0) + 1
        
        return {
            "active_transfers": active_count,
            "active_by_type": active_by_type,
            "active_transfers_detail": self.active_transfers
        }


# Global data transfer tracker instance
data_transfer_tracker = DataTransferTracker()
