"""
Streamlit UI for AI Contract Finder.
Main application entry point.
"""
import streamlit as st
import pandas as pd
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import json
import io

from config import settings
from sam_ingestion import SAMIngestion
from ai_classifier import AIClassifier
from ai_scoring import AIScoringEngine
from ai_bid_assistant import bid_assistant
from profile_manager import profile_manager, ProfileManager
from models import Opportunity, CapabilityProfile, OpportunityScore, RecommendedAction
from database import db
from auth import check_authentication, get_current_user, get_current_tenant_id, show_login_page, logout

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="AI Contract Finder - SAM.gov",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None
if "opportunities" not in st.session_state:
    st.session_state.opportunities = []
if "scores" not in st.session_state:
    st.session_state.scores = []
if "profile" not in st.session_state:
    st.session_state.profile = None
if "ingestion" not in st.session_state:
    st.session_state.ingestion = None
if "classifier" not in st.session_state:
    st.session_state.classifier = None
if "scorer" not in st.session_state:
    st.session_state.scorer = None
# Feature: Free/Pro plan gating
if "plan" not in st.session_state:
    st.session_state.plan = "Free"  # Default to Free plan
# Feature: Cache explanations per Notice ID to avoid re-running AI
if "explanations_cache" not in st.session_state:
    st.session_state.explanations_cache = {}
# Feature: Track selected notice ID for "Why?" explanation
if "selected_notice_id" not in st.session_state:
    st.session_state.selected_notice_id = None


def init_components():
    """Initialize AI components."""
    if st.session_state.ingestion is None:
        st.session_state.ingestion = SAMIngestion()
    if st.session_state.classifier is None:
        st.session_state.classifier = AIClassifier()
    if st.session_state.scorer is None:
        st.session_state.scorer = AIScoringEngine()


def get_color_for_score(score: float) -> str:
    """Get color for fit score."""
    if score >= 70:
        return "🟢"
    elif score >= 50:
        return "🟡"
    else:
        return "🔴"


def get_color_for_action(action: RecommendedAction) -> str:
    """Get color emoji for recommended action."""
    if action == RecommendedAction.BID:
        return "🟢"
    elif action == RecommendedAction.TEAM_SUB:
        return "🟡"
    else:
        return "🔴"


def _normalize_datetime_for_comparison(dt: datetime, reference: datetime = None) -> datetime:
    """
    Normalize datetime to match timezone awareness of reference.
    
    Args:
        dt: Datetime to normalize
        reference: Reference datetime (defaults to datetime.now())
        
    Returns:
        Normalized datetime
    """
    if reference is None:
        reference = datetime.now()
    
    # If dt is timezone-aware, make reference timezone-aware too
    if dt.tzinfo is not None:
        if reference.tzinfo is None:
            from datetime import timezone
            reference = reference.replace(tzinfo=timezone.utc)
    else:
        # If dt is naive, make sure reference is also naive
        if reference.tzinfo is not None:
            reference = reference.replace(tzinfo=None)
    
    return reference


def is_opportunity_expired(opportunity: Opportunity) -> bool:
    """Check if opportunity deadline has passed."""
    if not opportunity.due_date:
        return False  # Can't determine if no deadline
    
    now = _normalize_datetime_for_comparison(opportunity.due_date)
    return opportunity.due_date < now


def get_expiry_status(opportunity: Opportunity):
    """
    Get expiry status and message for an opportunity.
    
    Returns:
        (is_expired, status_message)
    """
    if not opportunity.due_date:
        return False, "No deadline specified"
    
    now = _normalize_datetime_for_comparison(opportunity.due_date)
    due_date = opportunity.due_date
    
    if due_date < now:
        days_past = (now - due_date).days
        return True, f"⚠️ EXPIRED ({days_past} days ago)"
    else:
        days_remaining = (due_date - now).days
        if days_remaining <= 7:
            return False, f"🔴 URGENT ({days_remaining} days left)"
        elif days_remaining <= 14:
            return False, f"🟡 Soon ({days_remaining} days left)"
        else:
            return False, f"✅ Active ({days_remaining} days left)"


def compute_executive_summary(scores: List[OpportunityScore]) -> Dict:
    """
    Feature: Compute executive summary statistics for scored opportunities.
    
    Returns:
        Dict with counts for BID, TEAM, IGNORE, and urgency metrics
    """
    if not scores:
        return {
            "total": 0,
            "bid_count": 0,
            "team_count": 0,
            "ignore_count": 0,
            "due_soon_count": 0,  # <= 7 days
            "urgent_count": 0  # <= 3 days
        }
    
    bid_count = sum(1 for s in scores if s.recommended_action == RecommendedAction.BID and s.fit_score >= 80)
    team_count = sum(1 for s in scores if s.recommended_action == RecommendedAction.TEAM_SUB and 60 <= s.fit_score < 80)
    ignore_count = sum(1 for s in scores if s.recommended_action == RecommendedAction.IGNORE or s.fit_score < 60)
    
    # Count urgency metrics
    now = datetime.now()
    due_soon_count = 0
    urgent_count = 0
    
    for score in scores:
        if score.opportunity.due_date:
            days_remaining = (score.opportunity.due_date - _normalize_datetime_for_comparison(score.opportunity.due_date)).days
            if days_remaining <= 7:
                due_soon_count += 1
            if days_remaining <= 3:
                urgent_count += 1
    
    return {
        "total": len(scores),
        "bid_count": bid_count,
        "team_count": team_count,
        "ignore_count": ignore_count,
        "due_soon_count": due_soon_count,
        "urgent_count": urgent_count
    }


def detect_recompete_signal(opportunity: Opportunity) -> str:
    """
    Feature: MVP heuristic to detect recompete/incumbent signals from opportunity text.
    
    Returns:
        "Likely Recompete", "Likely New", or "Unknown"
    """
    # Combine title and description for keyword search
    text_to_search = f"{opportunity.title} {opportunity.description}".lower()
    
    # Recompete keywords
    recompete_keywords = [
        "recompete", "incumbent", "follow-on", "renewal", "bridge",
        "sole source", "option year", "task order extension", "continuation",
        "existing contract", "current contractor"
    ]
    
    # New opportunity keywords
    new_keywords = [
        "new requirement", "new initiative", "greenfield", "new procurement",
        "new acquisition", "first time", "initial award"
    ]
    
    # Check for recompete signals
    if any(keyword in text_to_search for keyword in recompete_keywords):
        return "Likely Recompete"
    
    # Check for new opportunity signals
    if any(keyword in text_to_search for keyword in new_keywords):
        return "Likely New"
    
    return "Unknown"


def get_recompete_emoji(signal: str) -> str:
    """Get emoji for recompete signal."""
    if signal == "Likely Recompete":
        return "🟠"
    elif signal == "Likely New":
        return "🟢"
    else:
        return "⚪"


def generate_why_explanation(score: OpportunityScore, is_pro: bool = False) -> Dict[str, str]:
    """
    Feature: Generate "Why?" explanation for an opportunity score.
    
    Returns:
        Dict with 'bullets' (short summary) and 'full' (detailed explanation)
    """
    notice_id = score.opportunity.notice_id
    
    # Check cache first
    if notice_id in st.session_state.explanations_cache:
        cached = st.session_state.explanations_cache[notice_id]
        if is_pro:
            return cached
        else:
            # Free users get limited version
            return {
                "bullets": cached.get("bullets", "").split("\n")[:2],  # First 2 bullets only
                "full": "Upgrade to Pro to see full reasoning"
            }
    
    # Generate explanation
    breakdown = score.breakdown
    opp = score.opportunity
    
    # Build bullet summary
    bullets = []
    
    # Domain match
    if breakdown.domain_match >= 70:
        bullets.append(f"✅ Domain match: {breakdown.domain_match:.0f}% - Strong alignment")
    elif breakdown.domain_match >= 50:
        bullets.append(f"⚠️ Domain match: {breakdown.domain_match:.0f}% - Moderate alignment")
    else:
        bullets.append(f"❌ Domain match: {breakdown.domain_match:.0f}% - Weak alignment")
    
    # NAICS match
    if breakdown.naics_match >= 70:
        bullets.append(f"✅ NAICS match: {breakdown.naics_match:.0f}% - Excellent code alignment")
    elif breakdown.naics_match >= 50:
        bullets.append(f"⚠️ NAICS match: {breakdown.naics_match:.0f}% - Partial code match")
    else:
        bullets.append(f"❌ NAICS match: {breakdown.naics_match:.0f}% - Limited code match")
    
    # Agency preference
    if breakdown.agency_alignment >= 70:
        bullets.append(f"✅ Agency preference: {breakdown.agency_alignment:.0f}% - Preferred agency")
    elif breakdown.agency_alignment >= 50:
        bullets.append(f"⚠️ Agency preference: {breakdown.agency_alignment:.0f}% - Neutral agency")
    else:
        bullets.append(f"❌ Agency preference: {breakdown.agency_alignment:.0f}% - Not preferred")
    
    # Set-aside/certification (simplified - using contract_type_fit as proxy)
    if breakdown.contract_type_fit >= 70:
        bullets.append(f"✅ Contract type/certification: {breakdown.contract_type_fit:.0f}% - Good fit")
    elif breakdown.contract_type_fit >= 50:
        bullets.append(f"⚠️ Contract type/certification: {breakdown.contract_type_fit:.0f}% - Partial fit")
    else:
        bullets.append(f"❌ Contract type/certification: {breakdown.contract_type_fit:.0f}% - Poor fit")
    
    # Complexity risk
    complexity = opp.complexity or "Unknown"
    if complexity in ["High", "Very High"]:
        bullets.append(f"⚠️ Complexity risk: High - Requires significant expertise")
    elif complexity in ["Medium", "Moderate"]:
        bullets.append(f"ℹ️ Complexity risk: Medium - Moderate challenge")
    else:
        bullets.append(f"✅ Complexity risk: Low - Manageable scope")
    
    # Timing risk
    if opp.due_date:
        now = _normalize_datetime_for_comparison(opp.due_date)
        days_remaining = (opp.due_date - now).days
        if days_remaining <= 3:
            bullets.append(f"🔴 Timing risk: URGENT - Only {days_remaining} days remaining")
        elif days_remaining <= 7:
            bullets.append(f"🟡 Timing risk: Due soon - {days_remaining} days remaining")
        else:
            bullets.append(f"✅ Timing risk: Adequate time - {days_remaining} days remaining")
    else:
        bullets.append(f"ℹ️ Timing risk: No deadline specified")
    
    bullets_text = "\n".join(bullets)
    
    # Use existing explanation/reasoning for full text
    full_explanation = score.explanation
    if score.reasoning:
        full_explanation += f"\n\nDetailed Reasoning:\n{score.reasoning}"
    
    result = {
        "bullets": bullets_text,
        "full": full_explanation
    }
    
    # Cache the result
    st.session_state.explanations_cache[notice_id] = result
    
    # Return limited version for free users
    if not is_pro:
        return {
            "bullets": "\n".join(bullets[:2]),  # First 2 bullets only
            "full": "Upgrade to Pro to see full reasoning"
        }
    
    return result


async def fetch_and_classify_opportunities(
    days_ahead: int = 30,
    naics: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None,
    status_text=None,
    progress_bar=None,
    quick_test: bool = False
) -> List[Opportunity]:
    """Fetch and classify opportunities."""
    ingestion = st.session_state.ingestion
    classifier = st.session_state.classifier
    
    # Quick test mode: limit to 20 opportunities and use rule-based only
    # Regular mode: limit to 50 for faster processing (reduced from 100)
    limit = 20 if quick_test else 50
    
    # Fetch opportunities
    opportunities = await ingestion.get_opportunities(
        days_ahead=days_ahead,
        naics=naics,
        keywords=keywords,
        limit=limit
    )
    
    # Limit to 20 for quick test mode
    if quick_test and len(opportunities) > 20:
        opportunities = opportunities[:20]
    
    # Classify opportunities with progress tracking
    if opportunities:
        if status_text:
            if quick_test:
                status_text.text(f"⚡ Quick Test: Classifying {len(opportunities)} opportunities (rule-based only)...")
            else:
                status_text.text(f"Step 2/3: Classifying {len(opportunities)} opportunities...")
        if progress_bar:
            progress_bar.progress(40)
        
        # Quick test mode: always use rule-based (fast, no AI)
        if quick_test or not settings.openai_api_key:
            # Fast rule-based classification
            opportunities = classifier.classify_batch(opportunities)
            if progress_bar:
                progress_bar.progress(80)
        else:
            # AI classification with progress - limit to first 20 for speed
            # Rest will use rule-based classification (much faster)
            max_ai_classify = 20  # Reduced from 50 to 20 for faster processing
            classified = []
            total = len(opportunities)
            
            for i, opp in enumerate(opportunities):
                if i < max_ai_classify:
                    # Use AI for first batch
                    classified.append(classifier.classify_opportunity(opp))
                    # Update progress every 3 opportunities for better feedback
                    if (i + 1) % 3 == 0 or (i + 1) == max_ai_classify:
                        if progress_bar:
                            progress = 40 + int((i + 1) / max_ai_classify * 35)  # 40-75% for AI classification
                            progress_bar.progress(progress)
                        if status_text:
                            status_text.text(f"Step 2/3: AI classifying {i + 1}/{min(max_ai_classify, total)} opportunities...")
                else:
                    # Use fast rule-based for the rest
                    classified.append(classifier._rule_based_classify(opp))
                    if (i + 1) % 20 == 0 or (i + 1) == total:
                        if progress_bar:
                            progress = 75 + int((i + 1 - max_ai_classify) / (total - max_ai_classify) * 10) if total > max_ai_classify else 85
                            progress_bar.progress(progress)
                        if status_text:
                            status_text.text(f"Step 2/3: Processing {i + 1}/{total} opportunities...")
            
            opportunities = classified
    
    # Save to database
    for opp in opportunities:
        db.save_opportunity(opp)
    
    return opportunities


def score_opportunities(
    opportunities: List[Opportunity],
    profile: CapabilityProfile
) -> List[OpportunityScore]:
    """Score opportunities against profile."""
    scorer = st.session_state.scorer
    
    # Show progress for scoring
    total = len(opportunities)
    max_ai_score = 20
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        scores = []
        for i, opp in enumerate(opportunities):
            if i < max_ai_score:
                # AI scoring for first 20
                status_text.text(f"📊 Scoring {i + 1}/{min(max_ai_score, total)} opportunities with AI...")
                scores.append(scorer.score_opportunity(opp, profile))
                progress_bar.progress((i + 1) / total)
            else:
                # Fast rule-based for the rest
                if i == max_ai_score:
                    status_text.text(f"📊 Fast scoring remaining {total - max_ai_score} opportunities...")
                scores.append(scorer._rule_based_score(opp, profile))
                if (i + 1) % 10 == 0 or (i + 1) == total:
                    progress_bar.progress((i + 1) / total)
        
        status_text.text(f"✅ Scored {total} opportunities!")
        progress_bar.progress(1.0)
        
    finally:
        # Save scores to database with tenant_id
        tenant_id = get_current_tenant_id()
        for score in scores:
            db.save_score(score, tenant_id=tenant_id)
        
        # Clear progress indicators after a short delay
        import time
        time.sleep(0.5)
        progress_bar.empty()
        status_text.empty()
    
    return scores


def main():
    """Main application."""
    # Check authentication
    if not check_authentication():
        show_login_page()
        return
    
    # Get current user and tenant
    try:
        user = get_current_user()
        tenant_id = get_current_tenant_id()
    except Exception as e:
        logger.error(f"Error getting user/tenant: {e}")
        st.error(f"❌ Error loading user session: {str(e)}")
        st.info("💡 Please try logging out and logging back in.")
        return
    
    # Show user info and logout in sidebar
    with st.sidebar:
        if user:
            st.markdown(f"**👤 {user.get('name', user.get('email'))}**")
            st.markdown(f"**🏢 {user.get('tenant_name', 'Organization')}**")
            if st.button("🚪 Logout", key="logout_btn"):
                logout()
                return
        st.markdown("---")
        
        # Feature: Free/Pro plan toggle (simple demo, no real billing)
        st.markdown("### 💳 Account Plan")
        plan_options = ["Free", "Pro (demo)"]
        current_plan = st.radio(
            "Select plan",
            options=plan_options,
            index=0 if st.session_state.plan == "Free" else 1,
            key="plan_selector",
            help="Free: Limited features. Pro: Full access to all features."
        )
        st.session_state.plan = current_plan
        if current_plan == "Pro (demo)":
            st.success("✅ Pro features enabled")
        else:
            st.info("💡 Upgrade to Pro for full explanations, bid strategies, and detailed insights")
        st.markdown("---")
    
    st.title("🏛️ AI-Powered IT Contract Finder")
    st.markdown("**Find and score federal IT, AI, Data, Cloud, and Cyber opportunities from SAM.gov**")
    
    init_components()
    
    # Sidebar - Capability Profile
    with st.sidebar:
        st.header("📋 Company Capability Profile")
        
        # Get list of saved profiles for current tenant only
        saved_profiles = profile_manager.list_all_profiles(tenant_id=tenant_id)
        
        # New user onboarding - show welcome message if no profiles
        if not saved_profiles:
            st.info("👋 **Welcome!** Create your first company profile to get started.")
            st.markdown("""
            **Get started in 3 steps:**
            1. Enter your company name below
            2. Select your core capabilities
            3. Add technical skills and NAICS codes
            """)
        
        # Profile selection: dropdown or new profile
        if saved_profiles:
            profile_options = ["-- Create New Profile --"] + saved_profiles
            selected_option = st.selectbox(
                "Select Company Profile",
                options=profile_options,
                index=0 if not st.session_state.profile else (
                    saved_profiles.index(st.session_state.profile.company_name) + 1 
                    if st.session_state.profile and st.session_state.profile.company_name in saved_profiles 
                    else 0
                ),
                key="profile_selector"
            )
            
            if selected_option == "-- Create New Profile --":
                profile_name = st.text_input(
                    "New Company Name",
                    value="",
                    key="new_profile_name",
                    help="Enter a new company name to create a profile"
                )
                if profile_name:
                    # Check if profile already exists for this tenant
                    existing = profile_manager.get_profile(profile_name, tenant_id=tenant_id)
                    if existing:
                        st.warning(f"Profile '{profile_name}' already exists. Select it from dropdown or use a different name.")
                        profile_name = None
            else:
                profile_name = selected_option
                # Auto-load selected profile
                if not st.session_state.profile or st.session_state.profile.company_name != profile_name:
                    profile = profile_manager.get_profile(profile_name, tenant_id=tenant_id)
                    if profile:
                        st.session_state.profile = profile
                        st.success(f"✅ Loaded: {profile_name}")
        else:
            # No saved profiles yet - show prominent onboarding for new users
            st.markdown("### 🚀 Create Your First Company Profile")
            st.markdown("Enter your company name to start matching opportunities:")
            
            profile_name = st.text_input(
                "Company Name",
                value="",
                key="profile_name",
                help="Enter your company name (e.g., 'NM2TECH LLC', 'Acme Corp')",
                placeholder="e.g., NM2TECH LLC"
            )
            
            if profile_name:
                st.info(f"💡 Next: Fill in the profile details below for **{profile_name}**")
        
        # Manual load button (for edge cases)
        if saved_profiles and profile_name and profile_name != "-- Create New Profile --":
            if st.button("🔄 Reload Profile", key="reload_profile"):
                profile = profile_manager.get_profile(profile_name, tenant_id=tenant_id)
                if profile:
                    st.session_state.profile = profile
                    st.success(f"Reloaded profile for {profile_name}")
                else:
                    st.warning(f"No profile found for {profile_name}.")
        
        # Quick create simple sample profile
        st.markdown("---")
        with st.expander("🚀 Quick Start: Create Sample IT Profile", expanded=False):
            st.markdown("""
            **Create a simple sample IT profile** with limited selections for testing:
            - 8 technical skills
            - 3 NAICS codes  
            - 3 federal agencies
            """)
            if st.button("✨ Create Sample IT Profile", key="create_sample_profile"):
                try:
                    # Replace old comprehensive profile if it exists with simple version
                    old_comprehensive = profile_manager.get_profile("Comprehensive IT Solutions LLC", tenant_id=tenant_id)
                    if old_comprehensive:
                        # Update the comprehensive profile to have simple limited data
                        profile = profile_manager.create_profile(
                            company_name="Comprehensive IT Solutions LLC",
                            core_domains=[
                                "AI/ML",
                                "Data Analytics/Engineering",
                                "Cloud Architecture & Migration"
                            ],
                            technical_skills=[
                                "Python",
                                "SQL",
                                "AWS",
                                "Azure",
                                "Kubernetes",
                                "Terraform",
                                "Docker",
                                "Machine Learning"
                            ],
                            naics=[
                                "541511",
                                "541512",
                                "541519"
                            ],
                            preferred_agencies=[
                                "DEPT OF DEFENSE",
                                "DEPT OF HOMELAND SECURITY",
                                "GENERAL SERVICES ADMINISTRATION"
                            ],
                            certifications=[
                                "SDVOSB"
                            ],
                            role_preference="Either",
                            tenant_id=tenant_id
                        )
                        st.session_state.profile = profile
                        st.success("✅ Updated 'Comprehensive IT Solutions LLC' profile with limited selections!")
                        st.rerun()
                    else:
                        # Check if simple sample already exists
                        existing = profile_manager.get_profile("Sample IT Company", tenant_id=tenant_id)
                        if existing:
                            # Update existing to ensure it has limited data
                            profile = profile_manager.create_profile(
                                company_name="Sample IT Company",
                                core_domains=[
                                    "AI/ML",
                                    "Data Analytics/Engineering",
                                    "Cloud Architecture & Migration"
                                ],
                                technical_skills=[
                                    "Python",
                                    "SQL",
                                    "AWS",
                                    "Azure",
                                    "Kubernetes",
                                    "Terraform",
                                    "Docker",
                                    "Machine Learning"
                                ],
                                naics=[
                                    "541511",
                                    "541512",
                                    "541519"
                                ],
                                preferred_agencies=[
                                    "DEPT OF DEFENSE",
                                    "DEPT OF HOMELAND SECURITY",
                                    "GENERAL SERVICES ADMINISTRATION"
                                ],
                                certifications=[
                                    "SDVOSB"
                                ],
                                role_preference="Either",
                                tenant_id=tenant_id
                            )
                            st.session_state.profile = profile
                            st.success("✅ Updated 'Sample IT Company' profile with limited selections!")
                            st.rerun()
                        else:
                            # Create simple sample profile with limited selections
                            profile = profile_manager.create_profile(
                                company_name="Sample IT Company",
                                core_domains=[
                                    "AI/ML",
                                    "Data Analytics/Engineering",
                                    "Cloud Architecture & Migration"
                                ],
                                technical_skills=[
                                    "Python",
                                    "SQL",
                                    "AWS",
                                    "Azure",
                                    "Kubernetes",
                                    "Terraform",
                                    "Docker",
                                    "Machine Learning"
                                ],
                                naics=[
                                    "541511",
                                    "541512",
                                    "541519"
                                ],
                                preferred_agencies=[
                                    "DEPT OF DEFENSE",
                                    "DEPT OF HOMELAND SECURITY",
                                    "GENERAL SERVICES ADMINISTRATION"
                                ],
                                certifications=[
                                    "SDVOSB"
                                ],
                                role_preference="Either",
                                tenant_id=tenant_id
                            )
                            st.session_state.profile = profile
                            st.success("✅ Created 'Sample IT Company' profile! Select it from the dropdown above.")
                            st.rerun()
                except Exception as e:
                    st.error(f"Error creating profile: {str(e)}")
                    logger.error(f"Error creating sample profile: {e}")
        
        # Create/Edit Profile
        # Only show if we have a profile name (either selected or entered)
        profile_name_for_form = None
        if saved_profiles:
            if 'profile_selector' in st.session_state:
                selected = st.session_state.profile_selector
                if selected != "-- Create New Profile --":
                    profile_name_for_form = selected
                elif 'new_profile_name' in st.session_state and st.session_state.new_profile_name:
                    profile_name_for_form = st.session_state.new_profile_name
        else:
            if 'profile_name' in st.session_state and st.session_state.profile_name:
                profile_name_for_form = st.session_state.profile_name
        
        # Show profile creation form
        # For new users (no profiles), always show expanded
        # For existing users, show expanded only if no profile is loaded
        should_expand = not st.session_state.profile
        if not saved_profiles:
            should_expand = True  # Always expand for new users
        
        # Show profile form for new users or when profile name is entered
        if profile_name_for_form or (not saved_profiles and not st.session_state.profile):
            expander_title = "🚀 Create Your Company Profile" if not saved_profiles else "Create/Edit Profile"
            with st.expander(expander_title, expanded=should_expand):
                # For new users without a profile name, show company name input first
                if not saved_profiles and not profile_name_for_form:
                    profile_name_input = st.text_input(
                        "Company Name *",
                        value="",
                        key="new_user_company_name",
                        help="Enter your company name to create a profile",
                        placeholder="e.g., NM2TECH LLC"
                    )
                    if not profile_name_input:
                        st.stop()  # Don't show rest of form until company name is entered
                    profile_name_for_form = profile_name_input
                
                # Pre-fill from loaded profile if available
                current_profile = st.session_state.profile
                default_domains = current_profile.core_domains if current_profile else ["AI/ML", "Data Analytics/Engineering", "Cloud Architecture & Migration", 
                            "DevSecOps/Automation", "Cybersecurity/Zero Trust"]
                default_skills = ", ".join(current_profile.technical_skills) if current_profile and current_profile.technical_skills else "Python, SAS, SQL, AWS, Azure, Kubernetes, Terraform, LLMs"
                default_naics = ", ".join(current_profile.naics) if current_profile and current_profile.naics else "541511, 541512, 541519"
                default_agencies = ", ".join(current_profile.preferred_agencies) if current_profile and current_profile.preferred_agencies else "DoD, Air Force, DHS"
                default_certs = ", ".join(current_profile.certifications) if current_profile and current_profile.certifications else "SDVOSB"
                # Handle offices field - may not exist in older profiles
                default_offices = ""
                if current_profile:
                    offices = getattr(current_profile, 'offices', None)
                    if offices:
                        default_offices = ", ".join(offices) if isinstance(offices, list) else str(offices)
                default_role_idx = ["Prime", "Subcontractor", "Either"].index(current_profile.role_preference) if current_profile and current_profile.role_preference in ["Prime", "Subcontractor", "Either"] else 2
                
                core_domains = st.multiselect(
                    "Core Domains",
                    options=["AI/ML", "Data Analytics/Engineering", "Cloud Architecture & Migration", 
                            "DevSecOps/Automation", "Cybersecurity/Zero Trust",
                            "IT Modernization", "Software Engineering", "IT Operations"],
                    default=default_domains,
                    key="core_domains"
                )
                
                technical_skills = st.text_area(
                    "Technical Skills (comma-separated)",
                    value=default_skills,
                    key="technical_skills"
                )
                
                naics = st.text_area(
                    "NAICS Codes (comma-separated)",
                    value=default_naics,
                    key="naics"
                )
                
                preferred_agencies = st.text_area(
                    "Preferred Agencies (comma-separated)",
                    value=default_agencies,
                    key="preferred_agencies"
                )
                
                certifications = st.text_area(
                    "Certifications (comma-separated)",
                    value=default_certs,
                    key="certifications"
                )
                
                offices = st.text_area(
                    "Office Locations (comma-separated)",
                    value=default_offices,
                    help="Enter office locations (e.g., 'Washington, DC', 'Arlington, VA', 'Remote')",
                    key="offices"
                )
                
                role_preference = st.selectbox(
                    "Role Preference",
                    options=["Prime", "Subcontractor", "Either"],
                    index=default_role_idx,
                    key="role_preference"
                )
                
                if st.button("💾 Save Profile", key="save_profile"):
                    if not profile_name_for_form:
                        st.error("Please enter a company name first.")
                    elif not core_domains:
                        st.error("⚠️ Please select at least one Core Domain. This is required for accurate opportunity matching.")
                    else:
                        profile = profile_manager.create_profile(
                            company_name=profile_name_for_form,
                            core_domains=core_domains,
                            technical_skills=[s.strip() for s in technical_skills.split(",") if s.strip()],
                            naics=[n.strip() for n in naics.split(",") if n.strip()],
                            preferred_agencies=[a.strip() for a in preferred_agencies.split(",") if a.strip()],
                            certifications=[c.strip() for c in certifications.split(",") if c.strip()],
                            offices=[o.strip() for o in offices.split(",") if o.strip()] if offices else [],
                            role_preference=role_preference,
                            tenant_id=tenant_id
                        )
                        st.session_state.profile = profile
                        st.success(f"✅ Profile saved for {profile_name_for_form}!")
                        st.rerun()  # Refresh to update dropdown
        
        # Display current profile
        if st.session_state.profile:
            st.markdown("### Current Profile")
            profile = st.session_state.profile
            # Display profile info in a more readable format
            st.markdown(f"**Company:** {profile.company_name}")
            if profile.core_domains:
                st.markdown(f"**Core Domains:** {', '.join(profile.core_domains)}")
            else:
                st.warning("⚠️ No core domains set. Please edit the profile to add core domains.")
            if profile.technical_skills:
                st.markdown(f"**Technical Skills:** {', '.join(profile.technical_skills[:10])}{'...' if len(profile.technical_skills) > 10 else ''}")
            if profile.naics:
                st.markdown(f"**NAICS Codes:** {', '.join(profile.naics)}")
            if profile.preferred_agencies:
                st.markdown(f"**Preferred Agencies:** {', '.join(profile.preferred_agencies)}")
            if profile.certifications:
                st.markdown(f"**Certifications:** {', '.join(profile.certifications)}")
            if profile.offices:
                st.markdown(f"**Offices:** {', '.join(profile.offices)}")
            st.markdown(f"**Role Preference:** {profile.role_preference}")
            
            # Show full JSON in expander for debugging
            with st.expander("View Full Profile (JSON)"):
                st.json(profile.dict())
    
    # Main content area
    if not st.session_state.profile:
        # Enhanced onboarding for new users
        if not saved_profiles:
            st.info("""
            ## 👋 Welcome to AI Contract Finder!
            
            **Get started by creating your company profile:**
            1. **Enter your company name** in the sidebar
            2. **Select your core capabilities** (AI/ML, Data, Cloud, etc.)
            3. **Add technical skills** (Python, AWS, etc.)
            4. **Add NAICS codes** (541511, 541512, etc.)
            5. **Click "Save Profile"**
            
            Once your profile is created, you can:
            - Fetch opportunities from SAM.gov
            - Get AI-powered fit scores
            - Receive BID/TEAM/IGNORE recommendations
            - Use AI Bid Assistant for proposal help
            """)
        else:
            st.warning("⚠️ Please create or load a capability profile in the sidebar to begin.")
            st.info("💡 Use the 'Create/Edit Profile' section in the sidebar to set up your company profile.")
        return
    
    # Search and Filter Panel
    st.header("🔍 Search & Filter Opportunities")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        days_ahead = st.selectbox(
            "Days Ahead",
            options=[7, 14, 30, 60, 90],
            index=2,
            key="days_ahead"
        )
    
    with col2:
        domain_filter = st.selectbox(
            "Filter by Domain",
            options=["All", "AI", "Data", "Cloud", "Cybersecurity", "IT Operations", 
                    "Software Engineering", "Modernization"],
            key="domain_filter"
        )
    
    with col3:
        # Get unique agencies from database
        from database import db
        unique_agencies = db.get_unique_agencies()
        agency_options = ["All"] + unique_agencies if unique_agencies else ["All"]
        
        agency_filter = st.selectbox(
            "Filter by Agency",
            options=agency_options,
            index=0,
            key="agency_filter",
            help="Select an agency to filter opportunities" if unique_agencies else "No agencies available. Fetch opportunities first."
        )
    
    # Quick Test Mode option - make it more prominent
    col_fetch1, col_fetch2 = st.columns([3, 1])
    with col_fetch1:
        quick_test_mode = st.checkbox(
            "⚡ Quick Test Mode (Recommended - Fast, No AI, 20 opportunities)",
            value=False,
            key="quick_test_mode",
            help="Use rule-based classification only. Much faster (seconds vs minutes). Limits to 20 opportunities. Perfect for testing!"
        )
        if not quick_test_mode:
            st.info("💡 **Tip:** Enable Quick Test Mode for faster results (no AI classification). AI mode classifies 20 opportunities with AI, which takes longer.")
    
    # Fetch opportunities button
    if st.button("🔍 Fetch Opportunities from SAM.gov", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            if quick_test_mode:
                status_text.text("⚡ Quick Test Mode: Fetching sample opportunities...")
            else:
                status_text.text("Step 1/3: Fetching opportunities from SAM.gov...")
            progress_bar.progress(20)
            
            # Add timeout wrapper
            import asyncio
            
            # Create async function with timeout
            async def fetch_with_timeout():
                return await asyncio.wait_for(
                    fetch_and_classify_opportunities(
                        days_ahead=days_ahead,
                        status_text=status_text,
                        progress_bar=progress_bar,
                        quick_test=quick_test_mode
                    ),
                    timeout=120.0  # 2 minute timeout
                )
            
            try:
                opportunities = asyncio.run(fetch_with_timeout())
            except asyncio.TimeoutError:
                st.error("⏱️ Request timed out. The SAM.gov API may be slow. Try reducing 'Days Ahead' or try again later.")
                return
            
            progress_bar.progress(85)
            status_text.text("Step 3/3: Saving opportunities to database...")
            
            st.session_state.opportunities = opportunities
            
            progress_bar.progress(100)
            status_text.text("Step 3/3: Complete!")
            
            # Check if any are mock opportunities
            mock_count = sum(1 for opp in opportunities if opp.notice_id.startswith("MOCK-"))
            if quick_test_mode:
                st.success(f"⚡ **Quick Test Mode:** Fetched {len(opportunities)} opportunities using fast rule-based classification (no AI). Perfect for testing!")
            elif mock_count > 0:
                st.warning(f"⚠️ **Using Mock Data:** {mock_count} of {len(opportunities)} opportunities are sample/test data. To get real opportunities, ensure your SAM.gov API key is configured in Streamlit Cloud secrets.")
            else:
                st.success(f"✅ Fetched {len(opportunities)} real opportunities from SAM.gov")
            
            progress_bar.empty()
            status_text.empty()
            
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            # Filter out description endpoint errors (they're expected and handled)
            error_msg = str(e)
            if "API_KEY_INVALID" not in error_msg and "noticedesc" not in error_msg.lower():
                st.error(f"Error fetching opportunities: {e}")
                logger.error(f"Error: {e}")
            else:
                # Description endpoint errors are expected - just log, don't show to user
                logger.debug(f"Description endpoint error (expected): {e}")
                # Still show success if we got opportunities
                if st.session_state.opportunities:
                    st.success(f"✅ Fetched {len(st.session_state.opportunities)} opportunities (some descriptions may be unavailable)")
    
    # Score opportunities button
    if st.session_state.opportunities and st.button("📊 Score Opportunities", type="primary"):
        scores = score_opportunities(
            st.session_state.opportunities,
            st.session_state.profile
        )
        st.session_state.scores = scores
        st.success(f"✅ Scored {len(scores)} opportunities")
    
    # Display opportunities
    if st.session_state.scores:
        st.header("📊 Ranked Opportunities")
        
        # Feature: Executive Summary Bar
        summary = compute_executive_summary(st.session_state.scores)
        if summary["total"] > 0:
            col_sum1, col_sum2, col_sum3 = st.columns(3)
            with col_sum1:
                st.markdown(f"""
                **Out of {summary['total']} opportunities:**
                - 🟢 {summary['bid_count']} BID (≥80)
                - 🟡 {summary['team_count']} TEAM (60-79)
                - 🔴 {summary['ignore_count']} IGNORE (<60)
                """)
            with col_sum2:
                st.metric("Top Due Soon", f"{summary['due_soon_count']}", help="Opportunities with ≤7 days remaining")
            with col_sum3:
                st.metric("Top Urgent", f"{summary['urgent_count']}", help="Opportunities with ≤3 days remaining")
            st.markdown("---")
        
        # Filter options
        col_filter1, col_filter2 = st.columns([3, 1])
        with col_filter1:
            show_expired = st.checkbox(
                "Show Expired Opportunities",
                value=False,
                key="show_expired",
                help="Include opportunities with passed deadlines"
            )
        
        # Filter scores
        filtered_scores = st.session_state.scores
        
        # Filter out expired opportunities by default
        if not show_expired:
            filtered_scores = [
                s for s in filtered_scores
                if not is_opportunity_expired(s.opportunity)
            ]
        
        if domain_filter != "All":
            filtered_scores = [
                s for s in filtered_scores
                if s.opportunity.primary_domain and 
                domain_filter.lower() in str(s.opportunity.primary_domain).lower()
            ]
        
        if agency_filter and agency_filter != "All":
            filtered_scores = [
                s for s in filtered_scores
                if s.opportunity.agency and 
                agency_filter.lower() in s.opportunity.agency.lower()
            ]
        
        # Show warning if expired opportunities were filtered
        expired_count = len([s for s in st.session_state.scores if is_opportunity_expired(s.opportunity)])
        if expired_count > 0 and not show_expired:
            st.info(f"ℹ️ {expired_count} expired opportunity(ies) hidden. Check 'Show Expired Opportunities' to view them.")
        
        # Sort by fit score
        filtered_scores.sort(key=lambda x: x.fit_score, reverse=True)
        
        # Feature: Check if user is on Pro plan
        is_pro = st.session_state.plan == "Pro (demo)"
        
        # Create DataFrame for display with new features
        df_data = []
        for score in filtered_scores:
            is_expired, status_msg = get_expiry_status(score.opportunity)
            due_date_str = score.opportunity.due_date.strftime("%Y-%m-%d") if score.opportunity.due_date else "N/A"
            
            # Feature: Recompete signal detection
            recompete_signal = detect_recompete_signal(score.opportunity)
            recompete_display = f"{get_recompete_emoji(recompete_signal)} {recompete_signal}"
            
            # Feature: Free/Pro gating for Action column
            if is_pro:
                action_display = f"{get_color_for_action(score.recommended_action)} {score.recommended_action}"
            else:
                # Free users see blurred/locked action
                action_display = f"🔒 {score.fit_score:.1f} (Pro to unlock)"
            
            # Feature: "Why?" button column
            notice_id = score.opportunity.notice_id
            why_button_key = f"why_btn_{notice_id}"
            
            df_data.append({
                "Fit Score": f"{get_color_for_score(score.fit_score)} {score.fit_score:.1f}",
                "Action": action_display,
                "Why?": f"❓ Explain",  # Will be made clickable via selection
                "Recompete": recompete_display,  # Feature: New column (shortened name for better visibility)
                "Title": score.opportunity.title[:80] + "..." if len(score.opportunity.title) > 80 else score.opportunity.title,
                "Agency": score.opportunity.agency,
                "Domain": score.opportunity.primary_domain or "N/A",
                "Complexity": score.opportunity.complexity or "N/A",
                "Due Date": f"{due_date_str} {status_msg}" if score.opportunity.due_date else "N/A",
                "Notice ID": score.opportunity.notice_id
            })
        
        df = pd.DataFrame(df_data)
        
        # Feature: "Why?" explanation selection
        if len(filtered_scores) > 0:
            # Create a selectbox to choose which opportunity to explain
            why_options = ["-- Select to see explanation --"] + [
                f"{s.opportunity.title[:60]}... (Score: {s.fit_score:.1f})" 
                for s in filtered_scores
            ]
            selected_why_idx = st.selectbox(
                "💡 Click 'Why?' in table or select below to see explanation:",
                options=range(len(why_options)),
                format_func=lambda i: why_options[i],
                key="why_explanation_selector"
            )
            
            # If user selected an opportunity (not the default)
            if selected_why_idx > 0:
                selected_score = filtered_scores[selected_why_idx - 1]
                st.session_state.selected_notice_id = selected_score.opportunity.notice_id
                
                # Generate and display explanation
                explanation = generate_why_explanation(selected_score, is_pro=is_pro)
                
                with st.expander(f"📊 Why {selected_score.recommended_action}? - {selected_score.opportunity.title[:60]}...", expanded=True):
                    st.markdown("### Quick Summary")
                    st.markdown(explanation["bullets"])
                    
                    if is_pro:
                        st.markdown("### Full Explanation")
                        st.markdown(explanation["full"])
                    else:
                        st.info("💡 **Upgrade to Pro** to see full reasoning, detailed breakdown, and AI insights")
        
        # Display table
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Title": st.column_config.TextColumn("Title", width="large"),
                "Fit Score": st.column_config.TextColumn("Fit Score", width="small"),
                "Action": st.column_config.TextColumn("Action", width="small"),
                "Why?": st.column_config.TextColumn("Why?", width="small"),
                "Recompete": st.column_config.TextColumn("Recompete", width="medium"),
            }
        )
        
        # Detailed view
        st.header("📋 Opportunity Details")
        
        selected_index = st.selectbox(
            "Select opportunity to view details",
            options=range(len(filtered_scores)),
            format_func=lambda i: f"{filtered_scores[i].opportunity.title[:60]}... (Score: {filtered_scores[i].fit_score:.1f})"
        )
        
        if selected_index is not None:
            score = filtered_scores[selected_index]
            opp = score.opportunity
            
            # Main columns
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader(opp.title)
                
                # Show expiry warning if expired
                is_expired, status_msg = get_expiry_status(opp)
                if is_expired:
                    st.error(f"⚠️ **EXPIRED OPPORTUNITY** - Deadline passed: {opp.due_date.strftime('%Y-%m-%d') if opp.due_date else 'N/A'}")
                elif opp.due_date:
                    now = _normalize_datetime_for_comparison(opp.due_date)
                    days_remaining = (opp.due_date - now).days
                    if days_remaining <= 7:
                        st.warning(f"🔴 **URGENT** - Only {days_remaining} days remaining until deadline!")
                    elif days_remaining <= 14:
                        st.info(f"🟡 **Deadline approaching** - {days_remaining} days remaining")
                
                st.markdown(f"**Agency:** {opp.agency}")
                if opp.sub_agency:
                    st.markdown(f"**Sub-Agency:** {opp.sub_agency}")
                st.markdown(f"**Notice ID:** {opp.notice_id}")
                if opp.url:
                    # Check if it's a mock opportunity
                    if opp.notice_id.startswith("MOCK-"):
                        st.info("⚠️ **Mock/Test Opportunity** - This is sample data for testing. No real SAM.gov link available.")
                    else:
                        st.markdown(f"**Link:** [{opp.url}]({opp.url})")
                elif opp.notice_id.startswith("MOCK-"):
                    st.info("⚠️ **Mock/Test Opportunity** - This is sample data for testing purposes.")
                
                st.markdown("### Description")
                st.markdown(opp.description)
            
            with col2:
                st.metric("Fit Score", f"{score.fit_score:.1f}/100")
                st.metric("Recommended Action", score.recommended_action)
                
                st.markdown("### Score Breakdown")
                breakdown = score.breakdown
                st.progress(breakdown.domain_match / 100, text=f"Domain Match: {breakdown.domain_match:.1f}%")
                st.progress(breakdown.naics_match / 100, text=f"NAICS Match: {breakdown.naics_match:.1f}%")
                st.progress(breakdown.technical_skill_match / 100, text=f"Technical Skills: {breakdown.technical_skill_match:.1f}%")
                st.progress(breakdown.agency_alignment / 100, text=f"Agency Alignment: {breakdown.agency_alignment:.1f}%")
                st.progress(breakdown.contract_type_fit / 100, text=f"Contract Type: {breakdown.contract_type_fit:.1f}%")
                st.progress(breakdown.strategic_value / 100, text=f"Strategic Value: {breakdown.strategic_value:.1f}%")
            
            # AI Bid Assistant Panel (for BID opportunities)
            if score.recommended_action == RecommendedAction.BID:
                st.markdown("---")
                st.header("🎯 AI Bid Assistant")
                
                # Feature: Free/Pro gating for Bid Strategy
                is_pro_detail = st.session_state.plan == "Pro (demo)"
                if not is_pro_detail:
                    st.warning("🔒 **Pro Feature:** Upgrade to Pro to access AI Bid Assistant, bid strategies, and proposal generation.")
                    st.info("💡 Switch to 'Pro (demo)' in the sidebar to unlock this feature.")
                else:
                    st.info("💡 Use AI to generate bid strategy, proposal content, and win themes for this opportunity.")
                
                bid_tabs = st.tabs(["📋 Bid Strategy", "✍️ Proposal Sections", "📊 Quick Analysis", "💬 Ask Questions"])
                
                with bid_tabs[0]:
                    # Feature: Disable button for Free users
                    if is_pro_detail:
                        if st.button("🚀 Generate Bid Strategy", type="primary", key="generate_strategy"):
                            with st.spinner("Generating comprehensive bid strategy with AI..."):
                                strategy = bid_assistant.generate_bid_strategy(opp, st.session_state.profile, score)
                                
                                st.session_state[f"bid_strategy_{opp.notice_id}"] = strategy
                        
                        if f"bid_strategy_{opp.notice_id}" in st.session_state:
                            strategy = st.session_state[f"bid_strategy_{opp.notice_id}"]
                            
                            st.subheader("🎯 Win Themes")
                            st.markdown(strategy.get("win_themes", "Not generated"))
                            
                            st.subheader("📑 Proposal Outline")
                            st.markdown(strategy.get("proposal_outline", "Not generated"))
                            
                            st.subheader("💬 Key Talking Points")
                            st.markdown(strategy.get("key_talking_points", "Not generated"))
                            
                            st.subheader("🏆 Competitive Positioning")
                            st.markdown(strategy.get("competitive_positioning", "Not generated"))
                            
                            st.subheader("⚠️ Risk Mitigation")
                            st.markdown(strategy.get("risk_mitigation", "Not generated"))
                            
                            st.subheader("📝 Executive Summary Draft")
                            st.text_area(
                                "Executive Summary",
                                value=strategy.get("executive_summary_draft", ""),
                                height=200,
                                key=f"exec_summary_{opp.notice_id}",
                                help="Edit and customize the AI-generated executive summary"
                            )
                    else:
                        st.info("💡 Generate a bid strategy to see detailed recommendations.")
                
                with bid_tabs[1]:
                    if is_pro_detail:
                        st.subheader("Generate Proposal Sections")
                        section_type = st.selectbox(
                            "Select Section Type",
                            options=[
                                "Technical Approach",
                                "Management Plan",
                                "Past Performance",
                                "Key Personnel",
                                "Quality Assurance Plan",
                                "Risk Management Plan",
                                "Transition Plan"
                            ],
                            key=f"section_type_{opp.notice_id}"
                        )
                        
                        section_requirements = st.text_area(
                            "Section Requirements (Optional)",
                            placeholder="Enter any specific requirements or guidance for this section...",
                            key=f"section_req_{opp.notice_id}",
                            height=100
                        )
                        
                        if st.button("✨ Generate Section", key=f"gen_section_{opp.notice_id}"):
                            with st.spinner(f"Generating {section_type} section with AI..."):
                                section_content = bid_assistant.generate_proposal_section(
                                    opp,
                                    st.session_state.profile,
                                    section_type,
                                    section_requirements if section_requirements.strip() else None
                                )
                                
                                st.text_area(
                                    f"{section_type}",
                                    value=section_content,
                                    height=400,
                                    key=f"section_content_{opp.notice_id}",
                                    help="Edit and customize the AI-generated section"
                                )
                    else:
                        st.info("💡 Upgrade to Pro to generate proposal sections.")
                
                with bid_tabs[2]:
                    if is_pro_detail:
                        st.subheader("Quick Bid Analysis")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric("Fit Score", f"{score.fit_score:.1f}/100")
                            st.metric("Domain Match", f"{score.breakdown.domain_match:.1f}%")
                            st.metric("NAICS Match", f"{score.breakdown.naics_match:.1f}%")
                        
                        with col2:
                            st.metric("Technical Skills Match", f"{score.breakdown.technical_skill_match:.1f}%")
                            st.metric("Agency Alignment", f"{score.breakdown.agency_alignment:.1f}%")
                            st.metric("Strategic Value", f"{score.breakdown.strategic_value:.1f}%")
                        
                        if score.risk_factors:
                            st.subheader("⚠️ Risk Factors")
                            for risk in score.risk_factors:
                                st.warning(f"• {risk}")
                        
                        st.subheader("✅ Strengths")
                        strengths = []
                        if score.breakdown.domain_match >= 70:
                            strengths.append("Strong domain alignment")
                        if score.breakdown.naics_match >= 70:
                            strengths.append("Excellent NAICS code match")
                        if score.breakdown.technical_skill_match >= 70:
                            strengths.append("Strong technical capabilities match")
                        if score.breakdown.agency_alignment >= 70:
                            strengths.append("Good agency relationship potential")
                        
                        if strengths:
                            for strength in strengths:
                                st.success(f"✓ {strength}")
                        else:
                            st.info("Review individual match scores to identify strengths")
                    else:
                        st.info("💡 Upgrade to Pro to see detailed bid analysis.")
                
                with bid_tabs[3]:
                    if is_pro_detail:
                        st.subheader("💬 Ask Questions About This Opportunity")
                        st.info("💡 Ask any questions about this opportunity. Upload PDF attachments (e.g., submission instructions, requirements) to get answers based on the documents.")
                        
                        # PDF Upload Section
                        st.markdown("### 📎 Upload Opportunity Documents (PDFs)")
                        uploaded_files = st.file_uploader(
                        "Upload PDF documents (e.g., Submission Instructions, Requirements, Security Requirements)",
                        type=['pdf'],
                        accept_multiple_files=True,
                        key=f"pdf_upload_{opp.notice_id}",
                        help="Upload PDF attachments from the opportunity to get AI-powered summaries and Q&A"
                    )
                    
                    # Store PDF texts in session state
                    pdf_key = f"pdf_texts_{opp.notice_id}"
                    if pdf_key not in st.session_state:
                        st.session_state[pdf_key] = {}
                    
                    # Process uploaded PDFs
                    if uploaded_files:
                        for uploaded_file in uploaded_files:
                            if uploaded_file.name not in st.session_state[pdf_key]:
                                with st.spinner(f"Processing {uploaded_file.name}..."):
                                    # Extract text from PDF
                                    pdf_bytes = uploaded_file.read()
                                    pdf_text = bid_assistant.extract_text_from_pdf(io.BytesIO(pdf_bytes))
                                    
                                    # Store in session state
                                    st.session_state[pdf_key][uploaded_file.name] = {
                                        "text": pdf_text,
                                        "summary": None
                                    }
                                    
                                    st.success(f"✅ Processed {uploaded_file.name}")
                    
                    # Display uploaded PDFs and summaries
                    if st.session_state[pdf_key]:
                        st.markdown("### 📄 Uploaded Documents")
                        for filename, pdf_data in st.session_state[pdf_key].items():
                            with st.expander(f"📎 {filename}", expanded=False):
                                col1, col2 = st.columns([3, 1])
                                
                                with col1:
                                    st.markdown(f"**File:** {filename}")
                                    if pdf_data["summary"]:
                                        st.markdown("**Summary:**")
                                        st.markdown(pdf_data["summary"])
                                    else:
                                        if st.button(f"📝 Generate Summary", key=f"summarize_{filename}_{opp.notice_id}"):
                                            with st.spinner("Generating summary with AI..."):
                                                summary = bid_assistant.summarize_pdf(
                                                    pdf_data["text"],
                                                    opp,
                                                    st.session_state.profile
                                                )
                                                st.session_state[pdf_key][filename]["summary"] = summary
                                                st.rerun()
                                
                                with col2:
                                    if st.button("🗑️ Remove", key=f"remove_{filename}_{opp.notice_id}"):
                                        del st.session_state[pdf_key][filename]
                                        st.rerun()
                    
                    # Initialize chat history in session state
                    chat_key = f"bid_chat_{opp.notice_id}"
                    if chat_key not in st.session_state:
                        st.session_state[chat_key] = []
                    
                    # Display chat history
                    if st.session_state[chat_key]:
                        st.markdown("### Conversation History")
                        for i, (q, a) in enumerate(st.session_state[chat_key]):
                            with st.expander(f"Q{i+1}: {q[:60]}...", expanded=False):
                                st.markdown(f"**Question:** {q}")
                                st.markdown(f"**Answer:** {a}")
                    
                    # Question input
                    question = st.text_input(
                        "Ask a question about this opportunity",
                        placeholder="e.g., What is the contract amount? How do I submit the bid? What are the submission requirements?",
                        key=f"question_input_{opp.notice_id}"
                    )
                    
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        ask_button = st.button("❓ Ask", type="primary", key=f"ask_button_{opp.notice_id}")
                    
                    # Suggested questions
                    with col2:
                        st.markdown("**Suggested questions:**")
                        suggested_questions = [
                            "What is the contract amount?",
                            "How do I submit the bid?",
                            "What are the submission requirements?",
                            "What is the deadline?",
                            "What are the key requirements?",
                            "What certifications are needed?",
                            "What is the place of performance?",
                            "What is the contract type?"
                        ]
                        for sq in suggested_questions[:4]:  # Show first 4
                            if st.button(sq, key=f"suggested_{sq[:20]}_{opp.notice_id}"):
                                question = sq
                                ask_button = True
                    
                    # Process question
                    if ask_button and question.strip():
                        with st.spinner("🤔 Thinking..."):
                            # Get PDF texts if available
                            pdf_texts = []
                            if pdf_key in st.session_state and st.session_state[pdf_key]:
                                pdf_texts = [data["text"] for data in st.session_state[pdf_key].values()]
                            
                            # Answer with PDF context if available
                            if pdf_texts:
                                answer = bid_assistant.answer_question_with_pdfs(
                                    question,
                                    opp,
                                    st.session_state.profile,
                                    pdf_texts,
                                    score
                                )
                            else:
                                answer = bid_assistant.answer_question(
                                    question,
                                    opp,
                                    st.session_state.profile,
                                    score
                                )
                            
                            # Add to chat history
                            st.session_state[chat_key].append((question, answer))
                            
                            # Display answer
                            st.markdown("### Answer")
                            st.success(answer)
                            
                            # Clear input by rerunning
                            st.rerun()
                    
                        # Clear chat history button
                        if st.session_state[chat_key]:
                            if st.button("🗑️ Clear Conversation", key=f"clear_chat_{opp.notice_id}"):
                                st.session_state[chat_key] = []
                                st.rerun()
                    else:
                        st.info("💡 Upgrade to Pro to ask questions and upload PDFs for AI-powered Q&A.")
            
            # AI Reasoning Panel
            with st.expander("🤖 AI Reasoning & Explanation", expanded=True):
                st.markdown("### Explanation")
                st.info(score.explanation)
                
                st.markdown("### Detailed Reasoning")
                st.markdown(score.reasoning)
                
                if score.risk_factors:
                    st.markdown("### Risk Factors")
                    for risk in score.risk_factors:
                        st.warning(f"⚠️ {risk}")
            
            # Opportunity Details
            with st.expander("📄 Full Opportunity Details"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**NAICS:** {', '.join(opp.naics) if opp.naics else 'N/A'}")
                    st.markdown(f"**PSC:** {opp.psc or 'N/A'}")
                    st.markdown(f"**Set-Aside:** {opp.set_aside or 'N/A'}")
                    st.markdown(f"**Contract Type:** {opp.contract_type or 'N/A'}")
                    st.markdown(f"**Response Type:** {opp.response_type or 'N/A'}")
                
                with col2:
                    st.markdown(f"**Primary Domain:** {opp.primary_domain or 'N/A'}")
                    st.markdown(f"**Secondary Domains:** {', '.join([str(d) for d in opp.secondary_domains]) if opp.secondary_domains else 'N/A'}")
                    st.markdown(f"**Complexity:** {opp.complexity or 'N/A'}")
                    st.markdown(f"**Project Type:** {opp.project_type or 'N/A'}")
                    st.markdown(f"**Is Legacy:** {opp.is_legacy or False}")
                    st.markdown(f"**Place of Performance:** {opp.place_of_performance or 'N/A'}")
        
        # Export to CSV
        if st.button("📥 Export to CSV"):
            csv_data = []
            for score in filtered_scores:
                # Feature: Include recompete signal in export
                recompete_signal = detect_recompete_signal(score.opportunity)
                
                csv_data.append({
                    "Notice ID": score.opportunity.notice_id,
                    "Title": score.opportunity.title,
                    "Agency": score.opportunity.agency,
                    "Fit Score": score.fit_score,
                    "Recommended Action": score.recommended_action,
                    "Recompete": recompete_signal,  # Feature: New column
                    "Domain Match": score.breakdown.domain_match,
                    "NAICS Match": score.breakdown.naics_match,
                    "Technical Skill Match": score.breakdown.technical_skill_match,
                    "Agency Alignment": score.breakdown.agency_alignment,
                    "Contract Type Fit": score.breakdown.contract_type_fit,
                    "Strategic Value": score.breakdown.strategic_value,
                    "Primary Domain": score.opportunity.primary_domain,
                    "Complexity": score.opportunity.complexity,
                    "Due Date": score.opportunity.due_date.isoformat() if score.opportunity.due_date else "",
                    "URL": score.opportunity.url or ""
                })
            
            df_export = pd.DataFrame(csv_data)
            csv = df_export.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"contract_opportunities_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    elif st.session_state.opportunities:
        st.info("💡 Click 'Score Opportunities' to see AI-powered fit scores and recommendations.")
    
    else:
        st.info("💡 Click 'Fetch Opportunities from SAM.gov' to begin searching for contracts.")


# Initialize app - catch errors early but don't stop if database fails
# Database will be initialized lazily when first accessed
try:
    # Test database connection early (but don't fail if it doesn't work)
    _ = db.get_session()
    logger.info("Database connection successful")
except Exception as db_error:
    logger.warning(f"Database initialization warning (will retry on first use): {db_error}")
    # Don't stop - let it fail gracefully when actually used

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Catch any unhandled exceptions and display them
        logger.exception("Unhandled exception in main:")
        st.error(f"❌ Application Error: {str(e)}")
        st.exception(e)
        st.info("""
        **Troubleshooting Steps:**
        1. Check that all environment variables are set correctly
        2. Ensure the database file is writable
        3. Check the logs for more details
        4. Try refreshing the page
        """)

