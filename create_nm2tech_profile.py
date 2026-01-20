"""
Script to create NM2TECH company capability profile.
Run this to create or update the NM2TECH profile.
"""
from profile_manager import profile_manager

def create_nm2tech_profile():
    """Create NM2TECH capability profile."""
    
    # TODO: Update these values based on NM2TECH's actual capabilities
    profile = profile_manager.create_profile(
        company_name="NM2TECH",
        core_domains=[
            "AI/ML",  # Update based on your capabilities
            "Data Analytics/Engineering",
            "Cloud Architecture & Migration",
            "DevSecOps/Automation",
            "Cybersecurity/Zero Trust",
            "IT Modernization"
        ],
        technical_skills=[
            "Python",  # Update with your actual tech stack
            "Java",
            "AWS",
            "Azure",
            "Kubernetes",
            "Docker",
            "Terraform",
            "SQL",
            "Machine Learning",
            "LLMs"
        ],
        naics=[
            "541511",  # Custom Computer Programming Services
            "541512",  # Computer Systems Design Services
            "541519",  # Other Computer Related Services
            "541511"   # Add more as needed
        ],
        preferred_agencies=[
            "DoD",
            "DHS",
            "GSA",
            "Department of Defense"
        ],
        certifications=[
            # Add your certifications: "SDVOSB", "8(a)", "WOSB", "HUBZone", etc.
        ],
        offices=[
            # Add your office locations: "Washington, DC", "Arlington, VA", etc.
        ],
        role_preference="Either"  # Prime, Subcontractor, or Either
    )
    
    print(f"✅ Successfully created profile for {profile.company_name}")
    print(f"\nProfile Details:")
    print(f"  Core Domains: {', '.join(profile.core_domains)}")
    print(f"  Technical Skills: {', '.join(profile.technical_skills)}")
    print(f"  NAICS Codes: {', '.join(profile.naics)}")
    print(f"  Preferred Agencies: {', '.join(profile.preferred_agencies)}")
    print(f"  Certifications: {', '.join(profile.certifications) if profile.certifications else 'None'}")
    print(f"  Offices: {', '.join(profile.offices) if profile.offices else 'None'}")
    print(f"  Role Preference: {profile.role_preference}")
    
    return profile

if __name__ == "__main__":
    print("Creating NM2TECH capability profile...")
    print("=" * 60)
    print("\n⚠️  NOTE: This script uses default values.")
    print("   Please edit this script with NM2TECH's actual capabilities before running.")
    print("   Or use the Streamlit UI to create/edit the profile interactively.\n")
    print("=" * 60)
    
    # Uncomment the line below after updating the values above
    # create_nm2tech_profile()
