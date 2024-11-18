"""
Base classes for API connectors.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union, List
import aiohttp
from pydantic import BaseModel
import json
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

from ...core.tools import BaseTool
from ...core.errors import APIError

class APIResponse(BaseModel):
    """Standard API response model."""
    status_code: int
    headers: Dict[str, str]
    data: Any
    raw_response: Optional[str] = None

class BaseAPIConnector(BaseTool, ABC):
    """Base class for API connectors."""
    
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: int = 30,
        retry_attempts: int = 3,
        headers: Optional[Dict[str, str]] = None,
    ):
        """Initialize API connector.
        
        Args:
            base_url: Base URL for API
            api_key: Optional API key
            timeout: Request timeout in seconds
            retry_attempts: Number of retry attempts
            headers: Additional headers to include
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self._session: Optional[aiohttp.ClientSession] = None
        self._default_headers = headers or {}
        if api_key:
            self._default_headers['Authorization'] = f'Bearer {api_key}'
        super().__init__()
        
    async def __aenter__(self):
        """Set up session."""
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up session."""
        await self.close()
        
    async def start(self):
        """Start API session."""
        if not self._session:
            self._session = aiohttp.ClientSession(
                base_url=self.base_url,
                headers=self._default_headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
            
    async def close(self):
        """Close API session."""
        if self._session:
            await self._session.close()
            self._session = None
            
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], List[Any]]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> APIResponse:
        """Make API request with retries.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: Request data
            headers: Additional headers
            timeout: Request timeout override
            
        Returns:
            APIResponse object
        """
        if not self._session:
            await self.start()
            
        full_url = f"{self.base_url}/{endpoint.lstrip('/')}"
        request_headers = {**self._default_headers, **(headers or {})}
        
        try:
            async with self._session.request(
                method=method,
                url=endpoint,
                params=params,
                json=data,
                headers=request_headers,
                timeout=timeout or self.timeout
            ) as response:
                response_data = await response.text()
                
                try:
                    data = json.loads(response_data) if response_data else None
                except json.JSONDecodeError:
                    data = response_data
                    
                api_response = APIResponse(
                    status_code=response.status,
                    headers=dict(response.headers),
                    data=data,
                    raw_response=response_data
                )
                
                if not response.ok:
                    raise APIError(
                        f"API request failed: {response.status} - {response_data}",
                        response=api_response
                    )
                    
                return api_response
                
        except aiohttp.ClientError as e:
            raise APIError(f"Request failed: {str(e)}")
            
    async def get(self, endpoint: str, **kwargs) -> APIResponse:
        """Make GET request."""
        return await self._request('GET', endpoint, **kwargs)
        
    async def post(self, endpoint: str, **kwargs) -> APIResponse:
        """Make POST request."""
        return await self._request('POST', endpoint, **kwargs)
        
    async def put(self, endpoint: str, **kwargs) -> APIResponse:
        """Make PUT request."""
        return await self._request('PUT', endpoint, **kwargs)
        
    async def delete(self, endpoint: str, **kwargs) -> APIResponse:
        """Make DELETE request."""
        return await self._request('DELETE', endpoint, **kwargs)
        
    async def patch(self, endpoint: str, **kwargs) -> APIResponse:
        """Make PATCH request."""
        return await self._request('PATCH', endpoint, **kwargs)
        
    @abstractmethod
    async def validate_credentials(self) -> bool:
        """Validate API credentials."""
        pass
        
    @abstractmethod
    async def get_rate_limits(self) -> Dict[str, Any]:
        """Get current rate limit status."""
        pass
