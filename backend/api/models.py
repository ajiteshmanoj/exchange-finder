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


class LoginRequest(BaseModel):
    """Request model for login verification"""
    credentials: NTUCredentials

    class Config:
        json_schema_extra = {
            "example": {
                "credentials": {
                    "username": "AJITESH001",
                    "password": "your_password",
                    "domain": "Student"
                }
            }
        }


class LoginResponse(BaseModel):
    """Response model for login verification"""
    success: bool = Field(..., description="Whether login was successful")
    message: str = Field(..., description="Login result message")
    username: Optional[str] = Field(default=None, description="Authenticated username")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Login successful",
                "username": "AJITESH001"
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
    sem2_spots: int = Field(default=0, description="Semester 2 available spots")
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
                "sem2_spots": 2,
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


# ============= WEBSOCKET MESSAGE MODELS =============

class ProgressMessage(BaseModel):
    """WebSocket progress message for real-time updates"""
    type: str = Field(default="progress", description="Message type")
    step: int = Field(..., ge=1, le=3, description="Current pipeline step (1=PDF, 2=Scraping, 3=Processing)")
    step_name: str = Field(..., description="Human-readable step name")
    message: str = Field(..., description="Progress message")
    details: Optional[Dict] = Field(default=None, description="Additional progress details")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "progress",
                "step": 2,
                "step_name": "Module Mapping Scraping",
                "message": "Processing 5/45: University of Melbourne",
                "details": {
                    "current": 5,
                    "total": 45,
                    "university": "University of Melbourne",
                    "country": "Australia",
                    "found_modules": 3
                }
            }
        }


class CompleteMessage(BaseModel):
    """WebSocket completion message with final results"""
    type: str = Field(default="complete", description="Message type")
    message: str = Field(..., description="Completion message")
    execution_time: float = Field(..., description="Total execution time in seconds")
    results_count: int = Field(..., description="Number of universities found")
    results: List[UniversityResult] = Field(..., description="List of university results")
    cache_used: bool = Field(..., description="Whether cached data was used")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "complete",
                "message": "Found 25 universities matching criteria",
                "execution_time": 1234.5,
                "results_count": 25,
                "results": [],
                "cache_used": False
            }
        }


class ErrorMessage(BaseModel):
    """WebSocket error message"""
    type: str = Field(default="error", description="Message type")
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(default=None, description="Additional error details")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "error",
                "error": "Login failed - Invalid credentials",
                "details": "Please check your username and password"
            }
        }


class CountryUniversity(BaseModel):
    """Single country with its universities"""
    country: str = Field(..., description="Country name")
    universities: List[str] = Field(..., description="List of university names")
    university_count: int = Field(..., description="Number of universities in this country")

    class Config:
        json_schema_extra = {
            "example": {
                "country": "Australia",
                "universities": ["University of Melbourne", "University of Sydney"],
                "university_count": 45
            }
        }


class CountriesUniversitiesResponse(BaseModel):
    """Response for countries-universities endpoint"""
    status: str = Field(default="success", description="Response status")
    message: str = Field(..., description="Human-readable message")
    cache_used: bool = Field(..., description="Whether cached data was used")
    cache_timestamp: Optional[str] = Field(default=None, description="Cache timestamp")
    total_countries: int = Field(..., description="Total number of countries")
    total_universities: int = Field(..., description="Total number of universities")
    countries: List[CountryUniversity] = Field(..., description="List of countries with universities")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Retrieved 85 countries with 1234 universities",
                "cache_used": True,
                "cache_timestamp": "2025-12-25T10:30:00",
                "total_countries": 85,
                "total_universities": 1234,
                "countries": [
                    {
                        "country": "Australia",
                        "universities": ["University of Melbourne"],
                        "university_count": 45
                    }
                ]
            }
        }


class CountriesUniversitiesRequest(BaseModel):
    """Request for countries-universities endpoint"""
    credentials: NTUCredentials
    use_cache: bool = Field(default=True, description="Whether to use cached data")

    class Config:
        json_schema_extra = {
            "example": {
                "credentials": {
                    "username": "AJITESH001",
                    "password": "your_password",
                    "domain": "Student"
                },
                "use_cache": True
            }
        }


# ============= ADMIN MODELS =============

class AdminScrapeRequest(BaseModel):
    """Request to trigger admin full scrape"""
    credentials: NTUCredentials
    headless: bool = Field(default=True, description="Run browser in headless mode")

    class Config:
        json_schema_extra = {
            "example": {
                "credentials": {
                    "username": "AJITESH001",
                    "password": "your_password",
                    "domain": "Student"
                },
                "headless": True
            }
        }


class ScrapeJobStatus(BaseModel):
    """Status of a scrape job"""
    job_id: int = Field(..., description="Scrape job ID")
    status: str = Field(..., description="Job status (running/completed/failed/cancelled)")
    total_countries: int = Field(default=0, description="Total countries to scrape")
    completed_countries: int = Field(default=0, description="Countries completed")
    total_universities: int = Field(default=0, description="Total universities to scrape")
    completed_universities: int = Field(default=0, description="Universities completed")
    current_country: Optional[str] = Field(default=None, description="Currently processing country")
    current_university: Optional[str] = Field(default=None, description="Currently processing university")
    started_at: Optional[str] = Field(default=None, description="Job start time (ISO format)")
    completed_at: Optional[str] = Field(default=None, description="Job completion time (ISO format)")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": 1,
                "status": "running",
                "total_countries": 45,
                "completed_countries": 12,
                "total_universities": 900,
                "completed_universities": 245,
                "current_country": "Denmark",
                "current_university": "University of Copenhagen",
                "started_at": "2025-12-25T10:30:00",
                "completed_at": None,
                "error_message": None
            }
        }


class ScrapeStartResponse(BaseModel):
    """Response when starting a scrape job"""
    status: str = Field(default="started", description="Job status")
    job_id: int = Field(..., description="Scrape job ID for tracking")
    message: str = Field(..., description="Status message")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "started",
                "job_id": 1,
                "message": "Full scrape started. Use /api/admin/scrape/status/1 to track progress."
            }
        }


class DatabaseStatusResponse(BaseModel):
    """Response for database status check"""
    populated: bool = Field(..., description="Whether database has data")
    total_countries: int = Field(default=0, description="Number of countries in database")
    total_universities: int = Field(default=0, description="Number of universities in database")
    total_mappings: int = Field(default=0, description="Number of module mappings in database")
    unique_modules: int = Field(default=0, description="Number of unique NTU modules")
    last_scrape: Optional[str] = Field(default=None, description="Last successful scrape timestamp")
    db_path: str = Field(..., description="Database file path")

    class Config:
        json_schema_extra = {
            "example": {
                "populated": True,
                "total_countries": 45,
                "total_universities": 900,
                "total_mappings": 15000,
                "unique_modules": 150,
                "last_scrape": "2025-12-25T10:30:00",
                "db_path": "data/exchange_mappings.db"
            }
        }


class DatabaseSearchRequest(BaseModel):
    """Request for searching pre-scraped database (no credentials needed)"""
    target_modules: List[str] = Field(
        ...,
        min_length=1,
        description="List of NTU module codes to search for"
    )
    target_countries: Optional[List[str]] = Field(
        default=None,
        description="Optional list of countries to filter by"
    )
    target_semester: Optional[int] = Field(
        default=None,
        ge=1,
        le=2,
        description="Target semester (1, 2, or null for both). Filters universities with spots in selected semester."
    )
    min_mappable_modules: int = Field(
        default=1,
        ge=1,
        description="Minimum number of mappable modules required"
    )

    @validator('target_modules')
    def validate_modules(cls, v):
        """Ensure module codes are uppercase"""
        return [m.upper() for m in v]

    class Config:
        json_schema_extra = {
            "example": {
                "target_modules": ["SC4001", "SC4002", "SC4062"],
                "target_countries": ["Australia", "Denmark"],
                "target_semester": 1,
                "min_mappable_modules": 2
            }
        }


class DatabaseSearchResponse(BaseModel):
    """Response for database search (instant results)"""
    status: str = Field(default="success", description="Response status")
    message: str = Field(..., description="Human-readable message")
    execution_time_seconds: float = Field(..., description="Query execution time")
    database_timestamp: Optional[str] = Field(default=None, description="When database was last updated")
    results_count: int = Field(..., description="Number of universities found")
    results: List[UniversityResult] = Field(..., description="List of university results")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Found 25 universities matching criteria",
                "execution_time_seconds": 0.05,
                "database_timestamp": "2025-12-25T10:30:00",
                "results_count": 25,
                "results": []
            }
        }


class ScrapeProgressMessage(BaseModel):
    """WebSocket message for admin scrape progress"""
    type: str = Field(..., description="Message type (started/discovery/university_start/university_complete/country_complete/completed/error)")
    job_id: Optional[int] = Field(default=None, description="Scrape job ID")
    message: Optional[str] = Field(default=None, description="Progress message")
    country: Optional[str] = Field(default=None, description="Current country")
    university: Optional[str] = Field(default=None, description="Current university")
    mappings_found: Optional[int] = Field(default=None, description="Mappings found for current university")
    completed_countries: Optional[int] = Field(default=None, description="Countries completed")
    total_countries: Optional[int] = Field(default=None, description="Total countries")
    completed_universities: Optional[int] = Field(default=None, description="Universities completed")
    total_universities: Optional[int] = Field(default=None, description="Total universities")
    total_mappings: Optional[int] = Field(default=None, description="Total mappings found")
    duration_seconds: Optional[float] = Field(default=None, description="Total duration in seconds")
    error: Optional[str] = Field(default=None, description="Error message if failed")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "university_complete",
                "country": "Australia",
                "university": "University of Melbourne",
                "mappings_found": 25,
                "completed_universities": 45,
                "total_universities": 900
            }
        }
