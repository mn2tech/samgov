"""
Database models and storage layer.
Uses SQLAlchemy for ORM and supports SQLite/Postgres.
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict
from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship

from config import settings
from models import Opportunity, OpportunityScore, CapabilityProfile

logger = logging.getLogger(__name__)

Base = declarative_base()


class OpportunityDB(Base):
    """Database model for opportunities."""
    __tablename__ = "opportunities"
    
    id = Column(Integer, primary_key=True, index=True)
    notice_id = Column(String, unique=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    agency = Column(String, index=True)
    sub_agency = Column(String)
    naics = Column(JSON)  # Store as JSON array
    psc = Column(String)
    set_aside = Column(String)
    contract_type = Column(String)
    response_type = Column(String)
    due_date = Column(DateTime)
    place_of_performance = Column(String)
    posted_date = Column(DateTime)
    url = Column(String)
    
    # AI Classification fields
    primary_domain = Column(String)
    secondary_domains = Column(JSON)
    complexity = Column(String)
    project_type = Column(String)
    is_legacy = Column(Boolean)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OpportunityScoreDB(Base):
    """Database model for opportunity scores."""
    __tablename__ = "opportunity_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    notice_id = Column(String, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), index=True)  # Multi-tenant support
    company_name = Column(String, index=True)
    fit_score = Column(Float, index=True)
    
    # Score breakdown
    domain_match = Column(Float)
    naics_match = Column(Float)
    technical_skill_match = Column(Float)
    agency_alignment = Column(Float)
    contract_type_fit = Column(Float)
    strategic_value = Column(Float)
    
    # Recommendation
    recommended_action = Column(String, index=True)
    explanation = Column(Text)
    risk_factors = Column(JSON)
    reasoning = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)


class TenantDB(Base):
    """Database model for tenants (companies/organizations)."""
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    domain = Column(String)  # Email domain for auto-tenant assignment
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserDB(Base):
    """Database model for users."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    google_id = Column(String, unique=True, index=True)  # Google user ID (sub)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), index=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)


class CapabilityProfileDB(Base):
    """Database model for capability profiles."""
    __tablename__ = "capability_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), index=True)  # Multi-tenant support
    company_name = Column(String, index=True)  # No longer unique globally, unique per tenant
    profile_data = Column(JSON)  # Store full profile as JSON
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint per tenant
    __table_args__ = (UniqueConstraint('tenant_id', 'company_name', name='_tenant_company_uc'),)


class Database:
    """Database manager for opportunities and profiles."""
    
    def __init__(self):
        try:
            self.engine = create_engine(
                settings.database_url,
                connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
            )
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            # Create all tables if they don't exist
            Base.metadata.create_all(bind=self.engine)
            logger.info(f"Database initialized: {settings.database_url}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get database session."""
        return self.SessionLocal()
    
    def save_opportunity(self, opportunity: Opportunity) -> OpportunityDB:
        """Save or update opportunity in database."""
        session = self.get_session()
        try:
            db_opp = session.query(OpportunityDB).filter(
                OpportunityDB.notice_id == opportunity.notice_id
            ).first()
            
            if db_opp:
                # Update existing
                db_opp.title = opportunity.title
                db_opp.description = opportunity.description
                db_opp.agency = opportunity.agency
                db_opp.sub_agency = opportunity.sub_agency
                db_opp.naics = opportunity.naics
                db_opp.psc = opportunity.psc
                db_opp.set_aside = opportunity.set_aside
                db_opp.contract_type = opportunity.contract_type
                db_opp.response_type = opportunity.response_type
                db_opp.due_date = opportunity.due_date
                db_opp.place_of_performance = opportunity.place_of_performance
                db_opp.posted_date = opportunity.posted_date
                db_opp.url = opportunity.url
                db_opp.primary_domain = str(opportunity.primary_domain) if opportunity.primary_domain else None
                db_opp.secondary_domains = [str(d) for d in opportunity.secondary_domains] if opportunity.secondary_domains else []
                db_opp.complexity = str(opportunity.complexity) if opportunity.complexity else None
                db_opp.project_type = str(opportunity.project_type) if opportunity.project_type else None
                db_opp.is_legacy = opportunity.is_legacy
                db_opp.updated_at = datetime.utcnow()
            else:
                # Create new
                db_opp = OpportunityDB(
                    notice_id=opportunity.notice_id,
                    title=opportunity.title,
                    description=opportunity.description,
                    agency=opportunity.agency,
                    sub_agency=opportunity.sub_agency,
                    naics=opportunity.naics,
                    psc=opportunity.psc,
                    set_aside=opportunity.set_aside,
                    contract_type=opportunity.contract_type,
                    response_type=opportunity.response_type,
                    due_date=opportunity.due_date,
                    place_of_performance=opportunity.place_of_performance,
                    posted_date=opportunity.posted_date,
                    url=opportunity.url,
                    primary_domain=str(opportunity.primary_domain) if opportunity.primary_domain else None,
                    secondary_domains=[str(d) for d in opportunity.secondary_domains] if opportunity.secondary_domains else [],
                    complexity=str(opportunity.complexity) if opportunity.complexity else None,
                    project_type=str(opportunity.project_type) if opportunity.project_type else None,
                    is_legacy=opportunity.is_legacy
                )
                session.add(db_opp)
            
            session.commit()
            session.refresh(db_opp)
            return db_opp
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving opportunity: {e}")
            raise
        finally:
            session.close()
    
    def get_opportunities(
        self,
        limit: int = 100,
        domain: Optional[str] = None,
        agency: Optional[str] = None
    ) -> List[OpportunityDB]:
        """Get opportunities from database."""
        session = self.get_session()
        try:
            query = session.query(OpportunityDB)
            
            if domain:
                query = query.filter(OpportunityDB.primary_domain == domain)
            
            if agency:
                query = query.filter(OpportunityDB.agency.contains(agency))
            
            return query.order_by(OpportunityDB.due_date.desc()).limit(limit).all()
            
        finally:
            session.close()
    
    def get_unique_agencies(self) -> List[str]:
        """Get list of unique agencies from opportunities in database."""
        session = self.get_session()
        try:
            # Get distinct agencies, excluding None and "Unknown"
            agencies = session.query(OpportunityDB.agency).distinct().filter(
                OpportunityDB.agency.isnot(None),
                OpportunityDB.agency != "Unknown"
            ).order_by(OpportunityDB.agency).all()
            
            # Extract agency names and filter out empty strings
            agency_list = [a[0] for a in agencies if a[0] and a[0].strip()]
            return sorted(agency_list)
        finally:
            session.close()
    
    def save_score(self, score: OpportunityScore, tenant_id: Optional[int] = None) -> OpportunityScoreDB:
        """Save opportunity score."""
        session = self.get_session()
        try:
            db_score = OpportunityScoreDB(
                notice_id=score.opportunity.notice_id,
                tenant_id=tenant_id,
                company_name=score.capability_profile.company_name,
                fit_score=score.fit_score,
                domain_match=score.breakdown.domain_match,
                naics_match=score.breakdown.naics_match,
                technical_skill_match=score.breakdown.technical_skill_match,
                agency_alignment=score.breakdown.agency_alignment,
                contract_type_fit=score.breakdown.contract_type_fit,
                strategic_value=score.breakdown.strategic_value,
                recommended_action=str(score.recommended_action),
                explanation=score.explanation,
                risk_factors=score.risk_factors,
                reasoning=score.reasoning
            )
            session.add(db_score)
            session.commit()
            session.refresh(db_score)
            return db_score
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving score: {e}")
            raise
        finally:
            session.close()
    
    def save_profile(self, profile: CapabilityProfile, tenant_id: Optional[int] = None) -> CapabilityProfileDB:
        """Save or update capability profile for a tenant."""
        session = self.get_session()
        try:
            # Query by company_name AND tenant_id to ensure tenant isolation
            query = session.query(CapabilityProfileDB).filter(
                CapabilityProfileDB.company_name == profile.company_name
            )
            
            if tenant_id is not None:
                query = query.filter(CapabilityProfileDB.tenant_id == tenant_id)
            
            db_profile = query.first()
            
            if db_profile:
                # Update existing profile
                db_profile.profile_data = profile.dict()
                if tenant_id is not None:
                    db_profile.tenant_id = tenant_id
                db_profile.updated_at = datetime.utcnow()
            else:
                # Create new profile
                if tenant_id is None:
                    raise ValueError("tenant_id is required when creating a new profile")
                db_profile = CapabilityProfileDB(
                    company_name=profile.company_name,
                    profile_data=profile.dict(),
                    tenant_id=tenant_id
                )
                session.add(db_profile)
            
            session.commit()
            session.refresh(db_profile)
            return db_profile
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving profile: {e}")
            raise
        finally:
            session.close()
    
    def get_profile(self, company_name: str, tenant_id: Optional[int] = None) -> Optional[CapabilityProfile]:
        """Get capability profile by company name for a tenant."""
        session = self.get_session()
        try:
            query = session.query(CapabilityProfileDB).filter(
                CapabilityProfileDB.company_name == company_name
            )
            if tenant_id:
                query = query.filter(CapabilityProfileDB.tenant_id == tenant_id)
            
            db_profile = query.first()
            
            if db_profile:
                profile_data = db_profile.profile_data.copy()
                # Ensure offices field exists for backward compatibility
                if "offices" not in profile_data:
                    profile_data["offices"] = []
                return CapabilityProfile(**profile_data)
            return None
            
        finally:
            session.close()
    
    def list_all_profiles(self, tenant_id: Optional[int] = None) -> List[str]:
        """Get list of all saved company profile names for a tenant."""
        session = self.get_session()
        try:
            query = session.query(CapabilityProfileDB.company_name)
            if tenant_id:
                query = query.filter(CapabilityProfileDB.tenant_id == tenant_id)
            profiles = query.all()
            return [name[0] for name in profiles] if profiles else []
        finally:
            session.close()
    
    def get_or_create_tenant_by_email(self, email: str):
        """Get or create tenant based on email domain."""
        session = self.get_session()
        try:
            domain = email.split('@')[1] if '@' in email else 'default'
            
            # Try to find tenant by domain
            tenant = session.query(TenantDB).filter(TenantDB.domain == domain).first()
            
            if not tenant:
                # Create new tenant
                tenant = TenantDB(
                    name=domain.split('.')[0].title() + " Organization",
                    domain=domain
                )
                session.add(tenant)
                session.commit()
                session.refresh(tenant)
                logger.info(f"Created new tenant: {tenant.name} (domain: {domain})")
            
            return tenant
        except Exception as e:
            session.rollback()
            logger.error(f"Error getting/creating tenant: {e}")
            raise
        finally:
            session.close()
    
    def get_or_create_user(self, user_info: Dict, tenant_id: int):
        """Get or create user from Google auth info."""
        session = self.get_session()
        try:
            google_id = user_info.get('sub')
            email = user_info.get('email')
            
            # Try to find existing user
            user = session.query(UserDB).filter(
                (UserDB.google_id == google_id) | (UserDB.email == email)
            ).first()
            
            if user:
                # Update last login
                user.last_login = datetime.utcnow()
                # Update tenant if changed
                if user.tenant_id != tenant_id:
                    user.tenant_id = tenant_id
                session.commit()
                session.refresh(user)
            else:
                # Create new user
                user = UserDB(
                    email=email,
                    name=user_info.get('name', email.split('@')[0]),
                    google_id=google_id,
                    tenant_id=tenant_id,
                    last_login=datetime.utcnow()
                )
                session.add(user)
                session.commit()
                session.refresh(user)
                logger.info(f"Created new user: {email}")
            
            return user
        except Exception as e:
            session.rollback()
            logger.error(f"Error getting/creating user: {e}")
            raise
        finally:
            session.close()


# Global database instance - use property to initialize lazily
class DatabaseManager:
    """Lazy database manager to avoid import-time initialization errors."""
    _instance = None
    
    def __getattr__(self, name):
        if self._instance is None:
            self._instance = Database()
        return getattr(self._instance, name)

# For backward compatibility - this will initialize on first access
db = DatabaseManager()
