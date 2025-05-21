"""
Helper functions for Toggl workspaces.

This module provides functions for managing Toggl workspaces, including
retrieving workspace information and finding workspaces by name.
"""

from typing import Union, Dict, Any, List
from api.client import TogglApiClient

async def get_default_workspace_id(client: TogglApiClient) -> Union[int, str]:
    """
    Retrieve the default workspace ID of the currently authenticated Toggl user.

    Args:
        client: The Toggl API client

    Returns:
        int: The default workspace ID if the request succeeds and the value exists
        str: A descriptive error message if the request fails or the field is missing
    """
    response = await client.get("/me")
    
    if isinstance(response, str):  # Error message
        return f"Failed to fetch default workspace ID: {response}"
        
    default_workspace_id = response.get("default_workspace_id")
    
    if not default_workspace_id:
        return "No default workspace ID found for this user"
        
    return default_workspace_id

async def get_workspace_id_by_name(client: TogglApiClient, workspace_name: str) -> Union[int, str]:
    """
    Retrieve the ID of a workspace based on its name.
    
    Args:
        client: The Toggl API client
        workspace_name: The name of the workspace to search for
        
    Returns:
        int: The ID of the matching workspace, if found
        str: An error message if the workspace is not found or if the fetch fails
    """
    workspaces = await client.get("/me/workspaces")
    
    if isinstance(workspaces, str):  # Error message
        return f"Error fetching workspaces: {workspaces}"
    
    for workspace in workspaces:
        if workspace.get("name") == workspace_name:
            return workspace.get("id")
    
    return f"Workspace with name '{workspace_name}' doesn't exist"

async def get_workspaces(client: TogglApiClient) -> Union[List[Dict[str, Any]], str]:
    """
    Retrieve all workspaces associated with the authenticated Toggl user.
    
    Args:
        client: The Toggl API client
        
    Returns:
        List[Dict[str, Any]]: List of workspace objects
        str: Error message if the fetch fails
    """
    return await client.get("/me/workspaces")