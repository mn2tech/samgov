"""
Create an example company profile optimized for 80-100% match scores.
This profile is designed to match well with IT/AI/Data/Cloud opportunities.
"""
import sys
from database import db
from profile_manager import profile_manager
from models import CapabilityProfile

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def create_high_match_profile():
    """Create a profile optimized for high match scores."""
    
    # Create a comprehensive profile that matches well with IT opportunities
    profile = profile_manager.create_profile(
        company_name="TechGov Solutions Inc",
        core_domains=[
            "AI/ML",
            "Data Analytics/Engineering",
            "Cloud Architecture & Migration",
            "DevSecOps/Automation",
            "Cybersecurity/Zero Trust",
            "IT Modernization",
            "Software Engineering",
            "IT Operations"
        ],
        technical_skills=[
            "Python", "Java", "JavaScript", "TypeScript",
            "AWS", "Azure", "GCP", "Cloud Computing",
            "Kubernetes", "Docker", "Terraform", "Ansible",
            "SQL", "NoSQL", "Data Engineering", "ETL",
            "Machine Learning", "Deep Learning", "LLMs", "AI/ML",
            "DevOps", "CI/CD", "GitLab", "Jenkins",
            "Cybersecurity", "Zero Trust", "Security Architecture",
            "Microservices", "API Development", "REST", "GraphQL",
            "Data Analytics", "Business Intelligence", "Tableau", "Power BI",
            "Agile", "Scrum", "Project Management"
        ],
        naics=[
            "541511",  # Custom Computer Programming Services
            "541512",  # Computer Systems Design Services
            "541519",  # Other Computer Related Services
            "541511",  # Custom Computer Programming Services
            "518210",  # Data Processing, Hosting, and Related Services
            "541330",  # Engineering Services
            "541690",  # Other Scientific and Technical Consulting Services
            "541611",  # Administrative Management and General Management Consulting Services
        ],
        preferred_agencies=[
            "DEPT OF DEFENSE",
            "DEPT OF HOMELAND SECURITY",
            "DEPT OF VETERANS AFFAIRS",
            "GENERAL SERVICES ADMINISTRATION",
            "DEPARTMENT OF ENERGY",
            "NATIONAL AERONAUTICS AND SPACE ADMINISTRATION",
            "DEPARTMENT OF HEALTH AND HUMAN SERVICES",
            "DEPARTMENT OF TRANSPORTATION"
        ],
        certifications=[
            "SDVOSB",  # Service-Disabled Veteran-Owned Small Business
            "8(a)",    # 8(a) Business Development Program
            "WOSB",    # Women-Owned Small Business
            "HUBZone"  # Historically Underutilized Business Zone
        ],
        offices=[
            "Washington, DC",
            "Arlington, VA",
            "Alexandria, VA",
            "Reston, VA",
            "San Antonio, TX",
            "Colorado Springs, CO"
        ],
        role_preference="Either",  # Can be Prime or Subcontractor
        tenant_id=None  # Will use current tenant or create default
    )
    
    print("=" * 60)
    print("Created High-Match Profile: TechGov Solutions Inc")
    print("=" * 60)
    print()
    print("Profile Details:")
    print(f"  Company Name: {profile.company_name}")
    print(f"  Core Domains: {len(profile.core_domains)} domains")
    print(f"  Technical Skills: {len(profile.technical_skills)} skills")
    print(f"  NAICS Codes: {len(profile.naics)} codes")
    print(f"  Preferred Agencies: {len(profile.preferred_agencies)} agencies")
    print(f"  Certifications: {', '.join(profile.certifications)}")
    print(f"  Offices: {len(profile.offices)} locations")
    print(f"  Role Preference: {profile.role_preference}")
    print()
    print("This profile is optimized to match 80-100% with:")
    print("  - AI/ML opportunities")
    print("  - Data Analytics/Engineering projects")
    print("  - Cloud Architecture & Migration")
    print("  - DevSecOps/Automation")
    print("  - Cybersecurity/Zero Trust")
    print("  - IT Modernization initiatives")
    print()
    print("✅ Profile created successfully!")
    print()
    print("To use this profile in the app:")
    print("  1. Log in to the Streamlit app")
    print("  2. Select 'TechGov Solutions Inc' from the profile dropdown")
    print("  3. Fetch opportunities and see high match scores!")
    
    return profile


if __name__ == "__main__":
    try:
        # Get or create a default tenant for this example
        # In production, this would use the logged-in user's tenant
        tenant = db.get_or_create_tenant_by_email("example@techgov.com")
        print(f"Using tenant: {tenant.name} (ID: {tenant.id})")
        print()
        
        # Create the profile with tenant_id
        profile = profile_manager.create_profile(
            company_name="TechGov Solutions Inc",
            core_domains=[
                "AI/ML",
                "Data Analytics/Engineering",
                "Cloud Architecture & Migration",
                "DevSecOps/Automation",
                "Cybersecurity/Zero Trust",
                "IT Modernization",
                "Software Engineering",
                "IT Operations"
            ],
            technical_skills=[
                "Python", "Java", "JavaScript", "TypeScript",
                "AWS", "Azure", "GCP", "Cloud Computing",
                "Kubernetes", "Docker", "Terraform", "Ansible",
                "SQL", "NoSQL", "Data Engineering", "ETL",
                "Machine Learning", "Deep Learning", "LLMs", "AI/ML",
                "DevOps", "CI/CD", "GitLab", "Jenkins",
                "Cybersecurity", "Zero Trust", "Security Architecture",
                "Microservices", "API Development", "REST", "GraphQL",
                "Data Analytics", "Business Intelligence", "Tableau", "Power BI",
                "Agile", "Scrum", "Project Management"
            ],
            naics=[
                "541511",  # Custom Computer Programming Services
                "541512",  # Computer Systems Design Services
                "541519",  # Other Computer Related Services
                "518210",  # Data Processing, Hosting, and Related Services
                "541330",  # Engineering Services
                "541690",  # Other Scientific and Technical Consulting Services
                "541611",  # Administrative Management and General Management Consulting Services
            ],
            preferred_agencies=[
                "DEPT OF DEFENSE",
                "DEPT OF HOMELAND SECURITY",
                "DEPT OF VETERANS AFFAIRS",
                "GENERAL SERVICES ADMINISTRATION",
                "DEPARTMENT OF ENERGY",
                "NATIONAL AERONAUTICS AND SPACE ADMINISTRATION",
                "DEPARTMENT OF HEALTH AND HUMAN SERVICES",
                "DEPARTMENT OF TRANSPORTATION"
            ],
            certifications=[
                "SDVOSB",
                "8(a)",
                "WOSB",
                "HUBZone"
            ],
            offices=[
                "Washington, DC",
                "Arlington, VA",
                "Alexandria, VA",
                "Reston, VA",
                "San Antonio, TX",
                "Colorado Springs, CO"
            ],
            role_preference="Either",
            tenant_id=tenant.id
        )
        
        print("=" * 60)
        print("✅ Created High-Match Profile: TechGov Solutions Inc")
        print("=" * 60)
        print()
        print("Profile Summary:")
        print(f"  • Core Domains: {len(profile.core_domains)}")
        print(f"  • Technical Skills: {len(profile.technical_skills)}")
        print(f"  • NAICS Codes: {len(profile.naics)}")
        print(f"  • Preferred Agencies: {len(profile.preferred_agencies)}")
        print(f"  • Certifications: {', '.join(profile.certifications)}")
        print(f"  • Office Locations: {len(profile.offices)}")
        print()
        print("This profile is optimized for 80-100% matches with:")
        print("  ✓ AI/ML opportunities")
        print("  ✓ Data Analytics/Engineering projects")
        print("  ✓ Cloud Architecture & Migration")
        print("  ✓ DevSecOps/Automation")
        print("  ✓ Cybersecurity/Zero Trust")
        print("  ✓ IT Modernization initiatives")
        print()
        print("💡 To use in the app:")
        print("   1. Log in to Streamlit")
        print("   2. Select 'TechGov Solutions Inc' from dropdown")
        print("   3. Fetch opportunities and see high scores!")
        
    except Exception as e:
        print(f"❌ Error creating profile: {e}")
        import traceback
        traceback.print_exc()
