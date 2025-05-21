"""
Helper functions for Toggl time entries.

This module provides functions for managing Toggl time entries, including
creating, stopping, deleting, and updating time entries.
"""

from typing import List, Union, Dict, Any, Optional, Tuple
from api.client import TogglApiClient
from utils.timezone import tz_converter

async def get_time_entry_id_by_name(
    client: TogglApiClient,
    time_entry_name: str, 
    workspace_id: int
) -> Union[int, str]:
    """
    Retrieve the ID of a time entry based on an exact match of its description.

    Args:
        client: The Toggl API client
        time_entry_name: The exact description of the time entry
        workspace_id: The Toggl workspace to search in

    Returns:
        int: The ID of the matching time entry, if found
        str: An error message if the entry is not found or if the fetch fails
    """
    time_entries_response = await client.get("/me/time_entries")

    if isinstance(time_entries_response, str):  # Error message
        return f"Error fetching time entries: {time_entries_response}"
    
    for time_entry in time_entries_response:
        if time_entry.get("description") == time_entry_name:
            return time_entry.get("id")
        
    return f"Time entry with name '{time_entry_name}' doesn't exist"

async def new_time_entry(
    client: TogglApiClient,
    workspace_id: int,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    project_id: Optional[int] = None,
    start: Optional[str] = None,
    stop: Optional[str] = None,
    duration: Optional[int] = -1,
    billable: Optional[bool] = False
) -> Union[Tuple[dict, str], str]:
    """
    Creates a new Toggl time entry with flexible support for running or completed tasks.

    Args:
        client: The Toggl API client
        workspace_id: The workspace ID
        description: Activity being tracked
        tags: List of tags to associate
        project_id: Associated project ID
        start: UTC start timestamp (RFC3339)
        stop: UTC stop timestamp
        duration: Duration in seconds (use -1 for running entry)
        billable: Whether the task is billable

    Returns:
        Tuple[dict, str]: API response and system-local time
        str: Error message on failure
    """
    if workspace_id is None:
        return "Error: workspace_id must be provided to new_time_entry."
    
    endpoint = f"/workspaces/{workspace_id}/time_entries"

    current_iso_time = tz_converter.get_current_utc_time()
    current_local_time = tz_converter.utc_to_local(current_iso_time)

    payload = {
        "created_with": "toggl_mcp_server",
        "description": description,
        "tags": tags,
        "project_id": project_id,
        "start": start if start else current_iso_time,
        "stop": stop,
        "duration": duration,
        "billable": billable,
        "workspace_id": workspace_id
    }

    response = await client.post(endpoint, payload)
    
    if isinstance(response, str):  # Error message
        return response
        
    return response, current_local_time

async def stop_time_entry(
    client: TogglApiClient,
    time_entry_id: int, 
    workspace_id: int
) -> Union[dict, str]:
    """
    Stops a running Toggl time entry by its ID.

    Args:
        client: The Toggl API client
        time_entry_id: The unique ID of the time entry to stop
        workspace_id: The Toggl workspace ID the time entry belongs to

    Returns:
        dict: JSON response from the Toggl API if successful
        str: An error message if the request fails
    """
    endpoint = f"/workspaces/{workspace_id}/time_entries/{time_entry_id}/stop"
    return await client.patch(endpoint)

async def delete_time_entry(
    client: TogglApiClient,
    time_entry_id: int, 
    workspace_id: int
) -> Union[int, str]:
    """
    Deletes a specific time entry from the Toggl Track workspace.

    Args:
        client: The Toggl API client
        time_entry_id: The unique ID of the time entry to be deleted
        workspace_id: The Toggl workspace in which the time entry resides

    Returns:
        int: HTTP status code if the deletion is successful
        str: An error message if deletion fails
    """
    endpoint = f"/workspaces/{workspace_id}/time_entries/{time_entry_id}"
    return await client.delete(endpoint)

async def get_current_time_entry(client: TogglApiClient) -> Union[dict, str]:
    """
    Fetch the currently running time entry for the authenticated Toggl user.

    Args:
        client: The Toggl API client

    Returns:
        dict: JSON object describing the currently running time entry
        str: Error message if the request fails
    """
    endpoint = "/me/time_entries/current"
    return await client.get(endpoint)

async def update_time_entry(
    client: TogglApiClient,
    time_entry_id: int,
    workspace_id: int, 
    description: Optional[str] = None,
    tags: Optional[List[str]] = None, 
    project_id: Optional[int] = None, 
    start: Optional[str] = None, 
    stop: Optional[str] = None,  
    duration: Optional[int] = None,
    billable: Optional[bool] = None
) -> Union[dict, str]:
    """
    Updates attributes of an existing time entry in the Toggl Track workspace.

    Args:
        client: The Toggl API client
        time_entry_id: Unique identifier of the time entry to update
        workspace_id: Toggl workspace ID
        description: Updated description of the activity
        tags: Updated list of tag names
        project_id: ID of the new associated project
        start: ISO 8601 UTC timestamp for the new start time
        stop: ISO 8601 UTC timestamp for the new stop time
        duration: Duration in seconds
        billable: Flag indicating whether the entry is billable

    Returns:
        dict: JSON response from Toggl if the update succeeds
        str: Error message if the update fails
    """
    endpoint = f"/workspaces/{workspace_id}/time_entries/{time_entry_id}"

    payload = {
        "created_with": "toggl_mcp_server",
        "description": description,
        "tags": tags,
        "project_id": project_id,
        "start": start,
        "stop": stop,
        "duration": duration,
        "billable": billable,
    }

    return await client.put(endpoint, payload)

async def get_time_entries_in_range(
    client: TogglApiClient,
    start_time: str,
    end_time: str
) -> Union[List[dict], str]:
    """
    Retrieves time entries within a specified date range.

    Args:
        client: The Toggl API client
        start_time: UTC start timestamp in ISO format
        end_time: UTC end timestamp in ISO format

    Returns:
        List[dict]: List of time entries within the specified range
        str: Error message if retrieval fails
    """
    all_entries = await client.get("/me/time_entries")

    if isinstance(all_entries, str):  # Error message
        return f"Failed to retrieve entries: {all_entries}"

    def _in_range(entry: dict) -> bool:
        entry_start = entry.get("start")
        if entry_start is None:
            return False 
        return start_time <= entry_start <= end_time

    return [entry for entry in all_entries if _in_range(entry)]