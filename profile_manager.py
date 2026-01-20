"""
Capability profile manager.
Handles creation, storage, and retrieval of company capability profiles.
"""
import logging
from typing import Optional, List

from database import db
from models import CapabilityProfile

logger = logging.getLogger(__name__)


class ProfileManager:
    """Manages company capability profiles."""
    
    def __init__(self):
        self.db = db
    
    def create_profile(
        self,
        company_name: str,
        core_domains: list,
        technical_skills: list,
        naics: list,
        preferred_agencies: list = None,
        certifications: list = None,
        offices: list = None,
        role_preference: str = "Prime"
    ) -> CapabilityProfile:
        """
        Create a new capability profile.
        
        Args:
            company_name: Company name
            core_domains: List of core capability domains
            technical_skills: List of technical skills
            naics: List of NAICS codes
            preferred_agencies: List of preferred agencies
            certifications: List of certifications (e.g., SDVOSB, 8(a))
            offices: List of office locations (e.g., "Washington, DC", "Arlington, VA")
            role_preference: Prime, Subcontractor, or Either
            
        Returns:
            CapabilityProfile object
        """
        profile = CapabilityProfile(
            company_name=company_name,
            core_domains=core_domains or [],
            technical_skills=technical_skills or [],
            naics=naics or [],
            preferred_agencies=preferred_agencies or [],
            certifications=certifications or [],
            offices=offices or [],
            role_preference=role_preference
        )
        
        # Save to database
        self.db.save_profile(profile)
        logger.info(f"Created profile for {company_name}")
        
        return profile
    
    def get_profile(self, company_name: str) -> Optional[CapabilityProfile]:
        """Get capability profile by company name."""
        return self.db.get_profile(company_name)
    
    def list_all_profiles(self) -> List[str]:
        """Get list of all saved company profile names."""
        return self.db.list_all_profiles()
    
    def update_profile(self, profile: CapabilityProfile) -> CapabilityProfile:
        """Update existing capability profile."""
        self.db.save_profile(profile)
        logger.info(f"Updated profile for {profile.company_name}")
        return profile
    
    def get_default_profile(self) -> CapabilityProfile:
        """Get default example profile (Onyx Government Services)."""
        return CapabilityProfile(
            company_name="Onyx Government Services",
            core_domains=[
                "AI/ML",
                "Data Analytics/Engineering",
                "Cloud Architecture & Migration",
                "DevSecOps/Automation",
                "Cybersecurity/Zero Trust",
                "IT Modernization"
            ],
            technical_skills=[
                "Python",
                "SAS",
                "SQL",
                "AWS",
                "Azure",
                "Kubernetes",
                "Terraform",
                "LLMs"
            ],
            naics=["541511", "541512", "541519"],
            preferred_agencies=["DoD", "Air Force", "DHS"],
            certifications=["SDVOSB"],
            role_preference="Subcontractor"
        )


# Global profile manager instance
profile_manager = ProfileManager()
