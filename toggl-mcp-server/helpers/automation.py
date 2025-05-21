"""
Helper functions for automation features like timer presets and recurring entries.

This module provides functions for managing saved timer presets, 
applying those presets, and handling recurring time entries.
"""

import uuid
import datetime
from typing import Dict, Any, Optional, List, Union, Tuple

from api.client import TogglApiClient
from utils.storage import preset_storage
from utils.timezone import tz_converter
from helpers.time_entries import new_time_entry, get_time_entry_id_by_name
from helpers.projects import get_project_id_by_name
from helpers.workspaces import get_workspace_id_by_name, get_default_workspace_id

async def save_timer_preset(
    name: str,
    description: Optional[str] = None,
    project_name: Optional[str] = None,
    workspace_name: Optional[str] = None,
    tags: Optional[List[str]] = None,
    billable: Optional[bool] = None
) -> Union[Dict[str, Any], str]:
    """
    Save a time entry configuration as a preset for future use.
    
    Args:
        name: Name for the preset
        description: Description for timer entries created with this preset
        project_name: Project name for the preset
        workspace_name: Workspace name for the preset
        tags: List of tags to apply
        billable: Whether entries are billable
        
    Returns:
        Dict: Saved preset data
        str: Error message if save fails
    """
    # Create preset data
    preset = {
        "name": name,
        "description": description,
        "project_name": project_name,
        "workspace_name": workspace_name,
        "tags": tags,
        "billable": billable
    }
    
    # Save the preset
    success = preset_storage.save_preset(preset)
    
    if not success:
        return f"Failed to save preset '{name}'"
        
    return preset

async def get_timer_preset(name: str) -> Union[Dict[str, Any], str]:
    """
    Retrieve a saved timer preset by name.
    
    Args:
        name: Name of the preset to retrieve
        
    Returns:
        Dict: Preset data
        str: Error message if retrieval fails
    """
    preset = preset_storage.get_preset(name)
    
    if preset is None:
        return f"No preset found with name '{name}'"
        
    return preset

async def get_all_presets() -> List[Dict[str, Any]]:
    """
    Get all saved timer presets.
    
    Returns:
        List: List of preset data dictionaries
    """
    return preset_storage.get_all_presets()

async def delete_timer_preset(name: str) -> Union[Dict[str, Any], str]:
    """
    Delete a saved timer preset.
    
    Args:
        name: Name of the preset to delete
        
    Returns:
        Dict: Success message
        str: Error message if deletion fails
    """
    success = preset_storage.delete_preset(name)
    
    if not success:
        return f"No preset found with name '{name}' or deletion failed"
        
    return {"success": True, "message": f"Preset '{name}' deleted successfully"}

async def start_timer_with_preset(
    client: TogglApiClient,
    preset_name: str
) -> Union[Dict[str, Any], str]:
    """
    Start a new time entry using a saved preset configuration.
    
    Args:
        client: The Toggl API client
        preset_name: Name of the preset to use
        
    Returns:
        Dict: New time entry data
        str: Error message if start fails
    """
    # Get the preset
    preset = preset_storage.get_preset(preset_name)
    
    if preset is None:
        return f"No preset found with name '{preset_name}'"
    
    # Get workspace ID
    workspace_id = None
    if preset.get("workspace_name"):
        workspace_id = await get_workspace_id_by_name(client, preset["workspace_name"])
        if isinstance(workspace_id, str):  # Error message
            return workspace_id
    else:
        workspace_id = await get_default_workspace_id(client)
        if isinstance(workspace_id, str):  # Error message
            return workspace_id
    
    # Get project ID if specified
    project_id = None
    if preset.get("project_name"):
        project_id = await get_project_id_by_name(
            client, 
            preset["project_name"], 
            workspace_id
        )
        if isinstance(project_id, str):  # Error message
            return project_id
    
    # Start the time entry
    result = await new_time_entry(
        client=client,
        workspace_id=workspace_id,
        description=preset.get("description"),
        tags=preset.get("tags"),
        project_id=project_id,
        billable=preset.get("billable", False)
    )
    
    if isinstance(result, str):  # Error message
        return f"Failed to start timer with preset '{preset_name}': {result}"
    
    return {
        "time_entry": result[0],
        "preset_used": preset,
        "time": result[1]
    }

async def create_recurring_entry(
    client: TogglApiClient,
    description: str,
    project_name: Optional[str] = None,
    workspace_name: Optional[str] = None,
    tags: Optional[List[str]] = None,
    billable: Optional[bool] = False,
    schedule: Dict[str, Any] = None,
    entry_duration: Optional[int] = 3600  # Default to 1 hour
) -> Union[Dict[str, Any], str]:
    """
    Create a recurring time entry configuration.
    
    Args:
        client: The Toggl API client
        description: Description for the recurring time entry
        project_name: Project name for the entry
        workspace_name: Workspace name for the entry
        tags: List of tags to apply
        billable: Whether the entry is billable
        schedule: Dictionary defining recurrence (e.g., "weekly" on "Monday")
        entry_duration: Duration in seconds for each entry
        
    Returns:
        Dict: Created recurring entry configuration
        str: Error message if creation fails
    """
    # Validate schedule
    if not schedule:
        return "Schedule must be provided for recurring entries"
    
    # Get workspace ID
    workspace_id = None
    if workspace_name:
        workspace_id = await get_workspace_id_by_name(client, workspace_name)
        if isinstance(workspace_id, str):  # Error message
            return workspace_id
    else:
        workspace_id = await get_default_workspace_id(client)
        if isinstance(workspace_id, str):  # Error message
            return workspace_id
    
    # Get project ID if specified
    project_id = None
    if project_name:
        project_id = await get_project_id_by_name(
            client, 
            project_name, 
            workspace_id
        )
        if isinstance(project_id, str):  # Error message
            return project_id
    
    # Create recurring entry configuration
    entry_id = str(uuid.uuid4())
    recurring_entry = {
        "id": entry_id,
        "description": description,
        "project_name": project_name,
        "project_id": project_id,
        "workspace_name": workspace_name,
        "workspace_id": workspace_id,
        "tags": tags,
        "billable": billable,
        "schedule": schedule,
        "duration": entry_duration,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "last_run": None
    }
    
    # Save the recurring entry
    success = preset_storage.save_recurring_entry(recurring_entry)
    
    if not success:
        return "Failed to save recurring entry configuration"
        
    return recurring_entry

async def get_recurring_entry(entry_id: str) -> Union[Dict[str, Any], str]:
    """
    Get a recurring entry configuration by ID.
    
    Args:
        entry_id: ID of the recurring entry to retrieve
        
    Returns:
        Dict: Recurring entry configuration
        str: Error message if retrieval fails
    """
    entry = preset_storage.get_recurring_entry(entry_id)
    
    if entry is None:
        return f"No recurring entry found with ID '{entry_id}'"
        
    return entry

async def get_all_recurring_entries() -> List[Dict[str, Any]]:
    """
    Get all saved recurring entry configurations.
    
    Returns:
        List: List of recurring entry configurations
    """
    return preset_storage.get_all_recurring_entries()

async def delete_recurring_entry(entry_id: str) -> Union[Dict[str, Any], str]:
    """
    Delete a recurring entry configuration.
    
    Args:
        entry_id: ID of the recurring entry to delete
        
    Returns:
        Dict: Success message
        str: Error message if deletion fails
    """
    success = preset_storage.delete_recurring_entry(entry_id)
    
    if not success:
        return f"No recurring entry found with ID '{entry_id}' or deletion failed"
        
    return {"success": True, "message": f"Recurring entry deleted successfully"}

async def run_recurring_entry(
    client: TogglApiClient,
    entry_id: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> Union[Dict[str, Any], str]:
    """
    Manually run a recurring entry configuration now.
    
    Args:
        client: The Toggl API client
        entry_id: ID of the recurring entry to run
        start_time: Optional custom start time (ISO format in local timezone)
        end_time: Optional custom end time (ISO format in local timezone)
        
    Returns:
        Dict: Created time entry data
        str: Error message if entry creation fails
    """
    # Get the recurring entry configuration
    entry = preset_storage.get_recurring_entry(entry_id)
    
    if entry is None:
        return f"No recurring entry found with ID '{entry_id}'"
    
    # Prepare timestamps if provided
    final_start = None
    if start_time:
        final_start, _ = tz_converter.local_to_utc(start_time)
    
    final_stop = None
    if end_time:
        final_stop, _ = tz_converter.local_to_utc(end_time)
    
    # Set duration based on whether stop time is provided
    duration = entry.get("duration", 3600)  # Default 1 hour
    if start_time and end_time:
        # Use -1 for running entry if only start is provided
        duration = -1 if not end_time else duration
    
    # Create the time entry
    result = await new_time_entry(
        client=client,
        workspace_id=entry.get("workspace_id"),
        description=entry.get("description"),
        tags=entry.get("tags"),
        project_id=entry.get("project_id"),
        start=final_start,
        stop=final_stop,
        duration=duration,
        billable=entry.get("billable", False)
    )
    
    if isinstance(result, str):  # Error message
        return f"Failed to create time entry from recurring configuration: {result}"
    
    # Update last run timestamp
    entry["last_run"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    preset_storage.save_recurring_entry(entry)
    
    return {
        "time_entry": result[0],
        "recurring_entry": entry,
        "time": result[1]
    }