"""
AI-powered opportunity classification engine.
Classifies opportunities by domain, complexity, and project type.
"""
import logging
from typing import List, Optional
import json

from openai import OpenAI
from config import settings
from models import Opportunity, OpportunityDomain, Complexity, ProjectType

logger = logging.getLogger(__name__)


class AIClassifier:
    """AI-powered classifier for SAM.gov opportunities."""
    
    def __init__(self):
        if settings.openai_api_key:
            self.client = OpenAI(api_key=settings.openai_api_key)
            self.use_openai = True
            self.model = settings.openai_model
        elif settings.ollama_base_url:
            # Use local Ollama
            self.client = OpenAI(
                base_url=settings.ollama_base_url,
                api_key="ollama"  # Ollama doesn't require a real key
            )
            self.use_openai = False
            self.model = settings.ollama_model
        else:
            logger.warning("No AI provider configured. Using rule-based classification.")
            self.client = None
            self.use_openai = False
            self.model = None
    
    def classify_opportunity(self, opportunity: Opportunity) -> Opportunity:
        """
        Classify an opportunity using AI.
        
        Args:
            opportunity: Opportunity to classify
            
        Returns:
            Opportunity with classification fields populated
        """
        if not self.client:
            # Fallback to rule-based classification
            return self._rule_based_classify(opportunity)
        
        try:
            classification = self._ai_classify(opportunity)
            
            # Update opportunity with classification
            opportunity.primary_domain = classification.get("primary_domain")
            opportunity.secondary_domains = classification.get("secondary_domains", [])
            opportunity.complexity = classification.get("complexity")
            opportunity.project_type = classification.get("project_type")
            opportunity.is_legacy = classification.get("is_legacy", False)
            
            return opportunity
            
        except Exception as e:
            logger.error(f"Error classifying opportunity {opportunity.notice_id}: {e}")
            # Fallback to rule-based
            return self._rule_based_classify(opportunity)
    
    def _ai_classify(self, opportunity: Opportunity) -> dict:
        """Use AI to classify opportunity."""
        prompt = f"""You are an expert federal IT contracting analyst. Classify the following SAM.gov opportunity.

OPPORTUNITY TITLE: {opportunity.title}

DESCRIPTION:
{opportunity.description[:2000]}

NAICS: {', '.join(opportunity.naics) if opportunity.naics else 'N/A'}
AGENCY: {opportunity.agency}

Classify this opportunity and return ONLY a valid JSON object with the following structure:
{{
    "primary_domain": "AI" | "Data" | "Cloud" | "Cybersecurity" | "IT Operations" | "Software Engineering" | "Modernization" | "Other",
    "secondary_domains": ["list", "of", "secondary", "domains"],
    "complexity": "Low" | "Medium" | "High",
    "project_type": "Modernization" | "Operations" | "Greenfield" | "Legacy",
    "is_legacy": true | false
}}

Focus on:
- AI/ML: artificial intelligence, machine learning, LLMs, RAG, NLP, computer vision
- Data: data engineering, analytics, BI, data warehousing, SAS, Python, R
- Cloud: AWS, Azure, GCP, migration, containers, Kubernetes, serverless
- Cybersecurity: zero trust, FedRAMP, FISMA, RMF, IAM, SOC, SIEM
- IT Operations: IT consulting, operations, support, PMO, ITSM
- Software: development, APIs, microservices, DevOps, CI/CD
- Modernization: legacy system modernization, mainframe migration

Return ONLY the JSON object, no other text."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a federal IT contracting expert. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            classification = json.loads(content)
            
            # Validate and normalize
            return {
                "primary_domain": self._normalize_domain(classification.get("primary_domain")),
                "secondary_domains": [
                    self._normalize_domain(d) 
                    for d in classification.get("secondary_domains", [])
                ],
                "complexity": self._normalize_complexity(classification.get("complexity")),
                "project_type": self._normalize_project_type(classification.get("project_type")),
                "is_legacy": classification.get("is_legacy", False)
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.error(f"Response was: {content}")
            raise
        except Exception as e:
            logger.error(f"Error in AI classification: {e}")
            raise
    
    def _normalize_domain(self, domain: str) -> Optional[OpportunityDomain]:
        """Normalize domain string to enum."""
        if not domain:
            return None
        
        domain_upper = domain.upper()
        domain_mapping = {
            "AI": OpportunityDomain.AI,
            "AI/ML": OpportunityDomain.AI,
            "MACHINE LEARNING": OpportunityDomain.AI,
            "ML": OpportunityDomain.AI,
            "DATA": OpportunityDomain.DATA,
            "DATA ANALYTICS": OpportunityDomain.DATA,
            "DATA ANALYTICS/ENGINEERING": OpportunityDomain.DATA,
            "DATA ENGINEERING": OpportunityDomain.DATA,
            "CLOUD": OpportunityDomain.CLOUD,
            "CLOUD ARCHITECTURE": OpportunityDomain.CLOUD,
            "CLOUD ARCHITECTURE & MIGRATION": OpportunityDomain.CLOUD,
            "CLOUD MIGRATION": OpportunityDomain.CLOUD,
            "CYBERSECURITY": OpportunityDomain.CYBER,
            "CYBERSECURITY/ZERO TRUST": OpportunityDomain.CYBER,
            "ZERO TRUST": OpportunityDomain.CYBER,
            "CYBER": OpportunityDomain.CYBER,
            "DEVSECOPS": OpportunityDomain.SOFTWARE,
            "DEVSECOPS/AUTOMATION": OpportunityDomain.SOFTWARE,
            "DEVOPS": OpportunityDomain.SOFTWARE,
            "AUTOMATION": OpportunityDomain.SOFTWARE,
            "IT OPERATIONS": OpportunityDomain.IT_OPS,
            "IT OPS": OpportunityDomain.IT_OPS,
            "SOFTWARE": OpportunityDomain.SOFTWARE,
            "SOFTWARE ENGINEERING": OpportunityDomain.SOFTWARE,
            "MODERNIZATION": OpportunityDomain.MODERNIZATION,
        }
        
        for key, value in domain_mapping.items():
            if key in domain_upper:
                return value
        
        return OpportunityDomain.OTHER
    
    def _normalize_complexity(self, complexity: str) -> Optional[Complexity]:
        """Normalize complexity string to enum."""
        if not complexity:
            return Complexity.MEDIUM  # Default
        
        complexity_upper = complexity.upper()
        if "HIGH" in complexity_upper:
            return Complexity.HIGH
        elif "LOW" in complexity_upper:
            return Complexity.LOW
        else:
            return Complexity.MEDIUM
    
    def _normalize_project_type(self, project_type: str) -> Optional[ProjectType]:
        """Normalize project type string to enum."""
        if not project_type:
            return None
        
        pt_upper = project_type.upper()
        if "MODERNIZATION" in pt_upper:
            return ProjectType.MODERNIZATION
        elif "OPERATIONS" in pt_upper:
            return ProjectType.OPERATIONS
        elif "GREENFIELD" in pt_upper:
            return ProjectType.GREENFIELD
        elif "LEGACY" in pt_upper:
            return ProjectType.LEGACY
        
        return None
    
    def _rule_based_classify(self, opportunity: Opportunity) -> Opportunity:
        """
        Fallback rule-based classification when AI is unavailable.
        Uses keyword matching and heuristics.
        """
        text = f"{opportunity.title} {opportunity.description}".lower()
        
        # Exclude obvious non-IT terms that might cause false positives
        non_it_terms = [
            "grounds maintenance", "custodial", "janitorial", "cleaning", "waste collection",
            "valve", "cable assembly", "bracket", "cylinder", "window", "disc brake",
            "seal", "hinge", "elbow pipe", "cap shaft", "link assembly", "support structural",
            "hose exhaust", "fire pump", "water purification", "fume hood", "cabinet",
            "countertop", "barracks", "pier", "trailer", "apparel", "ammunition"
        ]
        
        # If title contains non-IT terms, classify as OTHER
        if any(term in text for term in non_it_terms):
            opportunity.primary_domain = OpportunityDomain.OTHER
            opportunity.complexity = Complexity.LOW
            return opportunity
        
        # Domain classification (only if IT-related)
        domains = []
        # AI/ML - require stronger signals
        if any(kw in text for kw in ["artificial intelligence", "machine learning", "ml model", "llm", "rag", "nlp", "neural network", "deep learning"]):
            domains.append(OpportunityDomain.AI)
        # Data - require data-specific terms
        if any(kw in text for kw in ["data analytics", "data engineering", "data warehouse", "data lake", "business intelligence", "bi ", "etl", "data pipeline"]):
            domains.append(OpportunityDomain.DATA)
        # Cloud - require cloud-specific terms
        if any(kw in text for kw in ["cloud migration", "cloud architecture", "aws ", "azure ", "gcp ", "cloud platform", "cloud infrastructure"]):
            domains.append(OpportunityDomain.CLOUD)
        # Cybersecurity - require security-specific terms
        if any(kw in text for kw in ["cybersecurity", "zero trust", "fedramp", "fisma", "security operations", "soc", "siem", "iam"]):
            domains.append(OpportunityDomain.CYBER)
        # Software/DevOps - require development/ops terms
        if any(kw in text for kw in ["software development", "devops", "devsecops", "ci/cd", "kubernetes", "docker", "terraform", "automation"]):
            domains.append(OpportunityDomain.SOFTWARE)
        # Modernization
        if any(kw in text for kw in ["modernization", "legacy system", "mainframe migration", "system upgrade"]):
            domains.append(OpportunityDomain.MODERNIZATION)
        
        if domains:
            opportunity.primary_domain = domains[0]
            opportunity.secondary_domains = domains[1:]
        else:
            opportunity.primary_domain = OpportunityDomain.OTHER
        
        # Complexity (heuristic)
        word_count = len(opportunity.description.split())
        if word_count > 1000 or "complex" in text or "enterprise" in text:
            opportunity.complexity = Complexity.HIGH
        elif word_count < 200:
            opportunity.complexity = Complexity.LOW
        else:
            opportunity.complexity = Complexity.MEDIUM
        
        # Project type
        if "modernization" in text or "migration" in text or "legacy" in text:
            opportunity.project_type = ProjectType.MODERNIZATION
            opportunity.is_legacy = True
        elif "operations" in text or "support" in text or "maintenance" in text:
            opportunity.project_type = ProjectType.OPERATIONS
        elif "new" in text or "development" in text or "build" in text:
            opportunity.project_type = ProjectType.GREENFIELD
        
        return opportunity
    
    def classify_batch(self, opportunities: List[Opportunity]) -> List[Opportunity]:
        """Classify multiple opportunities."""
        return [self.classify_opportunity(opp) for opp in opportunities]
