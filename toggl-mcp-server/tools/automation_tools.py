"""
MCP tool definitions for automation features like timer presets and recurring entries.

This module provides MCP tools for managing saved timer presets,
applying those presets, and handling recurring time entries.
"""

from typing import Dict, Any, Optional, List, Union
from mcp.server.fastmcp import FastMCP
from api.client import TogglApiClient
from utils.timezone import tz_converter
from helpers.automation import (
    save_timer_preset as helper_save_timer_preset,
    get_timer_preset as helper_get_timer_preset,
    get_all_presets as helper_get_all_presets,
    delete_timer_preset as helper_delete_timer_preset,
    start_timer_with_preset as helper_start_timer_with_preset,
    create_recurring_entry as helper_create_recurring_entry,
    get_recurring_entry as helper_get_recurring_entry,
    get_all_recurring_entries as helper_get_all_recurring_entries,
    delete_recurring_entry as helper_delete_recurring_entry,
    run_recurring_entry as helper_run_recurring_entry
)
from helpers.projects import get_project_id_by_name
from helpers.workspaces import get_default_workspace_id, get_workspace_id_by_name

def register_automation_tools(mcp: FastMCP, api_client: TogglApiClient):
    """
    Register all automation-related MCP tools.
    
    Args:
        mcp: The FastMCP instance
        api_client: The Toggl API client instance
    """
    
    @mcp.tool()
    async def save_timer_preset(
        name: str,
        description: Optional[str] = None,
        project_name: Optional[str] = None,
        workspace_name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        billable: Optional[bool] = False
    ) -> Union[Dict[str, Any], str]:
        """
        Save a time entry configuration as a preset for future use.

        Time entry presets allow you to save commonly used timer configurations
        and quickly start timers with the same settings later.

        If `workspace_name` is not provided, set it as None.
        
        Args:
            name: Name for the preset (used to identify it later)
            description: Default description for time entries
            project_name: Project to associate with the preset
            workspace_name: Workspace name (defaults to your default workspace)
            tags: List of tags to apply by default
            billable: Whether entries are billable by default
            
        Returns:
            Dict: The saved preset data
            str: Error message if save fails
        """
        result = await helper_save_timer_preset(
            name=name,
            description=description,
            project_name=project_name,
            workspace_name=workspace_name,
            tags=tags,
            billable=billable
        )
        
        if isinstance(result, str):  # Error message
            return result
            
        return {
            "preset": result,
            "status": "saved"
        }
    
    @mcp.tool()
    async def get_timer_preset(name: str) -> Union[Dict[str, Any], str]:
        """
        Retrieve a saved timer preset by name.
        
        Args:
            name: Name of the preset to retrieve
            
        Returns:
            Dict: The preset data
            str: Error message if retrieval fails
        """
        return await helper_get_timer_preset(name)
    
    @mcp.tool()
    async def list_timer_presets() -> Dict[str, Any]:
        """
        Get all saved timer presets.
        
        Lists all timer presets that have been saved, showing their names
        and configurations.
        
        Returns:
            Dict: Object containing all timer presets
        """
        presets = await helper_get_all_presets()
        
        return {
            "presets": presets,
            "count": len(presets)
        }
    
    @mcp.tool()
    async def delete_timer_preset(name: str) -> Union[Dict[str, Any], str]:
        """
        Delete a saved timer preset.
        
        Args:
            name: Name of the preset to delete
            
        Returns:
            Dict: Success information
            str: Error message if deletion fails
        """
        return await helper_delete_timer_preset(name)
    
    @mcp.tool()
    async def start_timer_with_preset(preset_name: str) -> Union[Dict[str, Any], str]:
        """
        Start a new time entry using a saved preset configuration.
        
        This is a convenient way to quickly start tracking time with 
        predefined settings like project, description, and tags.
        
        Args:
            preset_name: Name of the preset to use
            
        Returns:
            Dict: New time entry data
            str: Error message if start fails
        """
        result = await helper_start_timer_with_preset(
            client=api_client,
            preset_name=preset_name
        )
        
        if isinstance(result, str):  # Error message
            return result
            
        # Add local time data
        if "time_entry" in result:
            result["time_entry"] = tz_converter.enrich_time_entry_with_local_times(
                result["time_entry"]
            )
            
        result["timezone_info"] = tz_converter.get_timezone_info()
            
        return result
    
    @mcp.tool()
    async def create_recurring_entry(
        description: str,
        schedule: Dict[str, Any],
        project_name: Optional[str] = None,
        workspace_name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        billable: Optional[bool] = False,
        duration_minutes: Optional[int] = 60
    ) -> Union[Dict[str, Any], str]:
        """
        Create a recurring time entry configuration.
        
        This allows you to define entries that can be automatically 
        created on a recurring schedule. The entry configuration is stored
        but you will need to trigger it manually or via external scheduling.

        If `workspace_name` is not provided, set it as None.
        
        Args:
            description: Description for recurring time entries
            schedule: Dictionary defining recurrence pattern, such as:
                      {"frequency": "weekly", "days": ["Monday", "Wednesday"]}
                      {"frequency": "daily"}
                      {"frequency": "monthly", "day_of_month": 15}
            project_name: Project to associate with the entries
            workspace_name: Workspace name (defaults to default workspace)
            tags: List of tags to apply
            billable: Whether entries are billable
            duration_minutes: Default duration in minutes (default: 60)
            
        Returns:
            Dict: Created recurring entry configuration
            str: Error message if creation fails
        """
        # Convert duration from minutes to seconds
        duration_seconds = duration_minutes * 60
        
        result = await helper_create_recurring_entry(
            client=api_client,
            description=description,
            project_name=project_name,
            workspace_name=workspace_name,
            tags=tags,
            billable=billable,
            schedule=schedule,
            entry_duration=duration_seconds
        )
        
        if isinstance(result, str):  # Error message
            return result
            
        return {
            "recurring_entry": result,
            "status": "created",
            "notes": "This configuration is stored but must be triggered manually or via external scheduling."
        }
    
    @mcp.tool()
    async def list_recurring_entries() -> Dict[str, Any]:
        """
        List all saved recurring entry configurations.
        
        Returns:
            Dict: Object containing all recurring entry configurations
        """
        entries = await helper_get_all_recurring_entries()
        
        return {
            "recurring_entries": entries,
            "count": len(entries)
        }
    
    @mcp.tool()
    async def get_recurring_entry(entry_id: str) -> Union[Dict[str, Any], str]:
        """
        Get a recurring entry configuration by ID.
        
        Args:
            entry_id: ID of the recurring entry to retrieve
            
        Returns:
            Dict: Recurring entry configuration
            str: Error message if retrieval fails
        """
        return await helper_get_recurring_entry(entry_id)
    
    @mcp.tool()
    async def delete_recurring_entry(entry_id: str) -> Union[Dict[str, Any], str]:
        """
        Delete a recurring entry configuration.
        
        Args:
            entry_id: ID of the recurring entry to delete
            
        Returns:
            Dict: Success information
            str: Error message if deletion fails
        """
        return await helper_delete_recurring_entry(entry_id)
    
    @mcp.tool()
    async def run_recurring_entry(
        entry_id: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> Union[Dict[str, Any], str]:
        """
        Manually run a recurring entry configuration to create a time entry.
        
        This creates a time entry based on the saved recurring configuration,
        using either the current time or optional custom start/end times.

        If no times are provided, the entry will start now and use the 
        default duration from the recurring configuration.
        
        Args:
            entry_id: ID of the recurring entry to run
            start_time: Optional custom start time (ISO format in local timezone)
            end_time: Optional custom end time (ISO format in local timezone)
            
        Returns:
            Dict: Created time entry data
            str: Error message if entry creation fails
        """
        result = await helper_run_recurring_entry(
            client=api_client,
            entry_id=entry_id,
            start_time=start_time,
            end_time=end_time
        )
        
        if isinstance(result, str):  # Error message
            return result
            
        # Add local time data
        if "time_entry" in result:
            result["time_entry"] = tz_converter.enrich_time_entry_with_local_times(
                result["time_entry"]
            )
            
        result["timezone_info"] = tz_converter.get_timezone_info()
            
        return result