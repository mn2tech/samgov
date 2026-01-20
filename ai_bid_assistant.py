"""
AI Bid Assistant - Helps generate bid content, proposals, and win strategies.
"""
import logging
from typing import Dict, Optional, List
from openai import OpenAI
import io

from config import settings
from models import Opportunity, CapabilityProfile, OpportunityScore

# PDF parsing
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    try:
        import pdfplumber
        PDF_AVAILABLE = True
    except ImportError:
        PDF_AVAILABLE = False

logger = logging.getLogger(__name__)


class AIBidAssistant:
    """AI-powered assistant for bid preparation and proposal writing."""
    
    def __init__(self):
        """Initialize AI Bid Assistant."""
        self.client = None
        self.use_openai = False
        
        if settings.openai_api_key:
            try:
                self.client = OpenAI(api_key=settings.openai_api_key)
                self.use_openai = True
                logger.info("AI Bid Assistant initialized with OpenAI")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
                self.use_openai = False
    
    def generate_bid_strategy(
        self,
        opportunity: Opportunity,
        profile: CapabilityProfile,
        score: OpportunityScore
    ) -> Dict[str, str]:
        """
        Generate comprehensive bid strategy and proposal guidance.
        
        Returns:
            Dictionary with:
            - win_themes: Key win themes and differentiators
            - proposal_outline: Structured proposal outline
            - key_talking_points: Important points to emphasize
            - competitive_positioning: How to position against competitors
            - risk_mitigation: Strategies to address risks
            - executive_summary_draft: Draft executive summary
        """
        if not self.use_openai:
            return self._fallback_bid_strategy(opportunity, profile, score)
        
        try:
            prompt = self._build_bid_strategy_prompt(opportunity, profile, score)
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert government contracting proposal writer and bid strategist with deep knowledge of federal procurement."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            
            # Parse the response into structured sections
            return self._parse_bid_strategy_response(content, opportunity, profile, score)
            
        except Exception as e:
            logger.error(f"Error generating bid strategy with AI: {e}")
            return self._fallback_bid_strategy(opportunity, profile, score)
    
    def generate_proposal_section(
        self,
        opportunity: Opportunity,
        profile: CapabilityProfile,
        section_name: str,
        section_requirements: Optional[str] = None
    ) -> str:
        """
        Generate a specific proposal section (e.g., Technical Approach, Management Plan).
        
        Args:
            opportunity: The opportunity
            profile: Company capability profile
            section_name: Name of section to generate (e.g., "Technical Approach", "Management Plan")
            section_requirements: Optional specific requirements for this section
            
        Returns:
            Generated proposal section text
        """
        if not self.use_openai:
            return self._fallback_proposal_section(section_name, opportunity, profile)
        
        try:
            prompt = f"""Generate a compelling {section_name} section for a government contract proposal.

OPPORTUNITY DETAILS:
Title: {opportunity.title}
Agency: {opportunity.agency}
Description: {opportunity.description[:1000]}
Domain: {opportunity.primary_domain}
Complexity: {opportunity.complexity}

COMPANY CAPABILITIES:
Company: {profile.company_name}
Core Domains: {', '.join(profile.core_domains)}
Technical Skills: {', '.join(profile.technical_skills[:15])}
NAICS Codes: {', '.join(profile.naics)}
Certifications: {', '.join(profile.certifications) if profile.certifications else 'None'}
Role Preference: {profile.role_preference}

{f'SECTION REQUIREMENTS: {section_requirements}' if section_requirements else ''}

Generate a professional, compelling {section_name} section that:
1. Directly addresses the opportunity requirements
2. Highlights relevant company capabilities and experience
3. Demonstrates understanding of the agency's needs
4. Uses clear, professional language appropriate for government proposals
5. Is specific and actionable (not generic)

Length: 300-500 words. Focus on value proposition and differentiation."""

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert government proposal writer specializing in federal IT contracts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating proposal section: {e}")
            return self._fallback_proposal_section(section_name, opportunity, profile)
    
    def _build_bid_strategy_prompt(
        self,
        opportunity: Opportunity,
        profile: CapabilityProfile,
        score: OpportunityScore
    ) -> str:
        """Build comprehensive prompt for bid strategy generation."""
        return f"""Analyze this federal contract opportunity and generate a comprehensive bid strategy for {profile.company_name}.

OPPORTUNITY:
Title: {opportunity.title}
Agency: {opportunity.agency}
Sub-Agency: {opportunity.sub_agency or 'N/A'}
Description: {opportunity.description[:1500]}
Domain: {opportunity.primary_domain}
Complexity: {opportunity.complexity}
Project Type: {opportunity.project_type}
Due Date: {opportunity.due_date.strftime('%Y-%m-%d') if opportunity.due_date else 'N/A'}
NAICS: {', '.join(opportunity.naics)}
Set-Aside: {opportunity.set_aside or 'N/A'}

COMPANY PROFILE:
Company: {profile.company_name}
Core Domains: {', '.join(profile.core_domains)}
Technical Skills: {', '.join(profile.technical_skills)}
NAICS Codes: {', '.join(profile.naics)}
Preferred Agencies: {', '.join(profile.preferred_agencies) if profile.preferred_agencies else 'N/A'}
Certifications: {', '.join(profile.certifications) if profile.certifications else 'None'}
Role Preference: {profile.role_preference}
Offices: {', '.join(profile.offices) if profile.offices else 'N/A'}

FIT ANALYSIS:
Overall Fit Score: {score.fit_score}/100
Recommended Action: {score.recommended_action}
Domain Match: {score.breakdown.domain_match}%
NAICS Match: {score.breakdown.naics_match}%
Technical Skills Match: {score.breakdown.technical_skill_match}%
Agency Alignment: {score.breakdown.agency_alignment}%
Risk Factors: {', '.join(score.risk_factors) if score.risk_factors else 'None identified'}

Generate a comprehensive bid strategy with the following sections:

1. WIN THEMES (3-5 key themes that differentiate your company)
2. PROPOSAL OUTLINE (structured outline with main sections)
3. KEY TALKING POINTS (5-7 critical points to emphasize)
4. COMPETITIVE POSITIONING (how to position against competitors)
5. RISK MITIGATION (strategies to address identified risks)
6. EXECUTIVE SUMMARY DRAFT (compelling 200-word executive summary)

Format your response clearly with section headers."""

    def _parse_bid_strategy_response(
        self,
        content: str,
        opportunity: Opportunity,
        profile: CapabilityProfile,
        score: OpportunityScore
    ) -> Dict[str, str]:
        """Parse AI response into structured sections."""
        sections = {
            "win_themes": "",
            "proposal_outline": "",
            "key_talking_points": "",
            "competitive_positioning": "",
            "risk_mitigation": "",
            "executive_summary_draft": ""
        }
        
        # Simple parsing - look for section headers
        current_section = None
        lines = content.split('\n')
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Detect section headers
            if 'win theme' in line_lower or line_lower.startswith('1.'):
                current_section = "win_themes"
            elif 'proposal outline' in line_lower or line_lower.startswith('2.'):
                current_section = "proposal_outline"
            elif 'talking point' in line_lower or line_lower.startswith('3.'):
                current_section = "key_talking_points"
            elif 'competitive' in line_lower or line_lower.startswith('4.'):
                current_section = "competitive_positioning"
            elif 'risk' in line_lower or line_lower.startswith('5.'):
                current_section = "risk_mitigation"
            elif 'executive summary' in line_lower or line_lower.startswith('6.'):
                current_section = "executive_summary_draft"
            
            # Add content to current section
            if current_section and line.strip() and not line.strip().startswith('#'):
                if sections[current_section]:
                    sections[current_section] += "\n" + line
                else:
                    sections[current_section] = line
        
        # If parsing failed, return full content in executive summary
        if not any(sections.values()):
            sections["executive_summary_draft"] = content
        
        return sections
    
    def _fallback_bid_strategy(
        self,
        opportunity: Opportunity,
        profile: CapabilityProfile,
        score: OpportunityScore
    ) -> Dict[str, str]:
        """Fallback bid strategy when AI is not available."""
        return {
            "win_themes": f"""
1. Strong alignment with {opportunity.agency} mission and requirements
2. Proven expertise in {', '.join(profile.core_domains[:3])}
3. Technical capabilities: {', '.join(profile.technical_skills[:5])}
4. Relevant NAICS codes: {', '.join(profile.naics[:3])}
5. {profile.role_preference} contractor experience
""".strip(),
            "proposal_outline": """
1. Executive Summary
2. Understanding of Requirements
3. Technical Approach
4. Management Plan
5. Past Performance
6. Key Personnel
7. Pricing Strategy
""".strip(),
            "key_talking_points": f"""
- Direct match with opportunity requirements in {opportunity.primary_domain}
- Strong technical capabilities: {', '.join(profile.technical_skills[:3])}
- Relevant experience with {opportunity.agency}
- NAICS codes alignment: {', '.join(profile.naics[:2])}
- Fit score: {score.fit_score}/100 indicates strong alignment
""".strip(),
            "competitive_positioning": f"""
Position {profile.company_name} as a specialized {', '.join(profile.core_domains[:2])} provider with deep technical expertise and proven track record in federal contracting.
""".strip(),
            "risk_mitigation": f"""
Address identified risks: {', '.join(score.risk_factors[:3]) if score.risk_factors else 'Standard contract risks'}
""".strip(),
            "executive_summary_draft": f"""
{profile.company_name} is pleased to submit this proposal for {opportunity.title} with {opportunity.agency}. Our company brings extensive experience in {', '.join(profile.core_domains[:2])} and a proven track record of delivering successful federal IT solutions. With a fit score of {score.fit_score}/100, we are well-positioned to meet and exceed the agency's requirements.
""".strip()
        }
    
    def _fallback_proposal_section(
        self,
        section_name: str,
        opportunity: Opportunity,
        profile: CapabilityProfile
    ) -> str:
        """Fallback proposal section when AI is not available."""
        return f"""
{section_name}

{profile.company_name} will approach this {opportunity.primary_domain} opportunity leveraging our core capabilities in {', '.join(profile.core_domains[:2])}. Our technical team brings expertise in {', '.join(profile.technical_skills[:3])} and relevant experience with {opportunity.agency} requirements.

[This is a template section. Enable OpenAI API for AI-generated content.]
""".strip()
    
    def answer_question(
        self,
        question: str,
        opportunity: Opportunity,
        profile: CapabilityProfile,
        score: Optional[OpportunityScore] = None
    ) -> str:
        """
        Answer questions about the opportunity using AI.
        
        Args:
            question: User's question about the opportunity
            opportunity: The opportunity being asked about
            profile: Company capability profile
            score: Optional opportunity score for context
            
        Returns:
            AI-generated answer to the question
        """
        if not self.use_openai:
            return self._fallback_answer(question, opportunity, profile)
        
        try:
            prompt = f"""Answer the following question about this federal contract opportunity. Be specific, accurate, and helpful.

QUESTION: {question}

OPPORTUNITY DETAILS:
Title: {opportunity.title}
Agency: {opportunity.agency}
Sub-Agency: {opportunity.sub_agency or 'N/A'}
Description: {opportunity.description}
Domain: {opportunity.primary_domain}
Complexity: {opportunity.complexity}
Project Type: {opportunity.project_type}
Due Date: {opportunity.due_date.strftime('%Y-%m-%d') if opportunity.due_date else 'Not specified'}
Posted Date: {opportunity.posted_date.strftime('%Y-%m-%d') if opportunity.posted_date else 'N/A'}
NAICS Codes: {', '.join(opportunity.naics) if opportunity.naics else 'N/A'}
Set-Aside: {opportunity.set_aside or 'N/A'}
Contract Type: {opportunity.contract_type or 'N/A'}
Response Type: {opportunity.response_type or 'N/A'}
Place of Performance: {opportunity.place_of_performance or 'N/A'}
URL: {opportunity.url or 'N/A'}

COMPANY CONTEXT:
Company: {profile.company_name}
Core Domains: {', '.join(profile.core_domains)}
Certifications: {', '.join(profile.certifications) if profile.certifications else 'None'}
Role Preference: {profile.role_preference}

{f'FIT SCORE: {score.fit_score}/100' if score else ''}

Provide a clear, specific answer. If information is not available in the opportunity details, say so and suggest where to find it (e.g., "This information is typically found in the full solicitation document on SAM.gov")."""

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert government contracting advisor who helps companies understand federal contract opportunities and submission requirements."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return self._fallback_answer(question, opportunity, profile)
    
    def extract_text_from_pdf(self, pdf_file) -> str:
        """
        Extract text from a PDF file.
        
        Args:
            pdf_file: File-like object or bytes
            
        Returns:
            Extracted text from PDF
        """
        if not PDF_AVAILABLE:
            return "PDF parsing library not available. Please install PyPDF2 or pdfplumber."
        
        try:
            # Try PyPDF2 first
            try:
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
            except:
                # Fallback to pdfplumber
                import pdfplumber
                with pdfplumber.open(pdf_file) as pdf:
                    text = ""
                    for page in pdf.pages:
                        text += page.extract_text() + "\n"
                return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return f"Error extracting text from PDF: {str(e)}"
    
    def summarize_pdf(
        self,
        pdf_text: str,
        opportunity: Opportunity,
        profile: CapabilityProfile
    ) -> str:
        """
        Generate a summary of PDF content using AI.
        
        Args:
            pdf_text: Extracted text from PDF
            opportunity: Related opportunity
            profile: Company profile
            
        Returns:
            AI-generated summary
        """
        if not self.use_openai:
            return f"PDF Summary (AI not available):\n\nFirst 1000 characters:\n{pdf_text[:1000]}..."
        
        try:
            # Truncate if too long (keep first 8000 chars for context)
            truncated_text = pdf_text[:8000] if len(pdf_text) > 8000 else pdf_text
            
            prompt = f"""Summarize this PDF document related to federal contract opportunity: {opportunity.title}

OPPORTUNITY CONTEXT:
Agency: {opportunity.agency}
Domain: {opportunity.primary_domain}

PDF CONTENT:
{truncated_text}

Provide a comprehensive summary that includes:
1. Document Type and Purpose
2. Key Requirements
3. Important Deadlines or Dates
4. Submission Instructions (if applicable)
5. Key Sections/Topics Covered
6. Important Details or Specifications

Format the summary clearly with sections."""

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing government contract documents and extracting key information."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error summarizing PDF: {e}")
            return f"Error generating summary: {str(e)}\n\nPDF Text (first 1000 chars):\n{pdf_text[:1000]}..."
    
    def answer_question_with_pdfs(
        self,
        question: str,
        opportunity: Opportunity,
        profile: CapabilityProfile,
        pdf_texts: List[str],
        score: Optional[OpportunityScore] = None
    ) -> str:
        """
        Answer questions using both opportunity details and uploaded PDF content.
        
        Args:
            question: User's question
            opportunity: The opportunity
            profile: Company profile
            pdf_texts: List of extracted text from uploaded PDFs
            score: Optional opportunity score
            
        Returns:
            AI-generated answer
        """
        if not self.use_openai:
            return self._fallback_answer(question, opportunity, profile)
        
        try:
            # Combine all PDF texts (truncate if too long)
            combined_pdf_text = "\n\n---PDF DOCUMENT SEPARATOR---\n\n".join(pdf_texts)
            if len(combined_pdf_text) > 10000:
                combined_pdf_text = combined_pdf_text[:10000] + "... [truncated]"
            
            prompt = f"""Answer the following question about this federal contract opportunity. Use information from both the opportunity details AND the uploaded PDF documents.

QUESTION: {question}

OPPORTUNITY DETAILS:
Title: {opportunity.title}
Agency: {opportunity.agency}
Sub-Agency: {opportunity.sub_agency or 'N/A'}
Description: {opportunity.description}
Domain: {opportunity.primary_domain}
Due Date: {opportunity.due_date.strftime('%Y-%m-%d') if opportunity.due_date else 'Not specified'}
NAICS Codes: {', '.join(opportunity.naics) if opportunity.naics else 'N/A'}
Set-Aside: {opportunity.set_aside or 'N/A'}
Contract Type: {opportunity.contract_type or 'N/A'}
Response Type: {opportunity.response_type or 'N/A'}
URL: {opportunity.url or 'N/A'}

UPLOADED PDF DOCUMENTS CONTENT:
{combined_pdf_text if combined_pdf_text else 'No PDF documents uploaded.'}

COMPANY CONTEXT:
Company: {profile.company_name}
Core Domains: {', '.join(profile.core_domains)}
Certifications: {', '.join(profile.certifications) if profile.certifications else 'None'}

{f'FIT SCORE: {score.fit_score}/100' if score else ''}

Provide a clear, specific answer based on the PDF documents and opportunity details. If the information is in the PDFs, cite which document it came from. If information is not available, say so and suggest where to find it."""

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert government contracting advisor who helps companies understand federal contract opportunities by analyzing solicitation documents and answering questions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error answering question with PDFs: {e}")
            return self._fallback_answer(question, opportunity, profile)
    
    def _fallback_answer(
        self,
        question: str,
        opportunity: Opportunity,
        profile: CapabilityProfile
    ) -> str:
        """Fallback answer when AI is not available."""
        question_lower = question.lower()
        
        if "amount" in question_lower or "value" in question_lower or "budget" in question_lower:
            return f"The contract amount is not specified in the opportunity details. This information is typically found in the full solicitation document on SAM.gov. Check the official solicitation at: {opportunity.url or 'SAM.gov'} for detailed pricing requirements and contract value."
        
        elif "submit" in question_lower or "submission" in question_lower or "how to" in question_lower:
            return f"""To submit a bid for this opportunity:
1. Review the full solicitation document on SAM.gov: {opportunity.url or 'Visit SAM.gov and search for this opportunity'}
2. Follow the submission instructions in the solicitation (typically found in Section L - Instructions, Conditions, and Notices)
3. Submit by the deadline: {opportunity.due_date.strftime('%Y-%m-%d') if opportunity.due_date else 'Check solicitation for deadline'}
4. Ensure all required documents are included (technical proposal, past performance, pricing, etc.)
5. Submit via the method specified (e.g., email, portal, or hard copy)

For specific submission requirements, refer to the complete solicitation document."""
        
        elif "deadline" in question_lower or "due date" in question_lower or "when" in question_lower:
            return f"The response deadline is: {opportunity.due_date.strftime('%Y-%m-%d at %H:%M') if opportunity.due_date else 'Not specified in opportunity summary. Check the full solicitation document for exact deadline and time.'}"
        
        elif "requirement" in question_lower or "need" in question_lower or "what" in question_lower:
            return f"Key requirements: {opportunity.description[:500]}... For complete requirements, review the full solicitation document at {opportunity.url or 'SAM.gov'}."
        
        else:
            return f"I can help answer questions about this opportunity. For detailed information, please review the full solicitation document at: {opportunity.url or 'SAM.gov'}. Enable OpenAI API for more detailed AI-powered answers."


# Global bid assistant instance
bid_assistant = AIBidAssistant()
