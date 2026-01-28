"""
Log Management and Monitoring Routes
Provides endpoints for viewing and managing server logs
"""
from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from app.utils.server_logger import server_logger
from app.utils.data_transfer_tracker import data_transfer_tracker
from app.utils.logger import app_logger

router = APIRouter(prefix="/logs", tags=["Logs"])


@router.get("/server-stats")
async def get_server_stats():
    """Get comprehensive server statistics"""
    try:
        stats = server_logger.get_server_stats()
        transfer_stats = data_transfer_tracker.get_transfer_stats()
        
        return {
            "status": "success",
            "server_stats": stats,
            "transfer_stats": transfer_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        app_logger.error(f"Failed to get server stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get server statistics: {str(e)}"
        )


@router.get("/requests")
async def get_recent_requests(
    limit: int = Query(100, ge=1, le=1000, description="Number of requests to return"),
    hours: int = Query(24, ge=1, le=168, description="Hours to look back")
):
    """Get recent HTTP requests"""
    try:
        requests = server_logger.get_recent_requests(limit)
        
        # Filter by time if specified
        if hours < 24:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            requests = [
                req for req in requests 
                if datetime.fromisoformat(req.get("timestamp", "")).replace(tzinfo=None) >= cutoff_time
            ]
        
        return {
            "status": "success",
            "requests": requests,
            "count": len(requests),
            "limit": limit,
            "hours": hours,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        app_logger.error(f"Failed to get recent requests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recent requests: {str(e)}"
        )


@router.get("/transfers")
async def get_recent_transfers(
    limit: int = Query(100, ge=1, le=1000, description="Number of transfers to return"),
    hours: int = Query(24, ge=1, le=168, description="Hours to look back")
):
    """Get recent data transfers"""
    try:
        transfers = server_logger.get_recent_transfers(limit)
        
        # Filter by time if specified
        if hours < 24:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            transfers = [
                transfer for transfer in transfers 
                if datetime.fromisoformat(transfer.get("timestamp", "")).replace(tzinfo=None) >= cutoff_time
            ]
        
        return {
            "status": "success",
            "transfers": transfers,
            "count": len(transfers),
            "limit": limit,
            "hours": hours,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        app_logger.error(f"Failed to get recent transfers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recent transfers: {str(e)}"
        )


@router.get("/activities")
async def get_recent_activities(
    limit: int = Query(100, ge=1, le=1000, description="Number of activities to return"),
    hours: int = Query(24, ge=1, le=168, description="Hours to look back")
):
    """Get recent server activities"""
    try:
        activities = server_logger.get_recent_activities(limit)
        
        # Filter by time if specified
        if hours < 24:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            activities = [
                activity for activity in activities 
                if datetime.fromisoformat(activity.get("timestamp", "")).replace(tzinfo=None) >= cutoff_time
            ]
        
        return {
            "status": "success",
            "activities": activities,
            "count": len(activities),
            "limit": limit,
            "hours": hours,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        app_logger.error(f"Failed to get recent activities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recent activities: {str(e)}"
        )


@router.get("/active-transfers")
async def get_active_transfers():
    """Get currently active data transfers"""
    try:
        active_transfers = data_transfer_tracker.get_active_transfers()
        
        return {
            "status": "success",
            "active_transfers": active_transfers,
            "count": len(active_transfers),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        app_logger.error(f"Failed to get active transfers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active transfers: {str(e)}"
        )


@router.get("/performance")
async def get_performance_metrics(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back")
):
    """Get performance metrics"""
    try:
        # Get recent performance logs
        performance_logs = []
        # This would need to be implemented in server_logger
        # For now, return basic metrics
        
        server_stats = server_logger.get_server_stats()
        
        return {
            "status": "success",
            "performance_metrics": {
                "uptime_seconds": server_stats["uptime_seconds"],
                "total_requests": server_stats["total_requests"],
                "requests_per_second": server_stats["requests_per_second"],
                "total_data_transferred_mb": server_stats["total_data_transferred_mb"],
                "data_transfer_rate_mbps": server_stats["data_transfer_rate_mbps"]
            },
            "hours": hours,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        app_logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance metrics: {str(e)}"
        )


@router.get("/summary")
async def get_logs_summary(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back")
):
    """Get comprehensive logs summary"""
    try:
        # Get recent data
        requests = server_logger.get_recent_requests(1000)
        transfers = server_logger.get_recent_transfers(1000)
        activities = server_logger.get_recent_activities(1000)
        
        # Filter by time
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        recent_requests = [
            req for req in requests 
            if datetime.fromisoformat(req.get("timestamp", "")).replace(tzinfo=None) >= cutoff_time
        ]
        
        recent_transfers = [
            transfer for transfer in transfers 
            if datetime.fromisoformat(transfer.get("timestamp", "")).replace(tzinfo=None) >= cutoff_time
        ]
        
        recent_activities = [
            activity for activity in activities 
            if datetime.fromisoformat(activity.get("timestamp", "")).replace(tzinfo=None) >= cutoff_time
        ]
        
        # Calculate summary statistics
        total_requests = len(recent_requests)
        total_transfers = len(recent_transfers)
        total_activities = len(recent_activities)
        
        # Request statistics
        request_stats = {
            "total": total_requests,
            "by_method": {},
            "by_status": {},
            "by_path": {},
            "avg_processing_time": 0.0
        }
        
        total_processing_time = 0.0
        for req in recent_requests:
            method = req.get("method", "unknown")
            status_code = req.get("status_code", 0)
            path = req.get("path", "unknown")
            processing_time = req.get("processing_time_seconds", 0.0)
            
            request_stats["by_method"][method] = request_stats["by_method"].get(method, 0) + 1
            request_stats["by_status"][str(status_code)] = request_stats["by_status"].get(str(status_code), 0) + 1
            request_stats["by_path"][path] = request_stats["by_path"].get(path, 0) + 1
            total_processing_time += processing_time
        
        if total_requests > 0:
            request_stats["avg_processing_time"] = total_processing_time / total_requests
        
        # Transfer statistics
        transfer_stats = {
            "total": total_transfers,
            "by_type": {},
            "total_data_transferred": 0,
            "avg_transfer_time": 0.0
        }
        
        total_transfer_time = 0.0
        total_data = 0
        for transfer in recent_transfers:
            transfer_type = transfer.get("transfer_type", "unknown")
            file_size = transfer.get("file_size_bytes", 0)
            transfer_time = transfer.get("transfer_time_seconds", 0.0)
            
            transfer_stats["by_type"][transfer_type] = transfer_stats["by_type"].get(transfer_type, 0) + 1
            total_data += file_size
            total_transfer_time += transfer_time
        
        transfer_stats["total_data_transferred"] = total_data
        if total_transfers > 0:
            transfer_stats["avg_transfer_time"] = total_transfer_time / total_transfers
        
        # Activity statistics
        activity_stats = {
            "total": total_activities,
            "by_type": {},
            "by_level": {}
        }
        
        for activity in recent_activities:
            activity_type = activity.get("activity_type", "unknown")
            level = activity.get("level", "unknown")
            
            activity_stats["by_type"][activity_type] = activity_stats["by_type"].get(activity_type, 0) + 1
            activity_stats["by_level"][level] = activity_stats["by_level"].get(level, 0) + 1
        
        return {
            "status": "success",
            "summary": {
                "time_range_hours": hours,
                "requests": request_stats,
                "transfers": transfer_stats,
                "activities": activity_stats
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        app_logger.error(f"Failed to get logs summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get logs summary: {str(e)}"
        )


@router.post("/cleanup")
async def cleanup_old_logs(
    days_to_keep: int = Query(30, ge=1, le=365, description="Days of logs to keep")
):
    """Clean up old log files"""
    try:
        server_logger.cleanup_old_logs(days_to_keep)
        
        return {
            "status": "success",
            "message": f"Cleaned up logs older than {days_to_keep} days",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        app_logger.error(f"Failed to cleanup logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup logs: {str(e)}"
        )
