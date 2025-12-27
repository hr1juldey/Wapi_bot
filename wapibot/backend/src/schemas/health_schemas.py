"""Health check response schemas."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ServiceHealth(BaseModel):
    """Individual service health status."""
    status: str = Field(..., description="Health status: healthy, degraded, unhealthy")
    message: str = Field(..., description="Human-readable status message")
    latency_ms: Optional[float] = Field(None, description="Response latency in milliseconds")
    enabled: Optional[bool] = Field(None, description="Whether service is enabled")
    error: Optional[str] = Field(None, description="Error message if unhealthy")


class HealthStatusResponse(BaseModel):
    """Overall system health status."""
    status: str = Field(..., description="Overall status: healthy or degraded")
    timestamp: str = Field(..., description="ISO timestamp of health check")
    services: Dict[str, ServiceHealth] = Field(..., description="Status of each service")


class DiagnosisResponse(BaseModel):
    """Comprehensive diagnostic report."""
    timestamp: str = Field(..., description="ISO timestamp of diagnosis")
    overall_status: str = Field(..., description="Overall health: healthy or unhealthy")
    checks: Dict[str, Dict[str, Any]] = Field(..., description="Detailed check results")
    recommendations: List[str] = Field(default_factory=list, description="Actionable fixes")