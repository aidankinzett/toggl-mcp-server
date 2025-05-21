"""
Toggl API client for handling HTTP requests and authentication.
"""

import os
import httpx
from base64 import b64encode
from typing import Dict, Any, Optional, Union

class TogglApiClient:
    """
    API client for interacting with the Toggl API.
    
    Handles authentication and provides methods for making
    HTTP requests to the Toggl API endpoints.
    """
    
    BASE_URL = "https://api.track.toggl.com/api/v9"
    
    def __init__(self, api_token: Optional[str] = None, email: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize the Toggl API client with authentication credentials.
        
        Args:
            api_token: Optional Toggl API token for authentication
            email: Optional email for authentication
            password: Optional password for authentication
        
        If api_token is provided, it will be used for authentication.
        Otherwise, email and password must both be provided.
        
        If no arguments are provided, the client will attempt to load credentials
        from environment variables.
        """
        self.api_token = api_token or os.getenv("TOGGL_API_TOKEN")
        self.email = email or os.getenv("EMAIL")
        self.password = password or os.getenv("PASSWORD")
        
        if not self.api_token and not (self.email and self.password):
            raise ValueError("Authentication credentials missing. Please provide either TOGGL_API_TOKEN or both EMAIL and PASSWORD")
        
        # Set up authentication headers
        self.headers = self._get_auth_headers()
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """
        Create authentication headers for Toggl API requests.
        
        Returns:
            Dict containing the necessary headers for API authentication
        """
        if self.api_token:
            auth_credentials = f"{self.api_token}:api_token".encode('utf-8')
        else:
            auth_credentials = f"{self.email}:{self.password}".encode('utf-8')
        
        auth_header = f"Basic {b64encode(auth_credentials).decode('ascii')}"
        
        return {
            "Content-Type": "application/json",
            "Authorization": auth_header
        }
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Union[Dict[str, Any], str]:
        """
        Send a GET request to the Toggl API.
        
        Args:
            endpoint: API endpoint path (e.g., "/me/time_entries")
            params: Optional query parameters
            
        Returns:
            Dict containing the JSON response or a string with an error message
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403:
                    return "User does not have access to this resource."
                elif e.response.status_code == 404:
                    return "Resource not found."
                elif e.response.status_code == 500:
                    return "Internal Server Error"
                return f"HTTP error: {e.response.status_code}"
            except Exception as e:
                return f"Error: {str(e)}"
    
    async def post(self, endpoint: str, data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        Send a POST request to the Toggl API.
        
        Args:
            endpoint: API endpoint path
            data: JSON body data for the request
            
        Returns:
            Dict containing the JSON response or a string with an error message
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        # Remove None values from the payload
        payload = {k: v for k, v in data.items() if v is not None}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=self.headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403:
                    return "User does not have access to this resource."
                elif e.response.status_code == 404:
                    return "Resource not found."
                elif e.response.status_code == 500:
                    return "Internal Server Error"
                return f"HTTP error: {e.response.status_code}"
            except Exception as e:
                return f"Error: {str(e)}"
    
    async def put(self, endpoint: str, data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        Send a PUT request to the Toggl API.
        
        Args:
            endpoint: API endpoint path
            data: JSON body data for the request
            
        Returns:
            Dict containing the JSON response or a string with an error message
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        # Remove None values from the payload
        payload = {k: v for k, v in data.items() if v is not None}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.put(url, json=payload, headers=self.headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403:
                    return "User does not have access to this resource."
                elif e.response.status_code == 404:
                    return "Resource not found."
                elif e.response.status_code == 500:
                    return "Internal Server Error"
                return f"HTTP error: {e.response.status_code}"
            except Exception as e:
                return f"Error: {str(e)}"
    
    async def delete(self, endpoint: str) -> Union[int, str]:
        """
        Send a DELETE request to the Toggl API.
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            HTTP status code on success or a string with an error message
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.delete(url, headers=self.headers)
                response.raise_for_status()
                return response.status_code
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403:
                    return "User does not have access to this resource."
                elif e.response.status_code == 404:
                    return "Resource not found."
                elif e.response.status_code == 500:
                    return "Internal Server Error"
                return f"HTTP error: {e.response.status_code}"
            except Exception as e:
                return f"Error: {str(e)}"
    
    async def patch(self, endpoint: str, data: Dict[str, Any] = None) -> Union[Dict[str, Any], str]:
        """
        Send a PATCH request to the Toggl API.
        
        Args:
            endpoint: API endpoint path
            data: Optional JSON body data for the request
            
        Returns:
            Dict containing the JSON response or a string with an error message
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        async with httpx.AsyncClient() as client:
            try:
                kwargs = {"headers": self.headers}
                if data is not None:
                    kwargs["json"] = data
                
                response = await client.patch(url, **kwargs)
                
                if 200 <= response.status_code < 300:
                    try:
                        return response.json()
                    except Exception:
                        return {"status_code": response.status_code}
                else:
                    if response.status_code == 404:
                        return f"Resource not found: {response.text}"
                    elif response.status_code == 400:
                        return f"Bad Request: {response.text}"
                    else:
                        return f"HTTP error {response.status_code}: {response.text}"
            except httpx.RequestError as req_e:
                return f"Request failed: {req_e}"
            except Exception as e:
                return f"Error: {str(e)}"