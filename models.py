"""
Data models for opportunities, capability profiles, and scoring results.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class OpportunityDomain(str, Enum):
    """Primary opportunity domains."""
    AI = "AI"
    DATA = "Data"
    CLOUD = "Cloud"
    CYBER = "Cybersecurity"
    IT_OPS = "IT Operations"
    SOFTWARE = "Software Engineering"
    MODERNIZATION = "Modernization"
    OTHER = "Other"


class Complexity(str, Enum):
    """Technical complexity levels."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class ProjectType(str, Enum):
    """Project type classification."""
    MODERNIZATION = "Modernization"
    OPERATIONS = "Operations"
    GREENFIELD = "Greenfield"
    LEGACY = "Legacy"


class RecommendedAction(str, Enum):
    """Recommended action for opportunity."""
    BID = "BID"
    TEAM_SUB = "TEAM / SUB"
    IGNORE = "IGNORE"


class Opportunity(BaseModel):
    """SAM.gov opportunity data model."""
    notice_id: str
    title: str
    description: str
    agency: str
    sub_agency: Optional[str] = None
    naics: List[str] = Field(default_factory=list)
    psc: Optional[str] = None
    set_aside: Optional[str] = None
    contract_type: Optional[str] = None
    response_type: Optional[str] = None  # RFI, RFP, RFQ, Sources Sought
    due_date: Optional[datetime] = None
    place_of_performance: Optional[str] = None
    posted_date: Optional[datetime] = None
    url: Optional[str] = None
    
    # AI Classification fields (populated by classification engine)
    primary_domain: Optional[OpportunityDomain] = None
    secondary_domains: List[OpportunityDomain] = Field(default_factory=list)
    complexity: Optional[Complexity] = None
    project_type: Optional[ProjectType] = None
    is_legacy: Optional[bool] = None
    
    class Config:
        use_enum_values = True


class CapabilityProfile(BaseModel):
    """Company capability profile for matching."""
    company_name: str
    core_domains: List[str] = Field(default_factory=list)
    technical_skills: List[str] = Field(default_factory=list)
    naics: List[str] = Field(default_factory=list)
    preferred_agencies: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    offices: List[str] = Field(default_factory=list, description="Office locations (city, state or full address)")
    role_preference: str = "Prime"  # Prime, Subcontractor, Either
    min_contract_value: Optional[float] = None
    max_contract_value: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "company_name": "Onyx Government Services",
                "core_domains": [
                    "AI/ML",
                    "Data Analytics/Engineering",
                    "Cloud Architecture & Migration",
                    "DevSecOps/Automation",
                    "Cybersecurity/Zero Trust",
                    "IT Modernization"
                ],
                "technical_skills": [
                    "Python",
                    "SAS",
                    "SQL",
                    "AWS",
                    "Azure",
                    "Kubernetes",
                    "Terraform",
                    "LLMs"
                ],
                "naics": ["541511", "541512", "541519"],
                "preferred_agencies": ["DoD", "Air Force", "DHS"],
                "certifications": ["SDVOSB"],
                "role_preference": "Subcontractor"
            }
        }


class FitScoreBreakdown(BaseModel):
    """Detailed breakdown of fit score components."""
    domain_match: float = Field(ge=0, le=100, description="Domain match score (0-100)")
    naics_match: float = Field(ge=0, le=100, description="NAICS match score (0-100)")
    technical_skill_match: float = Field(ge=0, le=100, description="Technical skill match (0-100)")
    agency_alignment: float = Field(ge=0, le=100, description="Agency alignment (0-100)")
    contract_type_fit: float = Field(ge=0, le=100, description="Contract type fit (0-100)")
    strategic_value: float = Field(ge=0, le=100, description="Strategic value (0-100)")


class OpportunityScore(BaseModel):
    """AI-generated fit score and recommendation for an opportunity."""
    opportunity: Opportunity
    capability_profile: CapabilityProfile
    fit_score: float = Field(ge=0, le=100, description="Overall fit score (0-100)")
    breakdown: FitScoreBreakdown
    explanation: str = Field(description="Plain-English explanation of the fit")
    risk_factors: List[str] = Field(default_factory=list)
    recommended_action: RecommendedAction
    reasoning: str = Field(description="Detailed AI reasoning for the recommendation")
    
    class Config:
        use_enum_values = True
