"""
SAM.gov API ingestion module.
Pulls federal IT/AI/Data/Cloud/Cyber opportunities from SAM.gov.
"""
import httpx
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dateutil import parser as date_parser

from config import settings
from models import Opportunity

logger = logging.getLogger(__name__)

# IT-focused NAICS codes
IT_NAICS_CODES = [
    "541511",  # Custom Computer Programming Services
    "541512",  # Computer Systems Design Services
    "541513",  # Computer Facilities Management Services
    "541519",  # Other Computer Related Services
    "518210",  # Data Processing, Hosting, and Related Services
    "541330",  # Engineering Services
    "541690",  # Other Scientific and Technical Consulting Services
]

# Keywords for IT/AI/Data/Cloud/Cyber opportunities
IT_KEYWORDS = [
    "artificial intelligence", "AI", "machine learning", "ML", "generative AI",
    "LLM", "large language model", "RAG", "NLP", "computer vision",
    "data engineering", "data warehouse", "data lake", "BI", "business intelligence",
    "analytics", "predictive analytics", "statistical modeling", "SAS", "Python", "R",
    "ETL", "ELT", "data quality", "data governance",
    "cloud", "AWS", "Azure", "GCP", "migration", "cloud-native",
    "container", "Docker", "Kubernetes", "serverless", "Terraform", "IaC",
    "modernization", "legacy", "mainframe",
    "cybersecurity", "zero trust", "FedRAMP", "FISMA", "RMF", "IAM", "SOC", "SIEM",
    "DevOps", "DevSecOps", "CI/CD", "microservices", "API",
    "full-stack", "software development", "application support",
    "IT consulting", "IT operations", "systems integration", "enterprise IT",
    "PMO", "program management", "ITSM", "data center"
]


class SAMIngestion:
    """Handles SAM.gov API data ingestion."""
    
    def __init__(self):
        self.api_key = settings.sam_api_key
        self.base_url = settings.sam_api_base_url
        self.client = httpx.AsyncClient(timeout=60.0)  # Increased timeout for large requests
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
    
    def _parse_place_of_performance(self, pop_data) -> Optional[str]:
        """Parse place of performance from dict or string."""
        if not pop_data:
            return None
        if isinstance(pop_data, str):
            return pop_data
        if isinstance(pop_data, dict):
            # Format: {"city": {...}, "state": {...}, "country": {...}}
            parts = []
            if "city" in pop_data:
                city = pop_data["city"]
                if isinstance(city, dict):
                    parts.append(city.get("name", ""))
                else:
                    parts.append(str(city))
            if "state" in pop_data:
                state = pop_data["state"]
                if isinstance(state, dict):
                    parts.append(state.get("name", ""))
                else:
                    parts.append(str(state))
            if "country" in pop_data:
                country = pop_data["country"]
                if isinstance(country, dict):
                    country_name = country.get("name", "")
                    if country_name and country_name != "UNITED STATES":
                        parts.append(country_name)
            return ", ".join([p for p in parts if p]) or None
        return str(pop_data)
    
    async def _fetch_description(self, description_url: str) -> Optional[str]:
        """
        Fetch full description from the noticedesc endpoint.
        
        NOTE: This endpoint REQUIRES header authentication (X-Api-Key),
        NOT query parameter authentication.
        
        Args:
            description_url: URL to the noticedesc endpoint
            
        Returns:
            Description text or None if fetch fails (silently)
        """
        try:
            if not self.api_key:
                return None
            
            # The noticedesc endpoint REQUIRES header authentication (X-Api-Key)
            # Query parameter authentication returns 500 Internal Server Error
            # Use shorter timeout for description fetching to avoid blocking
            headers = {"X-Api-Key": self.api_key}
            response = await asyncio.wait_for(
                self.client.get(description_url, headers=headers, timeout=5.0),
                timeout=5.0
            )
            
            if response.status_code == 200:
                # The response is JSON with a "description" field
                try:
                    data = response.json()
                    # Extract description from JSON response
                    desc = data.get("description") or data.get("text") or data.get("content")
                    if desc:
                        # Remove HTML tags if present
                        import re
                        desc = re.sub(r'<[^>]+>', '', desc)  # Remove HTML tags
                        return desc[:10000] if desc else None  # Limit length
                    return None
                except Exception as e:
                    logger.debug(f"Error parsing description JSON: {e}")
                    # If not JSON, return as text
                    return response.text[:10000] if response.text else None
            else:
                # Any non-200 status - silently return None
                # Don't log errors - description fetching is optional
                return None
            
        except Exception as e:
            # Silently fail - description fetching is completely optional
            # Don't log or propagate any errors
            return None
    
    def _build_search_params(
        self,
        naics: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        days_ahead: int = 30,
        active_only: bool = True,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Build search parameters for SAM.gov API.
        
        Args:
            naics: List of NAICS codes to filter by
            keywords: List of keywords to search for
            days_ahead: Number of days ahead to search (default: 30)
            active_only: Only return active opportunities
            limit: Maximum number of results
            
        Returns:
            Dictionary of API parameters
        """
        params = {
            "limit": limit,
            "postedFrom": (datetime.now() - timedelta(days=30)).strftime("%m/%d/%Y"),  # Look back 30 days
            "postedTo": (datetime.now() + timedelta(days=days_ahead)).strftime("%m/%d/%Y"),
        }
        
        # Note: API key will be sent as header, not query parameter
        
        if active_only:
            params["active"] = "true"
            # Note: We don't filter by responseDeadline here because the SAM.gov API
            # may not support those parameters. Instead, we filter expired opportunities
            # after parsing in the get_opportunities() method.
        
        if naics:
            params["naics"] = ",".join(naics)
        
        if keywords:
            # SAM.gov API may use different keyword parameter
            params["q"] = " ".join(keywords[:5])  # Limit to avoid URL length issues
        
        return params
    
    async def fetch_opportunities(
        self,
        naics: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        days_ahead: int = 30,
        active_only: bool = True,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch opportunities from SAM.gov API.
        
        Args:
            naics: NAICS codes to filter by (defaults to IT NAICS)
            keywords: Keywords to search (defaults to IT keywords)
            days_ahead: Days ahead to search
            active_only: Only active opportunities
            limit: Max results
            
        Returns:
            List of opportunity dictionaries
        """
        if naics is None:
            naics = IT_NAICS_CODES
        
        if keywords is None:
            keywords = IT_KEYWORDS
        
        # If no API key, return mock data for testing
        if not self.api_key:
            logger.warning("No SAM.gov API key provided. Using mock data for testing.")
            return self._get_mock_opportunities()
        
        params = self._build_search_params(
            naics=naics,
            keywords=keywords,
            days_ahead=days_ahead,
            active_only=active_only,
            limit=limit
        )
        
        try:
            logger.info(f"Fetching opportunities from SAM.gov with params: {params}")
            
            # SAM.gov Opportunities API - try API key as query parameter first
            # (This is the most common format for SAM.gov APIs)
            if self.api_key:
                params["api_key"] = self.api_key
            
            # Try query parameter approach first (this is the standard method)
            response = await self.client.get(
                f"{self.base_url}/search",
                params=params
            )
            
            # Check for authentication errors
            if response.status_code in [401, 403]:
                error_text = response.text
                logger.warning(f"Authentication error ({response.status_code}): {error_text[:200]}")
                
                # If query param failed, try header method
                if self.api_key and "api_key" in params:
                    logger.info("Query parameter auth failed, trying header authentication...")
                    params_without_key = {k: v for k, v in params.items() if k != "api_key"}
                    headers = {"X-Api-Key": self.api_key}
                    response = await self.client.get(
                        f"{self.base_url}/search",
                        params=params_without_key,
                        headers=headers
                    )
                    
                    if response.status_code in [401, 403]:
                        # Check if it's a rate limit or actual auth failure
                        if "rate" in error_text.lower() or "limit" in error_text.lower():
                            logger.warning("Possible rate limiting. Using mock data as fallback.")
                            return self._get_mock_opportunities()
                        else:
                            logger.error(f"SAM.gov API authentication failed. Check your API key.")
                            # Don't raise - return mock data instead
                            return self._get_mock_opportunities()
            
            # Check for rate limiting (429)
            if response.status_code == 429:
                logger.warning("Rate limit exceeded. Using mock data as fallback.")
                return self._get_mock_opportunities()
            
            response.raise_for_status()
            data = response.json()
            
            # SAM.gov API structure may vary - adjust based on actual response
            opportunities = data.get("opportunitiesData", [])
            if not opportunities and isinstance(data, list):
                opportunities = data
            elif not opportunities and isinstance(data, dict):
                # Sometimes the API returns data in a different structure
                opportunities = data.get("data", data.get("results", []))
            
            # Filter for IT opportunities by NAICS codes (post-fetch filtering)
            # The API might return non-IT opportunities that match keywords
            it_opportunities = []
            for opp in opportunities:
                opp_naics = []
                if isinstance(opp, dict):
                    # Extract NAICS codes
                    if opp.get("naicsCodes"):
                        opp_naics = opp["naicsCodes"] if isinstance(opp["naicsCodes"], list) else [opp["naicsCodes"]]
                    elif opp.get("naicsCode"):
                        opp_naics = [opp["naicsCode"]]
                    elif opp.get("naics"):
                        opp_naics = opp["naics"] if isinstance(opp["naics"], list) else [opp["naics"]]
                    
                    # Check if any NAICS matches IT codes
                    if any(naics in IT_NAICS_CODES for naics in opp_naics):
                        # If it has IT NAICS codes, include it (less strict filtering)
                        it_opportunities.append(opp)
                    # Also check if title/description contains IT keywords (even without IT NAICS)
                    elif opp.get("title") or opp.get("description"):
                        title_desc = f"{opp.get('title', '')} {opp.get('description', '')}".lower()
                        it_keywords = [
                            "software", "information technology", "IT", "computer", "system", "data",
                            "artificial intelligence", "AI", "machine learning", "cloud", "cybersecurity",
                            "network", "application", "platform", "database", "analytics", "digital",
                            "automation", "devops", "infrastructure", "enterprise", "solution",
                            "programming", "development", "engineering", "technical", "technology",
                            "web", "mobile", "api", "integration", "support", "maintenance", "services"
                        ]
                        # If it has strong IT keywords, include it
                        if any(kw in title_desc for kw in it_keywords):
                            it_opportunities.append(opp)
                    # If no NAICS and no clear IT keywords, but it came from IT-focused search, include it anyway
                    # (might be a valid IT opportunity with unclear description)
                    elif not opp_naics:
                        # Include opportunities without NAICS if they came from our IT-focused search
                        it_opportunities.append(opp)
            
            if it_opportunities:
                logger.info(f"Filtered to {len(it_opportunities)} IT opportunities from {len(opportunities)} total")
                return it_opportunities
            else:
                logger.warning(f"No IT opportunities found in {len(opportunities)} results. Returning all for review.")
                return opportunities
            
        except httpx.HTTPStatusError as e:
            # Get detailed error response from SAM.gov
            error_detail = "Unknown error"
            try:
                if e.response is not None:
                    error_detail = e.response.text
                    logger.error(f"SAM.gov API error ({e.response.status_code}): {error_detail}")
            except:
                pass
            
            logger.error(f"Error fetching opportunities: {e}")
            
            # If it's an authentication error, don't use mock data - show the error
            if e.response and e.response.status_code in [401, 403]:
                logger.error(f"Authentication failed. Check your API key. Error: {error_detail}")
                raise Exception(f"SAM.gov API authentication failed: {error_detail}")
            
            # Return mock data for other errors
            logger.warning("Returning mock data for development")
            return self._get_mock_opportunities()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching opportunities: {e}")
            logger.warning("Returning mock data for development")
            return self._get_mock_opportunities()
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []
    
    async def _parse_opportunity(self, raw_data: Dict[str, Any]) -> Opportunity:
        """
        Parse raw SAM.gov API response into Opportunity model.
        
        Note: SAM.gov API structure may vary. This is a flexible parser.
        """
        try:
            # Parse dates with fallback
            due_date = None
            if raw_data.get("responseDeadLine"):
                try:
                    due_date = date_parser.parse(raw_data["responseDeadLine"])
                except:
                    pass
            
            posted_date = None
            if raw_data.get("postedDate"):
                try:
                    posted_date = date_parser.parse(raw_data["postedDate"])
                except:
                    pass
            
            # Parse NAICS (may be string, list, or in naicsCode/naicsCodes fields)
            naics = []
            if raw_data.get("naicsCodes"):
                naics = raw_data["naicsCodes"] if isinstance(raw_data["naicsCodes"], list) else [raw_data["naicsCodes"]]
            elif raw_data.get("naicsCode"):
                naics = [raw_data["naicsCode"]] if isinstance(raw_data["naicsCode"], str) else raw_data["naicsCode"]
            elif raw_data.get("naics"):
                if isinstance(raw_data["naics"], list):
                    naics = raw_data["naics"]
                elif isinstance(raw_data["naics"], str):
                    naics = [raw_data["naics"]]
            
            # Extract agency from fullParentPathName (e.g., "DEPT OF DEFENSE.DEPT OF THE NAVY.NAVAIR...")
            agency = "Unknown"
            full_path = raw_data.get("fullParentPathName")
            if full_path:
                # fullParentPathName format: "DEPT OF DEFENSE.DEPT OF THE NAVY.NAVAIR..."
                parts = str(full_path).split(".")
                if parts and parts[0]:
                    agency = parts[0].strip()  # First part is the main agency
                    # Clean up agency name
                    agency = agency.replace("DEPT OF", "DEPARTMENT OF")
            elif raw_data.get("department"):
                agency = str(raw_data["department"]).strip()
            elif raw_data.get("agency"):
                agency = str(raw_data["agency"]).strip()
            
            # Extract sub-agency (second part of fullParentPathName or organization info)
            sub_agency = None
            if full_path:
                parts = str(full_path).split(".")
                if len(parts) > 1:
                    # Use second part as sub-agency (e.g., "DEPT OF THE NAVY")
                    sub_agency = parts[1].strip()
            if not sub_agency:
                sub_agency = raw_data.get("subTier") or raw_data.get("sub_agency")
                if sub_agency:
                    sub_agency = str(sub_agency).strip()
            
            # Description might be a URL pointing to the noticedesc endpoint
            description = raw_data.get("description", "")
            if description and description.startswith("http") and "noticedesc" in description:
                # Try to fetch the actual description from the noticedesc endpoint
                # Note: This is optional - if it fails, we'll use a fallback
                # Skip description fetching if API key issues - use title/type instead
                try:
                    desc_text = await self._fetch_description(description)
                    if desc_text and len(desc_text) > 50:  # Only use if we got substantial content
                        description = desc_text
                    else:
                        # Fallback to title and type if fetch fails or returns minimal content
                        description = f"{raw_data.get('title', '')} - {raw_data.get('type', '')}"
                except Exception as e:
                    # Silently fail - description fetching is optional
                    # Don't log API key errors as they're expected if description endpoint has issues
                    error_msg = str(e).lower()
                    if "api_key" not in error_msg and "invalid" not in error_msg and "401" not in error_msg and "403" not in error_msg:
                        logger.debug(f"Could not fetch description: {e}")
                    # Fallback to title and type
                    description = f"{raw_data.get('title', '')} - {raw_data.get('type', '')}"
            elif description and description.startswith("http"):
                # Other URL, use title and type as description
                description = f"{raw_data.get('title', '')} - {raw_data.get('type', '')}"
            
            # Get URL from uiLink or links
            url = raw_data.get("uiLink") or raw_data.get("url") or raw_data.get("link")
            
            return Opportunity(
                notice_id=raw_data.get("noticeId", raw_data.get("notice_id", "")),
                title=raw_data.get("title", "Untitled"),
                description=description or raw_data.get("title", ""),
                agency=agency,
                sub_agency=sub_agency,
                naics=naics,
                psc=raw_data.get("psc", raw_data.get("productServiceCode", raw_data.get("classificationCode"))),
                set_aside=raw_data.get("typeOfSetAside", raw_data.get("typeOfSetAsideDescription", raw_data.get("set_aside"))),
                contract_type=raw_data.get("contractType", raw_data.get("contract_type")),
                response_type=raw_data.get("type", raw_data.get("baseType", raw_data.get("response_type"))),
                due_date=due_date,
                place_of_performance=self._parse_place_of_performance(raw_data.get("placeOfPerformance", raw_data.get("place_of_performance"))),
                posted_date=posted_date,
                url=url
            )
        except Exception as e:
            logger.error(f"Error parsing opportunity: {e}")
            # Return minimal opportunity
            return Opportunity(
                notice_id=raw_data.get("noticeId", "unknown"),
                title=raw_data.get("title", "Unknown"),
                description=raw_data.get("description", ""),
                agency="Unknown"
            )
    
    async def get_opportunities(
        self,
        naics: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        days_ahead: int = 30,
        active_only: bool = True,
        limit: int = 100
    ) -> List[Opportunity]:
        """
        Get parsed opportunities from SAM.gov.
        
        Returns:
            List of Opportunity models
        """
        raw_opportunities = await self.fetch_opportunities(
            naics=naics,
            keywords=keywords,
            days_ahead=days_ahead,
            active_only=active_only,
            limit=limit
        )
        
        # Parse opportunities (now async to fetch descriptions)
        opportunities = []
        for opp in raw_opportunities:
            parsed = await self._parse_opportunity(opp)
            opportunities.append(parsed)
        
        # Filter out expired opportunities if active_only is True
        if active_only:
            now = datetime.now()
            filtered_opportunities = []
            for opp in opportunities:
                # If no due_date, include it (can't determine if expired)
                if not opp.due_date:
                    filtered_opportunities.append(opp)
                else:
                    # Normalize datetime for comparison (handle timezone-aware vs naive)
                    due_date = opp.due_date
                    # If due_date is timezone-aware, make now timezone-aware too
                    if due_date.tzinfo is not None:
                        from datetime import timezone
                        now_aware = now.replace(tzinfo=timezone.utc) if now.tzinfo is None else now
                        # Only include if due_date is in the future
                        if due_date > now_aware:
                            filtered_opportunities.append(opp)
                        else:
                            logger.debug(f"Filtered out expired opportunity: {opp.notice_id} (due: {due_date})")
                    else:
                        # If due_date is naive, make sure now is also naive
                        now_naive = now.replace(tzinfo=None) if now.tzinfo is not None else now
                        # Only include if due_date is in the future
                        if due_date > now_naive:
                            filtered_opportunities.append(opp)
                        else:
                            logger.debug(f"Filtered out expired opportunity: {opp.notice_id} (due: {due_date})")
            opportunities = filtered_opportunities
        
        return opportunities
    
    def _get_mock_opportunities(self) -> List[Dict[str, Any]]:
        """Generate mock opportunities for development/testing."""
        return [
            {
                "noticeId": "MOCK-001",
                "title": "AI/ML Data Analytics Platform Development",
                "description": "Seeking contractor to develop AI/ML platform for predictive analytics using Python, AWS, and large language models. Must have experience with RAG, NLP, and data engineering.",
                "department": "Department of Defense",
                "subTier": "Air Force",
                "naics": ["541511", "541512"],
                "psc": "D399",
                "typeOfSetAside": "Small Business",
                "contractType": "Fixed Price",
                "type": "RFP",
                "responseDeadLine": (datetime.now() + timedelta(days=45)).isoformat(),
                "postedDate": datetime.now().isoformat(),
                "placeOfPerformance": "Washington, DC",
                "uiLink": None  # Mock data - no real URL
            },
            {
                "noticeId": "MOCK-002",
                "title": "Cloud Migration and Modernization Services",
                "description": "Legacy mainframe to cloud migration project. Requires AWS/Azure expertise, Kubernetes, Terraform, and DevSecOps practices. FedRAMP compliance required.",
                "department": "Department of Homeland Security",
                "naics": ["541512", "541519"],
                "psc": "D399",
                "typeOfSetAside": "8(a)",
                "contractType": "Cost Plus",
                "type": "RFP",
                "responseDeadLine": (datetime.now() + timedelta(days=60)).isoformat(),
                "postedDate": datetime.now().isoformat(),
                "placeOfPerformance": "Remote",
                "uiLink": None  # Mock data - no real URL
            },
            {
                "noticeId": "MOCK-003",
                "title": "Cybersecurity Zero Trust Implementation",
                "description": "Zero Trust architecture implementation with IAM, SOC/SIEM integration, and security automation. FISMA and RMF compliance required.",
                "department": "Department of Defense",
                "subTier": "Navy",
                "naics": ["541511"],
                "psc": "D399",
                "typeOfSetAside": "SDVOSB",
                "contractType": "Time and Materials",
                "type": "RFP",
                "responseDeadLine": (datetime.now() + timedelta(days=30)).isoformat(),
                "postedDate": datetime.now().isoformat(),
                "placeOfPerformance": "Arlington, VA",
                "uiLink": None  # Mock data - no real URL
            }
        ]
