"""
WelcomeKit API Client
Direct API integration for WTTJ bypassing browser automation entirely
Based on: https://developers.welcomekit.co/candidates-api/candidates/create-a-candidate
"""
import httpx
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class WTTJAPIClient:
    """
    Direct API client for WelcomeKit (Welcome to the Jungle)
    Strategy C: ATS API Integration - No browser needed!
    """
    
    BASE_URL = "https://api.welcomekit.co"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize WTTJ API client
        
        Args:
            api_key: WelcomeKit API key (if available)
        """
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=30.0,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }
        )
        
        if api_key:
            self.client.headers['Authorization'] = f'Bearer {api_key}'
    
    async def create_candidate(
        self,
        email: str,
        first_name: str,
        last_name: str,
        phone: Optional[str] = None,
        resume_url: Optional[str] = None,
        linkedin_url: Optional[str] = None,
        cover_letter: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a candidate profile via API
        
        Args:
            email: Candidate email
            first_name: First name
            last_name: Last name
            phone: Phone number
            resume_url: URL to resume/CV
            linkedin_url: LinkedIn profile URL
            cover_letter: Cover letter text
            
        Returns:
            API response with candidate data
        """
        try:
            payload = {
                "candidate": {
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                }
            }
            
            # Add optional fields
            if phone:
                payload["candidate"]["phone"] = phone
            if resume_url:
                payload["candidate"]["resume_url"] = resume_url
            if linkedin_url:
                payload["candidate"]["linkedin_url"] = linkedin_url
            if cover_letter:
                payload["candidate"]["cover_letter"] = cover_letter
            
            # Add any additional fields
            for key, value in kwargs.items():
                if value is not None:
                    payload["candidate"][key] = value
            
            logger.info(f"Creating candidate via API: {email}")
            
            response = await self.client.post("/v1/candidates", json=payload)
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Candidate created successfully via API: {email}")
                return {
                    "success": True,
                    "data": response.json(),
                    "method": "api"
                }
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"API returned {response.status_code}",
                    "details": response.text,
                    "method": "api"
                }
                
        except Exception as e:
            logger.error(f"Failed to create candidate via API: {e}")
            return {
                "success": False,
                "error": str(e),
                "method": "api"
            }
    
    async def apply_to_job(
        self,
        job_reference: str,
        email: str,
        first_name: str,
        last_name: str,
        phone: Optional[str] = None,
        resume_url: Optional[str] = None,
        cover_letter: Optional[str] = None,
        message: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Apply to a job via API
        
        Args:
            job_reference: Job reference/ID
            email: Candidate email
            first_name: First name
            last_name: Last name
            phone: Phone number
            resume_url: URL to resume
            cover_letter: Cover letter
            message: Application message
            
        Returns:
            API response
        """
        try:
            payload = {
                "application": {
                    "job_reference": job_reference,
                    "candidate": {
                        "email": email,
                        "first_name": first_name,
                        "last_name": last_name,
                    }
                }
            }
            
            # Add optional candidate fields
            if phone:
                payload["application"]["candidate"]["phone"] = phone
            if resume_url:
                payload["application"]["candidate"]["resume_url"] = resume_url
            if linkedin_url := kwargs.get("linkedin_url"):
                payload["application"]["candidate"]["linkedin_url"] = linkedin_url
            
            # Add application-specific fields
            if cover_letter:
                payload["application"]["cover_letter"] = cover_letter
            if message:
                payload["application"]["message"] = message
            
            logger.info(f"Applying to job {job_reference} via API for {email}")
            
            response = await self.client.post("/v1/applications", json=payload)
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Application submitted successfully via API")
                return {
                    "success": True,
                    "data": response.json(),
                    "method": "api",
                    "job_reference": job_reference
                }
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"API returned {response.status_code}",
                    "details": response.text,
                    "method": "api"
                }
                
        except Exception as e:
            logger.error(f"Failed to apply via API: {e}")
            return {
                "success": False,
                "error": str(e),
                "method": "api"
            }
    
    async def search_jobs(
        self,
        query: Optional[str] = None,
        location: Optional[str] = None,
        contract_type: Optional[List[str]] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """
        Search for jobs
        
        Args:
            query: Search query
            location: Location filter
            contract_type: Contract types (e.g., ['full_time', 'contract'])
            page: Page number
            per_page: Results per page
            
        Returns:
            Search results
        """
        try:
            params = {
                "page": page,
                "per_page": per_page
            }
            
            if query:
                params["query"] = query
            if location:
                params["location"] = location
            if contract_type:
                params["contract_type"] = ",".join(contract_type)
            
            logger.info(f"Searching jobs via API: {params}")
            
            response = await self.client.get("/v1/jobs", params=params)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Found {len(data.get('jobs', []))} jobs")
                return {
                    "success": True,
                    "data": data,
                    "method": "api"
                }
            else:
                logger.error(f"API error: {response.status_code}")
                return {
                    "success": False,
                    "error": f"API returned {response.status_code}",
                    "method": "api"
                }
                
        except Exception as e:
            logger.error(f"Job search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "method": "api"
            }
    
    async def get_candidate_profile(self, candidate_id: str) -> Dict[str, Any]:
        """Get candidate profile by ID"""
        try:
            response = await self.client.get(f"/v1/candidates/{candidate_id}")
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json(),
                    "method": "api"
                }
            else:
                return {
                    "success": False,
                    "error": f"API returned {response.status_code}",
                    "method": "api"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "method": "api"
            }
    
    async def update_candidate_profile(
        self,
        candidate_id: str,
        **update_fields
    ) -> Dict[str, Any]:
        """Update candidate profile"""
        try:
            payload = {"candidate": update_fields}
            
            response = await self.client.patch(
                f"/v1/candidates/{candidate_id}",
                json=payload
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Profile updated successfully")
                return {
                    "success": True,
                    "data": response.json(),
                    "method": "api"
                }
            else:
                return {
                    "success": False,
                    "error": f"API returned {response.status_code}",
                    "method": "api"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "method": "api"
            }
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


class AlgoliaJobSearchClient:
    """
    Direct access to WTTJ's Algolia-powered job search
    Bypasses web scraping entirely by using their public search API
    """
    
    ALGOLIA_APP_ID = "wttj_production"  # WTTJ's Algolia app ID
    ALGOLIA_API_KEY = "public_key"  # Public search-only key
    ALGOLIA_INDEX = "wttj_cms_jobs_production"
    
    def __init__(self):
        self.base_url = f"https://{self.ALGOLIA_APP_ID}-dsn.algolia.net"
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                'Content-Type': 'application/json',
                'X-Algolia-Application-Id': self.ALGOLIA_APP_ID,
                'X-Algolia-API-Key': self.ALGOLIA_API_KEY,
            }
        )
    
    async def search_jobs(
        self,
        query: str = "",
        location: Optional[str] = None,
        contract_type: Optional[str] = None,
        page: int = 0,
        hits_per_page: int = 20
    ) -> Dict[str, Any]:
        """
        Search WTTJ jobs using Algolia
        
        Args:
            query: Search query (job title, skills, etc.)
            location: Location filter
            contract_type: Contract type filter
            page: Page number (0-indexed)
            hits_per_page: Results per page
            
        Returns:
            Search results
        """
        try:
            # Build filters
            filters = []
            if location:
                filters.append(f'location:"{location}"')
            if contract_type:
                filters.append(f'contract_type:"{contract_type}"')
            
            payload = {
                "params": f"query={query}&page={page}&hitsPerPage={hits_per_page}"
            }
            
            if filters:
                payload["params"] += f"&filters={' AND '.join(filters)}"
            
            logger.info(f"Searching Algolia: {query}")
            
            response = await self.client.post(
                f"/1/indexes/{self.ALGOLIA_INDEX}/query",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Found {data.get('nbHits', 0)} jobs via Algolia")
                return {
                    "success": True,
                    "data": data,
                    "method": "algolia",
                    "total_results": data.get('nbHits', 0),
                    "jobs": data.get('hits', [])
                }
            else:
                logger.error(f"Algolia error: {response.status_code}")
                return {
                    "success": False,
                    "error": f"Algolia returned {response.status_code}",
                    "method": "algolia"
                }
                
        except Exception as e:
            logger.error(f"Algolia search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "method": "algolia"
            }
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Example usage
async def example_api_usage():
    """Example of using WTTJ API client"""
    
    # Option 1: Use WelcomeKit API (if you have API key)
    api_client = WTTJAPIClient(api_key="your_api_key_here")
    
    try:
        # Create candidate profile
        result = await api_client.create_candidate(
            email="john@example.com",
            first_name="John",
            last_name="Developer",
            phone="+33612345678",
            linkedin_url="https://linkedin.com/in/john"
        )
        
        if result["success"]:
            print("✅ Profile created via API!")
            print(result["data"])
        
        # Search jobs
        jobs_result = await api_client.search_jobs(
            query="Python Developer",
            location="Paris",
            contract_type=["full_time"]
        )
        
        if jobs_result["success"]:
            print(f"✅ Found {len(jobs_result['data'].get('jobs', []))} jobs")
        
    finally:
        await api_client.close()
    
    # Option 2: Use Algolia search (no auth needed)
    algolia_client = AlgoliaJobSearchClient()
    
    try:
        # Search jobs directly via Algolia
        result = await algolia_client.search_jobs(
            query="Python",
            location="Paris",
            hits_per_page=20
        )
        
        if result["success"]:
            print(f"✅ Found {result['total_results']} jobs via Algolia")
            for job in result['jobs'][:5]:
                print(f"  - {job.get('name')} at {job.get('organization', {}).get('name')}")
    
    finally:
        await algolia_client.close()


if __name__ == '__main__':
    import asyncio
    asyncio.run(example_api_usage())
