"""
AI-powered fit scoring engine.
Computes fit scores and recommendations for opportunities.
"""
import logging
from typing import List
import json

from openai import OpenAI
from config import settings
from models import (
    Opportunity, CapabilityProfile, OpportunityScore,
    FitScoreBreakdown, RecommendedAction
)

logger = logging.getLogger(__name__)


class AIScoringEngine:
    """AI-powered fit scoring engine for opportunity matching."""
    
    # Scoring weights (as specified in requirements)
    WEIGHTS = {
        "domain_match": 0.30,
        "naics_match": 0.20,
        "technical_skill_match": 0.20,
        "agency_alignment": 0.10,
        "contract_type_fit": 0.10,
        "strategic_value": 0.10
    }
    
    def __init__(self):
        if settings.openai_api_key:
            self.client = OpenAI(api_key=settings.openai_api_key)
            self.use_openai = True
            self.model = settings.openai_model
        elif settings.ollama_base_url:
            self.client = OpenAI(
                base_url=settings.ollama_base_url,
                api_key="ollama"
            )
            self.use_openai = False
            self.model = settings.ollama_model
        else:
            logger.warning("No AI provider configured. Using rule-based scoring.")
            self.client = None
            self.use_openai = False
            self.model = None
    
    def score_opportunity(
        self,
        opportunity: Opportunity,
        profile: CapabilityProfile
    ) -> OpportunityScore:
        """
        Score an opportunity against a capability profile.
        
        Args:
            opportunity: Opportunity to score
            profile: Company capability profile
            
        Returns:
            OpportunityScore with fit score and recommendation
        """
        if not self.client:
            # Fallback to rule-based scoring
            return self._rule_based_score(opportunity, profile)
        
        try:
            score_data = self._ai_score(opportunity, profile)
            
            # Ensure breakdown exists
            if "breakdown" not in score_data or not score_data["breakdown"]:
                # Fallback to rule-based if AI didn't return breakdown
                logger.warning(f"AI didn't return breakdown for {opportunity.notice_id}, using rule-based")
                return self._rule_based_score(opportunity, profile)
            
            # Calculate weighted fit score
            breakdown = FitScoreBreakdown(**score_data["breakdown"])
            fit_score = (
                breakdown.domain_match * self.WEIGHTS["domain_match"] +
                breakdown.naics_match * self.WEIGHTS["naics_match"] +
                breakdown.technical_skill_match * self.WEIGHTS["technical_skill_match"] +
                breakdown.agency_alignment * self.WEIGHTS["agency_alignment"] +
                breakdown.contract_type_fit * self.WEIGHTS["contract_type_fit"] +
                breakdown.strategic_value * self.WEIGHTS["strategic_value"]
            )
            
            # Determine recommended action
            if fit_score >= 70:
                recommended_action = RecommendedAction.BID
            elif fit_score >= 50:
                recommended_action = RecommendedAction.TEAM_SUB
            else:
                recommended_action = RecommendedAction.IGNORE
            
            # Pass profile directly - Pydantic v2 should handle CapabilityProfile instances
            # Get explanation and reasoning with defaults
            explanation = score_data.get("explanation", "AI scoring completed")
            reasoning = score_data.get("reasoning", explanation)
            risk_factors = score_data.get("risk_factors", [])
            
            try:
                return OpportunityScore(
                    opportunity=opportunity,
                    capability_profile=profile,  # Try passing instance directly
                    fit_score=round(fit_score, 2),
                    breakdown=breakdown,
                    explanation=explanation,
                    risk_factors=risk_factors,
                    recommended_action=recommended_action,
                    reasoning=reasoning
                )
            except (ValueError, TypeError) as e:
                # Fallback: convert to dict and reconstruct if direct instance doesn't work
                logger.debug(f"Direct profile instance failed, converting to dict: {e}")
                if isinstance(profile, CapabilityProfile):
                    try:
                        profile_dict = profile.model_dump()
                    except AttributeError:
                        profile_dict = profile.dict()
                else:
                    profile_dict = profile
                
                return OpportunityScore(
                    opportunity=opportunity,
                    capability_profile=CapabilityProfile(**profile_dict),  # Reconstruct from dict
                    fit_score=round(fit_score, 2),
                    breakdown=breakdown,
                    explanation=explanation,
                    risk_factors=risk_factors,
                    recommended_action=recommended_action,
                    reasoning=reasoning
                )
            
        except Exception as e:
            logger.error(f"Error scoring opportunity {opportunity.notice_id}: {e}")
            # Fallback to rule-based
            return self._rule_based_score(opportunity, profile)
    
    def _ai_score(self, opportunity: Opportunity, profile: CapabilityProfile) -> dict:
        """Use AI to score opportunity fit."""
        prompt = f"""You are an expert federal IT capture manager and AI architect. Score how well this opportunity fits the company's capabilities.

OPPORTUNITY:
Title: {opportunity.title}
Description: {opportunity.description[:1500]}
Agency: {opportunity.agency}
NAICS: {', '.join(opportunity.naics) if opportunity.naics else 'N/A'}
Primary Domain: {opportunity.primary_domain}
Complexity: {opportunity.complexity}
Project Type: {opportunity.project_type}
Set-Aside: {opportunity.set_aside}
Contract Type: {opportunity.contract_type}
Due Date: {opportunity.due_date}

COMPANY PROFILE:
Name: {profile.company_name}
Core Domains: {', '.join(profile.core_domains)}
Technical Skills: {', '.join(profile.technical_skills)}
NAICS: {', '.join(profile.naics)}
Preferred Agencies: {', '.join(profile.preferred_agencies)}
Certifications: {', '.join(profile.certifications)}
Role Preference: {profile.role_preference}

Score this opportunity on a 0-100 scale for each category:
1. Domain Match (30% weight): How well does the opportunity's domain align with company's core domains?
2. NAICS Match (20% weight): Do the NAICS codes align?
3. Technical Skill Match (20% weight): Do the required technical skills match company capabilities?
4. Agency Alignment (10% weight): Is this a preferred agency?
5. Contract Type Fit (10% weight): Does the contract type and set-aside work for the company?
6. Strategic Value (10% weight): Strategic importance for company growth/market entry?

Return ONLY a valid JSON object:
{{
    "breakdown": {{
        "domain_match": 0-100,
        "naics_match": 0-100,
        "technical_skill_match": 0-100,
        "agency_alignment": 0-100,
        "contract_type_fit": 0-100,
        "strategic_value": 0-100
    }},
    "explanation": "Plain-English explanation of the fit (2-3 sentences)",
    "risk_factors": ["list", "of", "key", "risks"],
    "reasoning": "Detailed reasoning for the scores (3-5 sentences)"
}}

Return ONLY the JSON object, no other text."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a federal IT capture manager. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            score_data = json.loads(content)
            
            # Ensure all required keys exist with defaults
            if "breakdown" not in score_data:
                score_data["breakdown"] = {}
            if "explanation" not in score_data:
                score_data["explanation"] = "AI classification completed"
            if "reasoning" not in score_data:
                score_data["reasoning"] = score_data["explanation"]
            if "risk_factors" not in score_data:
                score_data["risk_factors"] = []
            
            # Validate scores are in 0-100 range
            breakdown = score_data.get("breakdown", {})
            for key, value in breakdown.items():
                breakdown[key] = max(0, min(100, float(value)))
            score_data["breakdown"] = breakdown
            
            return score_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.error(f"Response was: {content}")
            raise
        except Exception as e:
            logger.error(f"Error in AI scoring: {e}")
            raise
    
    def _rule_based_score(
        self,
        opportunity: Opportunity,
        profile: CapabilityProfile
    ) -> OpportunityScore:
        """Fallback rule-based scoring when AI is unavailable."""
        # Domain match - improved to handle new domain formats
        opp_domain = str(opportunity.primary_domain).lower() if opportunity.primary_domain else ""
        domain_match = 0
        
        # Create domain keywords for matching
        domain_keywords = {
            "ai": ["ai", "ml", "machine learning", "artificial intelligence"],
            "data": ["data", "analytics", "engineering", "warehouse", "bi"],
            "cloud": ["cloud", "migration", "architecture", "aws", "azure", "gcp"],
            "cyber": ["cyber", "security", "zero trust", "fedramp", "fisma"],
            "software": ["devops", "devsecops", "automation", "ci/cd", "software"],
        }
        
        for domain in profile.core_domains:
            domain_lower = domain.lower()
            # Direct match
            if domain_lower in opp_domain or opp_domain in domain_lower:
                domain_match = 80
                break
            # Keyword-based matching for new formats
            for key, keywords in domain_keywords.items():
                if any(kw in domain_lower for kw in keywords) and any(kw in opp_domain for kw in keywords):
                    domain_match = 80
                    break
            if domain_match > 0:
                break
        
        if domain_match == 0:
            domain_match = 30  # Partial match
        
        # NAICS match
        naics_match = 0
        if opportunity.naics and profile.naics:
            common_naics = set(opportunity.naics) & set(profile.naics)
            if common_naics:
                naics_match = 100
            else:
                naics_match = 20
        else:
            naics_match = 50  # Neutral if no NAICS data
        
        # Technical skill match (keyword-based)
        text = f"{opportunity.title} {opportunity.description}".lower()
        skill_matches = sum(1 for skill in profile.technical_skills if skill.lower() in text)
        total_skills = len(profile.technical_skills) if profile.technical_skills else 1
        technical_skill_match = min(100, (skill_matches / total_skills) * 100) if total_skills > 0 else 50
        
        # Agency alignment
        agency_match = 0
        opp_agency = opportunity.agency.lower()
        for pref_agency in profile.preferred_agencies:
            if pref_agency.lower() in opp_agency or opp_agency in pref_agency.lower():
                agency_match = 100
                break
        if agency_match == 0:
            agency_match = 50  # Neutral
        
        # Contract type fit (simplified)
        contract_type_fit = 70  # Default assumption
        
        # Strategic value (heuristic)
        strategic_value = 60  # Default moderate value
        
        breakdown = FitScoreBreakdown(
            domain_match=domain_match,
            naics_match=naics_match,
            technical_skill_match=technical_skill_match,
            agency_alignment=agency_match,
            contract_type_fit=contract_type_fit,
            strategic_value=strategic_value
        )
        
        fit_score = (
            breakdown.domain_match * self.WEIGHTS["domain_match"] +
            breakdown.naics_match * self.WEIGHTS["naics_match"] +
            breakdown.technical_skill_match * self.WEIGHTS["technical_skill_match"] +
            breakdown.agency_alignment * self.WEIGHTS["agency_alignment"] +
            breakdown.contract_type_fit * self.WEIGHTS["contract_type_fit"] +
            breakdown.strategic_value * self.WEIGHTS["strategic_value"]
        )
        
        if fit_score >= 70:
            recommended_action = RecommendedAction.BID
        elif fit_score >= 50:
            recommended_action = RecommendedAction.TEAM_SUB
        else:
            recommended_action = RecommendedAction.IGNORE
        
        explanation = f"Domain match: {domain_match:.0f}%, NAICS: {naics_match:.0f}%, Skills: {technical_skill_match:.0f}%"
        
        # Pass profile directly - Pydantic v2 should handle CapabilityProfile instances
        # If that fails, convert to dict
        try:
            return OpportunityScore(
                opportunity=opportunity,
                capability_profile=profile,  # Try passing instance directly
                fit_score=round(fit_score, 2),
                breakdown=breakdown,
                explanation=explanation,
                risk_factors=["Rule-based scoring used (AI unavailable)"],
                recommended_action=recommended_action,
                reasoning=explanation
            )
        except Exception:
            # Fallback: convert to dict if direct instance doesn't work
            if isinstance(profile, CapabilityProfile):
                try:
                    profile_dict = profile.model_dump()
                except AttributeError:
                    profile_dict = profile.dict()
            else:
                profile_dict = profile
            
            return OpportunityScore(
                opportunity=opportunity,
                capability_profile=CapabilityProfile(**profile_dict),  # Reconstruct from dict
                fit_score=round(fit_score, 2),
                breakdown=breakdown,
                explanation=explanation,
                risk_factors=["Rule-based scoring used (AI unavailable)"],
                recommended_action=recommended_action,
                reasoning=explanation
            )
    
    def score_batch(
        self,
        opportunities: List[Opportunity],
        profile: CapabilityProfile
    ) -> List[OpportunityScore]:
        """
        Score multiple opportunities.
        Uses AI for first 20 opportunities, then rule-based for the rest (much faster).
        """
        if not self.client:
            # No AI available - use rule-based for all
            return [self._rule_based_score(opp, profile) for opp in opportunities]
        
        # Limit AI scoring to first 20 for speed (rest use fast rule-based)
        max_ai_score = 20
        scores = []
        
        for i, opp in enumerate(opportunities):
            if i < max_ai_score:
                # Use AI for first batch
                scores.append(self.score_opportunity(opp, profile))
            else:
                # Use fast rule-based for the rest
                scores.append(self._rule_based_score(opp, profile))
        
        return scores
