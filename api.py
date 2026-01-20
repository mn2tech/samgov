"""
FastAPI backend for AI Contract Finder.
Optional REST API for programmatic access and future multi-tenant SaaS.
"""
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import asyncio
import logging

from config import settings
from sam_ingestion import SAMIngestion
from ai_classifier import AIClassifier
from ai_scoring import AIScoringEngine
from profile_manager import profile_manager
from models import Opportunity, CapabilityProfile, OpportunityScore
from database import db

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-Powered IT Contract Finder API"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
ingestion = SAMIngestion()
classifier = AIClassifier()
scorer = AIScoringEngine()


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    await ingestion.close()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/opportunities/fetch", response_model=List[Opportunity])
async def fetch_opportunities(
    days_ahead: int = 30,
    naics: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None,
    limit: int = 50
):
    """
    Fetch and classify opportunities from SAM.gov.
    
    Args:
        days_ahead: Number of days ahead to search
        naics: Optional list of NAICS codes
        keywords: Optional list of keywords
        limit: Maximum number of results
    """
    try:
        opportunities = await ingestion.get_opportunities(
            days_ahead=days_ahead,
            naics=naics,
            keywords=keywords,
            limit=limit
        )
        
        # Classify opportunities
        opportunities = classifier.classify_batch(opportunities)
        
        # Save to database
        for opp in opportunities:
            db.save_opportunity(opp)
        
        return opportunities
        
    except Exception as e:
        logger.error(f"Error fetching opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/opportunities/score", response_model=List[OpportunityScore])
async def score_opportunities(
    opportunities: List[Opportunity],
    profile: CapabilityProfile
):
    """
    Score opportunities against a capability profile.
    
    Args:
        opportunities: List of opportunities to score
        profile: Capability profile to match against
    """
    try:
        scores = scorer.score_batch(opportunities, profile)
        
        # Save scores to database
        for score in scores:
            db.save_score(score)
        
        return scores
        
    except Exception as e:
        logger.error(f"Error scoring opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/opportunities/fetch-and-score", response_model=List[OpportunityScore])
async def fetch_and_score(
    profile: CapabilityProfile,
    days_ahead: int = 30,
    naics: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None,
    limit: int = 50
):
    """
    Fetch, classify, and score opportunities in one operation.
    
    Args:
        profile: Capability profile to match against
        days_ahead: Number of days ahead to search
        naics: Optional list of NAICS codes
        keywords: Optional list of keywords
        limit: Maximum number of results
    """
    try:
        # Fetch and classify
        opportunities = await ingestion.get_opportunities(
            days_ahead=days_ahead,
            naics=naics,
            keywords=keywords,
            limit=limit
        )
        
        opportunities = classifier.classify_batch(opportunities)
        
        # Save opportunities
        for opp in opportunities:
            db.save_opportunity(opp)
        
        # Score
        scores = scorer.score_batch(opportunities, profile)
        
        # Save scores
        for score in scores:
            db.save_score(score)
        
        return scores
        
    except Exception as e:
        logger.error(f"Error in fetch-and-score: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/opportunities", response_model=List[Opportunity])
async def get_opportunities(
    limit: int = 100,
    domain: Optional[str] = None,
    agency: Optional[str] = None
):
    """
    Get opportunities from database.
    
    Args:
        limit: Maximum number of results
        domain: Filter by primary domain
        agency: Filter by agency (partial match)
    """
    try:
        db_opportunities = db.get_opportunities(limit=limit, domain=domain, agency=agency)
        
        # Convert DB models to Pydantic models
        opportunities = []
        for db_opp in db_opportunities:
            opp = Opportunity(
                notice_id=db_opp.notice_id,
                title=db_opp.title,
                description=db_opp.description,
                agency=db_opp.agency,
                sub_agency=db_opp.sub_agency,
                naics=db_opp.naics or [],
                psc=db_opp.psc,
                set_aside=db_opp.set_aside,
                contract_type=db_opp.contract_type,
                response_type=db_opp.response_type,
                due_date=db_opp.due_date,
                place_of_performance=db_opp.place_of_performance,
                posted_date=db_opp.posted_date,
                url=db_opp.url,
                primary_domain=db_opp.primary_domain,
                secondary_domains=db_opp.secondary_domains or [],
                complexity=db_opp.complexity,
                project_type=db_opp.project_type,
                is_legacy=db_opp.is_legacy
            )
            opportunities.append(opp)
        
        return opportunities
        
    except Exception as e:
        logger.error(f"Error getting opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/profiles", response_model=CapabilityProfile)
async def create_profile(
    profile: CapabilityProfile,
    tenant_id: Optional[int] = Query(None, description="Tenant ID for multi-tenant support")
):
    """
    Create or update a capability profile.
    
    Note: For multi-tenant support, tenant_id should be provided as a query parameter.
    """
    try:
        db.save_profile(profile, tenant_id=tenant_id)
        return profile
    except Exception as e:
        logger.error(f"Error creating profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/profiles/{company_name}", response_model=CapabilityProfile)
async def get_profile(company_name: str):
    """Get capability profile by company name."""
    profile = profile_manager.get_profile(company_name)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
