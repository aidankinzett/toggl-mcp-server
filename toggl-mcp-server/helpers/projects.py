"""
Helper functions for Toggl projects.

This module provides functions for managing Toggl projects, including
creating, deleting, updating, and searching for projects.
"""

from typing import List, Union, Dict, Any, Optional
from api.client import TogglApiClient

async def get_project_id_by_name(
    client: TogglApiClient, 
    project_name: str, 
    workspace_id: int
) -> Union[int, str]:
    """
    Fetches the project ID corresponding to a given project name.
    
    Args:
        client: The Toggl API client
        project_name: The name of the project
        workspace_id: The workspace ID
        
    Returns:
        int: The project ID if found
        str: Error message if not found
    """
    matching_projects = await search_projects_by_name(
        client=client,
        query=project_name,
        workspace_id=workspace_id,
        exact_match=True
    )
    
    if isinstance(matching_projects, str):  # Error message
        return f"Error searching for project: {matching_projects}"
    
    if not matching_projects:
        return f"Project with name '{project_name}' doesn't exist"
    
    # Return the ID of the first (and hopefully only) exact match
    return matching_projects[0].get("id")

async def get_projects_paginated(
    client: TogglApiClient,
    workspace_id: int, 
    page_size: int = 50, 
    active_only: bool = False
) -> Union[List[dict], str]:
    """
    Retrieve projects from the user's Toggl workspace with pagination.

    Args:
        client: The Toggl API client
        workspace_id: ID of the workspace to fetch projects from
        page_size: Number of projects per page (defaults to 50)
        active_only: Whether to fetch only active projects (defaults to False)

    Returns:
        List[dict]: List of project objects
        str: Error message if the request fails
    """
    endpoint = f"/workspaces/{workspace_id}/projects"
    
    # Add query parameters for pagination and filtering
    params = {
        "per_page": page_size
    }
    
    if active_only:
        params["active"] = "true"
    
    all_projects = []
    page = 1
    
    while True:
        params["page"] = page
        response = await client.get(endpoint, params=params)
        
        if isinstance(response, str):  # Error message
            return response
            
        # If the response is empty or not a list, we've reached the end
        if not response or not isinstance(response, list):
            break
            
        all_projects.extend(response)
        
        # If we got fewer projects than the page size, we've reached the end
        if len(response) < page_size:
            break
            
        page += 1
    
    return all_projects

async def search_projects_by_name(
    client: TogglApiClient,
    query: str, 
    workspace_id: int, 
    case_sensitive: bool = False,
    exact_match: bool = False
) -> Union[List[dict], str]:
    """
    Search for Toggl projects by name.

    Args:
        client: The Toggl API client
        query: Search query to match against project names
        workspace_id: ID of the workspace to search in
        case_sensitive: Whether to perform case-sensitive matching (defaults to False)
        exact_match: Whether to require exact name matches (defaults to False)

    Returns:
        List[dict]: List of matching project objects
        str: Error message if the request fails
    """
    projects = await get_projects_paginated(client, workspace_id)
    
    if isinstance(projects, str):  # Error message
        return projects
        
    # Filter projects by name
    matching_projects = []
    for project in projects:
        project_name = project.get("name", "")
        
        if exact_match:
            if case_sensitive:
                if project_name == query:
                    matching_projects.append(project)
            else:
                if project_name.lower() == query.lower():
                    matching_projects.append(project)
        else:
            if case_sensitive:
                if query in project_name:
                    matching_projects.append(project)
            else:
                if query.lower() in project_name.lower():
                    matching_projects.append(project)
    
    return matching_projects

async def create_project(
    client: TogglApiClient,
    name: str,
    workspace_id: int,
    active: Optional[bool] = True,
    billable: Optional[bool] = False,
    client_id: Optional[int] = None,
    color: Optional[str] = None,
    is_private: Optional[bool] = True,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    estimated_hours: Optional[int] = None,
    template: Optional[bool] = False,
    template_id: Optional[int] = None
) -> Union[dict, str]:
    """
    Creates a new project in a Toggl workspace.

    Args:
        client: The Toggl API client
        name: Name of the project to create
        workspace_id: ID of the workspace to create the project in
        active: Whether project is active (defaults to True)
        billable: Whether project is billable (defaults to False)
        client_id: Associated client ID
        color: Project color hex code
        is_private: Whether project is private (defaults to True)
        start_date: Project start date in ISO format
        end_date: Project end date in ISO format
        estimated_hours: Estimated project hours
        template: Whether this is a template (defaults to False)
        template_id: ID of template to use

    Returns:
        dict: Project data on success
        str: Error message on failure
    """
    endpoint = f"/workspaces/{workspace_id}/projects"

    payload = {
        "name": name,
        "active": active,
        "billable": billable,
        "client_id": client_id,
        "color": color,
        "is_private": is_private,
        "start_date": start_date,
        "end_date": end_date,
        "estimated_hours": estimated_hours,
        "template": template,
        "template_id": template_id
    }

    return await client.post(endpoint, payload)

async def delete_project(
    client: TogglApiClient,
    project_id: int, 
    workspace_id: int
) -> Union[int, str]:
    """
    Deletes a project identified by its ID within a specified workspace.

    Args:
        client: The Toggl API client
        project_id: The ID of the project to delete
        workspace_id: The Toggl workspace ID

    Returns:
        int: HTTP status code on successful deletion
        str: Error message if deletion fails
    """
    endpoint = f"/workspaces/{workspace_id}/projects/{project_id}"
    return await client.delete(endpoint)

async def update_projects(
    client: TogglApiClient,
    workspace_id: int,
    project_ids: List[int],
    operations: List[dict]
) -> Union[dict, str]:
    """
    Bulk update multiple projects in a workspace using PATCH operations.

    Args:
        client: The Toggl API client
        workspace_id: ID of the workspace containing the projects
        project_ids: List of project IDs to update
        operations: List of patch operations, each containing:
            - op (str): Operation type ("add", "remove", "replace")
            - path (str): Path to the field (e.g., "/color")
            - value (Any): New value for the field

    Returns:
        dict: Response containing success and failure information
        str: Error message if the request fails
    """
    # Convert project IDs list to comma-separated string
    project_ids_str = ",".join(str(pid) for pid in project_ids)
    
    endpoint = f"/workspaces/{workspace_id}/projects/{project_ids_str}"
    return await client.patch(endpoint, operations)