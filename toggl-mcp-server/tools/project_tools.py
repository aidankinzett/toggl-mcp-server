"""
MCP tool definitions for Toggl projects.

This module provides MCP tools for managing Toggl projects, including
creating, deleting, updating, and retrieving projects.
"""

from typing import Any, List, Union, Optional, Literal
from mcp.server.fastmcp import FastMCP
from api.client import TogglApiClient
from helpers.projects import (
    get_project_id_by_name,
    create_project as helper_create_project,
    delete_project as helper_delete_project,
    update_projects as helper_update_projects,
    search_projects_by_name,
    get_projects_paginated
)
from helpers.workspaces import get_default_workspace_id, get_workspace_id_by_name

# Toggl colors literal type
TOGGL_COLORS = Literal[
    "#4dc3ff",  # Light Blue
    "#bc85e6",  # Lavender
    "#df7baa",  # Pink
    "#f68d38",  # Orange
    "#b27636",  # Brown
    "#8ab734",  # Lime Green
    "#14a88e",  # Teal
    "#268bb5",  # Medium Blue
    "#6668b4",  # Purple
    "#a4506c",  # Rose
    "#67412c",  # Dark Brown
    "#3c6526",  # Forest Green
    "#094558",  # Navy Blue
    "#bc2d07",  # Red
    "#999999"   # Gray
]

def register_project_tools(mcp: FastMCP, api_client: TogglApiClient):
    """
    Register all project-related MCP tools.
    
    Args:
        mcp: The FastMCP instance
        api_client: The Toggl API client instance
    """
    
    @mcp.tool()
    async def create_project(
        name: str,
        workspace_name: Optional[str] = None,
        active: Optional[bool] = True,
        billable: Optional[bool] = False,
        client_id: Optional[int] = None,
        color: Optional[TOGGL_COLORS] = None,
        is_private: Optional[bool] = True,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        estimated_hours: Optional[int] = None,
        template: Optional[bool] = False,
        template_id: Optional[int] = None
    ) -> Union[dict, str]:
        """
        Creates a new project in a Toggl workspace.

        If `workspace_name` is not provided, set it as None.

        If color is not in TOGGL_COLORS, choose color from TOGGL_COLORS which is
        most similar to the given color.

        Args:
            name (str): Name of the project to create
            workspace_name (str, optional): Name of the workspace. Defaults to user's default workspace.
            active (bool, optional): Whether project is active. Defaults to True
            billable (bool, optional): Whether project is billable. Defaults to False
            client_id (int, optional): Associated client ID
            color (str, optional): Project color hex code from TOGGL_COLORS
            is_private (bool, optional): Whether project is private. Defaults to True
            start_date (str, optional): Project start date in ISO format
            end_date (str, optional): Project end date in ISO format
            estimated_hours (int, optional): Estimated project hours
            template (bool, optional): Whether this is a template. Defaults to False
            template_id (int, optional): ID of template to use

        Returns:
            dict: Project data on success
            str: Error message on failure
        """
        if workspace_name is None:
            workspace_id = await get_default_workspace_id(api_client)
        else:
            workspace_id = await get_workspace_id_by_name(api_client, workspace_name)

        if isinstance(workspace_id, str):  # Error message
            return workspace_id

        response = await helper_create_project(
            client=api_client,
            name=name,
            workspace_id=workspace_id,
            active=active,
            billable=billable,
            client_id=client_id,
            color=color,
            is_private=is_private,
            start_date=start_date,
            end_date=end_date,
            estimated_hours=estimated_hours,
            template=template,
            template_id=template_id
        )

        if isinstance(response, str):  # Error message
            return f"Failed to create project: {response}"
        
        return response

    @mcp.tool()
    async def delete_project(project_name: str, workspace_name: Optional[str] = None) -> str:
        """
        Deletes a Toggl project by its name.

        If `workspace_name` is not provided, set it as None.

            Args:
            project_name (str): The name of the project to delete.
            workspace_name (str, optional): Name of the Toggl workspace. If not provided, defaults to the user's default workspace.

        Returns:
            str: Success message if the project is deleted, or an error message if it fails.
        """
        if workspace_name is None:
            workspace_id = await get_default_workspace_id(api_client)
        else:
            workspace_id = await get_workspace_id_by_name(api_client, workspace_name)

        if isinstance(workspace_id, str):  # Error message
            return workspace_id

        project_id = await get_project_id_by_name(api_client, project_name, workspace_id)
        
        if isinstance(project_id, str):  # Error message
            return project_id
        
        delete_status = await helper_delete_project(api_client, project_id, workspace_id)

        if isinstance(delete_status, int):
            return f"Successfully deleted the project with project_id: {project_id}"
        elif isinstance(delete_status, str) and delete_status == "Project not found/accessible":
            return f"Project with project_id {project_id} was not found or is inaccessible."
        else:
            return f"Failed to delete project {project_id}. Details: {delete_status}"

    @mcp.tool()
    async def update_projects(
        project_names: List[str],
        workspace_name: Optional[str] = None,
        operations: Optional[List[Any]] = None
    ) -> Union[dict, str]:
        """
        Update multiple projects in bulk using PATCH operations.

        If `workspace_name` is not provided, set it as None.

        Args:
            project_names (List[str]): List of project names to update
            workspace_name (str, optional): Name of the workspace. Defaults to user's default workspace.
            operations (List[Any], optional): List of patch operations, each containing:
                - op (str): Operation type ("add", "remove", "replace") 
                - path (str): Path to field (e.g., "/color")
                - value (Any): New value for the field

        Returns:
            dict: Response containing success/failure info for each project
            str: Error message if the operation fails`
        """
        if operations is None:
            return "Error: No operations provided for update."

        if workspace_name is None:
            workspace_id = await get_default_workspace_id(api_client) 
        else:
            workspace_id = await get_workspace_id_by_name(api_client, workspace_name)

        if isinstance(workspace_id, str):  # Error message
            return workspace_id

        project_ids = []
        for name in project_names:
            project_id = await get_project_id_by_name(api_client, name, workspace_id)
            if isinstance(project_id, str):  # Error message
                return f"Error with project '{name}': {project_id}"
            project_ids.append(project_id)

        response = await helper_update_projects(
            client=api_client,
            workspace_id=workspace_id,
            project_ids=project_ids,
            operations=operations
        )

        if isinstance(response, str):
            return f"Failed to update projects: {response}"
            
        return response

    @mcp.tool()
    async def get_all_projects(
        workspace_name: Optional[str] = None,
        active_only: bool = False,
        page_size: int = 50
    ) -> Union[dict, str]:
        """
        Retrieve all projects in the user's Toggl workspace with pagination.

        If `workspace_name` is not provided, the default workspace will be used.

        Args:
            workspace_name (str, optional): Name of the workspace to fetch projects from. 
                                          Defaults to the user's default workspace if None.
            active_only (bool, optional): Whether to fetch only active projects. Defaults to False.
            page_size (int, optional): Number of projects per page. Defaults to 50.
        Returns:
            dict: JSON response containing all projects in the user's workspace.
            str: Error message if the request fails.
        """
        if workspace_name is None:
            workspace_id = await get_default_workspace_id(api_client)
            if isinstance(workspace_id, str): 
                return f"Error fetching default workspace ID: {workspace_id}"
            if workspace_id is None: 
                return "Error: Could not determine default workspace ID."
        else:
            workspace_id = await get_workspace_id_by_name(api_client, workspace_name)

        if isinstance(workspace_id, str):
            return workspace_id 

        projects = await get_projects_paginated(
            client=api_client,
            workspace_id=workspace_id,
            page_size=page_size,
            active_only=active_only
        )

        if isinstance(projects, str):  # Error message
            return f"Error fetching projects for workspace ID {workspace_id}: {projects}"

        return {"projects": projects}

    @mcp.tool()
    async def search_projects(
        query: str,
        workspace_name: Optional[str] = None,
        case_sensitive: bool = False,
        exact_match: bool = False
    ) -> Union[dict, str]:
        """
        Search for projects by name in a Toggl workspace.

        This tool allows you to find projects by their name, supporting both partial and exact matching.
        
        Args:
            query (str): The search term to look for in project names
            workspace_name (str, optional): Name of the workspace to search in. Defaults to user's default workspace.
            case_sensitive (bool, optional): Whether to perform case-sensitive matching. Defaults to False.
            exact_match (bool, optional): Whether to require exact name matches. Defaults to False.

        Returns:
            dict: Object containing matching projects
            str: Error message if the search fails
        """
        if workspace_name is None:
            workspace_id = await get_default_workspace_id(api_client)
        else:
            workspace_id = await get_workspace_id_by_name(api_client, workspace_name)

        if isinstance(workspace_id, str):  # Error message
            return workspace_id
            
        matching_projects = await search_projects_by_name(
            client=api_client,
            query=query,
            workspace_id=workspace_id,
            case_sensitive=case_sensitive,
            exact_match=exact_match
        )
        
        if isinstance(matching_projects, str):  # Error message
            return matching_projects
            
        return {"projects": matching_projects}