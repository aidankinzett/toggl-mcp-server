"""
Toggl MCP Server

This is the main entry point for the Toggl MCP server.
It creates an MCP server that provides tools for interacting with Toggl Track.
"""

import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Import modules
from api.client import TogglApiClient
from tools.project_tools import register_project_tools
from tools.time_entry_tools import register_time_entry_tools
from tools.automation_tools import register_automation_tools
from utils.timezone import tz_converter

# Load environment variables
load_dotenv()

# System instructions for MCP
system_instructions = """
<timezone_info>
When using Toggl MCP tools, ALL timestamps provided by you (the agent) should be in the user's LOCAL timezone format (e.g., "2025-05-21T11:15:00"). The MCP server will automatically handle the conversion to UTC for the Toggl API. Similarly, when displaying times to users, always use the local time values provided in fields ending with "_local" or within the "timezone_info" section of responses.
</timezone_info>
"""

def create_mcp_server():
    """
    Create and configure the MCP server with Toggl tools.
    
    Returns:
        FastMCP: The configured MCP server
    """
    # Create MCP server
    mcp = FastMCP("toggl", system_instructions=system_instructions)
    
    # Create API client
    api_client = TogglApiClient()
    
    # Register tools
    register_project_tools(mcp, api_client)
    register_time_entry_tools(mcp, api_client)
    register_automation_tools(mcp, api_client)
    
    # Register resources
    @mcp.resource("toggl:://entities/{workspace_id}/projects")
    async def get_projects(workspace_id: int) -> dict:
        """Retrieve projects within the user's Toggl workspace."""
        url = f"/workspaces/{workspace_id}/projects"
        response = await api_client.get(url)
        
        if isinstance(response, str):
            return {"error": response}
            
        return {"projects": response}

    @mcp.resource("toggl:://me/time_entries")
    async def get_time_entries() -> dict:
        """Retrieve all time entries associated with the authenticated Toggl user."""
        response = await api_client.get("/me/time_entries")
        
        if isinstance(response, str):
            return {"error": response}
            
        return response

    @mcp.resource("toggl:://me/workspaces")
    async def get_workspaces() -> dict:
        """Retrieve all workspaces associated with the authenticated Toggl user."""
        response = await api_client.get("/me/workspaces")
        
        if isinstance(response, str):
            return {"error": response}
            
        return response
    
    return mcp

if __name__ == "__main__":
    mcp = create_mcp_server()
    mcp.run()