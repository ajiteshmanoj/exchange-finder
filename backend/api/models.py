"""
Pydantic models for NTU Exchange University Recommendation API.
Defines request and response schemas with validation.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional


# ============= REQUEST MODELS =============

class NTUCredentials(BaseModel):
    """NTU SSO credentials for authentication"""
    username: str = Field(..., min_length=1, description="NTU network username (e.g., AJITESH001)")
    password: str = Field(..., min_length=1, description="NTU password")
    domain: str = Field(default="Student", description="NTU domain (Student/Staff)")

    @validator('domain')
    def validate_domain(cls, v):
        """Validate domain is either Student or Staff"""
        if v.upper() not in ['STUDENT', 'STAFF']:
            raise ValueError('Domain must be Student or Staff')
        return v.capitalize()

    class Config:
        json_schema_extra = {
            "example": {
                "username": "AJITESH001",
                "password": "your_password",
                "domain": "Student"
            }
        }


class SearchRequest(BaseModel):
    """Request model for university search endpoint"""
    credentials: NTUCredentials
    target_countries: Optional[List[str]] = Field(
        default=None,
        description="List of countries to filter (None = use config defaults)"
    )
    target_modules: Optional[List[str]] = Field(
        default=None,
        description="List of NTU module codes (None = use config defaults)"
    )
    min_mappable_modules: Optional[int] = Field(
        default=2,
        ge=1,
        description="Minimum number of mappable modules required"
    )
    use_cache: bool = Field(
        default=True,
        description="Whether to use cached data (recommended for faster response)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "credentials": {
                    "username": "AJITESH001",
                    "password": "your_password",
                    "domain": "Student"
                },
                "target_countries": ["Australia", "Denmark", "Sweden"],
                "target_modules": ["SC4001", "SC4002", "SC4062"],
                "min_mappable_modules": 2,
                "use_cache": True
            }
        }


# ============= RESPONSE MODELS =============

class ModuleMapping(BaseModel):
    """Individual module mapping information"""
    ntu_module: str = Field(..., description="NTU module code")
    ntu_module_name: str = Field(..., description="NTU module name")
    partner_module_code: str = Field(..., description="Partner university module code")
    partner_module_name: str = Field(..., description="Partner university module name")
    academic_units: str = Field(..., description="Academic units (AU)")
    status: str = Field(..., description="Mapping status (Approved/Rejected)")
    approval_year: str = Field(..., description="Year of approval")
    semester: str = Field(..., description="Semester")

    class Config:
        json_schema_extra = {
            "example": {
                "ntu_module": "SC4001",
                "ntu_module_name": "Neural Networks & Deep Learning",
                "partner_module_code": "COMP3308",
                "partner_module_name": "Introduction to Artificial Intelligence",
                "academic_units": "6",
                "status": "Approved",
                "approval_year": "2024",
                "semester": "1"
            }
        }


class UniversityResult(BaseModel):
    """Single university result with mappings"""
    rank: int = Field(..., description="Overall rank")
    name: str = Field(..., description="University name")
    country: str = Field(..., description="Country")
    university_code: str = Field(..., description="University code")
    sem1_spots: int = Field(..., description="Semester 1 available spots")
    min_cgpa: float = Field(..., description="Minimum CGPA requirement")
    mappable_count: int = Field(..., description="Number of mappable modules")
    coverage_score: float = Field(..., description="Coverage percentage")
    mappable_modules: Dict[str, List[ModuleMapping]] = Field(..., description="Mappable modules grouped by NTU module code")
    unmappable_modules: List[str] = Field(..., description="List of unmappable modules")
    remarks: str = Field(default="", description="Additional remarks")

    class Config:
        json_schema_extra = {
            "example": {
                "rank": 1,
                "name": "University of Melbourne",
                "country": "Australia",
                "university_code": "AU-MELB",
                "sem1_spots": 3,
                "min_cgpa": 3.7,
                "mappable_count": 4,
                "coverage_score": 66.7,
                "mappable_modules": {
                    "SC4001": [
                        {
                            "ntu_module": "SC4001",
                            "ntu_module_name": "Neural Networks & Deep Learning",
                            "partner_module_code": "COMP30027",
                            "partner_module_name": "Machine Learning",
                            "academic_units": "6",
                            "status": "Approved",
                            "approval_year": "2024",
                            "semester": "1"
                        }
                    ]
                },
                "unmappable_modules": ["SC4062"],
                "remarks": "Group of Eight member"
            }
        }


class SearchResponse(BaseModel):
    """Response model for search endpoint"""
    status: str = Field(default="success", description="Response status")
    message: str = Field(..., description="Human-readable message")
    execution_time_seconds: float = Field(..., description="Total execution time in seconds")
    cache_used: bool = Field(..., description="Whether cached data was used")
    cache_timestamp: Optional[str] = Field(default=None, description="Timestamp of cached data (ISO format)")
    results_count: int = Field(..., description="Number of universities found")
    results: List[UniversityResult] = Field(..., description="List of university results")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Found 25 universities matching criteria",
                "execution_time_seconds": 1.2,
                "cache_used": True,
                "cache_timestamp": "2025-12-25T10:30:00",
                "results_count": 25,
                "results": [
                    {
                        "rank": 1,
                        "name": "University of Melbourne",
                        "country": "Australia",
                        "university_code": "AU-MELB",
                        "sem1_spots": 3,
                        "min_cgpa": 3.7,
                        "mappable_count": 4,
                        "coverage_score": 66.7,
                        "mappable_modules": {},
                        "unmappable_modules": ["SC4062"],
                        "remarks": ""
                    }
                ]
            }
        }


class CacheClearResponse(BaseModel):
    """Response for cache clear operation"""
    status: str = Field(default="success", description="Operation status")
    message: str = Field(..., description="Operation result message")
    cleared_items: List[str] = Field(..., description="List of cleared cache items")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Cleared 5 cache items",
                "cleared_items": [
                    "universities.json",
                    "mappings/abc123.json",
                    "mappings/def456.json"
                ]
            }
        }


class ErrorResponse(BaseModel):
    """Error response model"""
    status: str = Field(default="error", description="Status indicating error")
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(default=None, description="Additional error details")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "error": "Authentication failed: Invalid credentials",
                "details": "Login failed - check username and password"
            }
        }
