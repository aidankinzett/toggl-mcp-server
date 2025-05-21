"""
Helper functions for Toggl time entries.

This module provides functions for managing Toggl time entries, including
creating, stopping, deleting, and updating time entries, as well as
bulk operations for multiple time entries.
"""

from typing import List, Union, Dict, Any, Optional, Tuple
import datetime
from datetime import timezone, timedelta
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

async def advanced_search_time_entries(
    client: TogglApiClient,
    search_text: Optional[str] = None,
    project_ids: Optional[List[int]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    tags: Optional[List[str]] = None,
    min_duration: Optional[int] = None,
    max_duration: Optional[int] = None,
    billable: Optional[bool] = None,
    case_sensitive: bool = False,
    exact_match: bool = False,
    workspace_id: Optional[int] = None
) -> Union[List[dict], str]:
    """
    Performs advanced search of time entries with multiple filter criteria.
    
    Args:
        client: The Toggl API client
        search_text: Text to search for in time entry descriptions
        project_ids: List of project IDs to filter by
        start_date: Earliest UTC date to include (ISO format)
        end_date: Latest UTC date to include (ISO format)
        tags: List of tags to filter by (entries must have at least one)
        min_duration: Minimum duration in seconds
        max_duration: Maximum duration in seconds
        billable: Filter by billable status
        case_sensitive: Whether text search should be case-sensitive
        exact_match: Whether text should match exactly or as substring
        workspace_id: Optional workspace ID to filter by
        
    Returns:
        List[dict]: List of matching time entries
        str: Error message if search fails
    """
    # Get all time entries
    all_entries = await client.get("/me/time_entries")
    
    if isinstance(all_entries, str):  # Error message
        return f"Failed to retrieve entries: {all_entries}"
    
    # Define filter functions for each criteria
    def _matches_text(entry: dict) -> bool:
        if search_text is None:
            return True
        
        description = entry.get("description", "")
        if not description:
            return False
            
        if not case_sensitive:
            return search_text.lower() in description.lower() if not exact_match else search_text.lower() == description.lower()
        else:
            return search_text in description if not exact_match else search_text == description
    
    def _matches_project(entry: dict) -> bool:
        if project_ids is None:
            return True
        
        entry_project_id = entry.get("project_id")
        if entry_project_id is None:
            return False
            
        return entry_project_id in project_ids
    
    def _in_date_range(entry: dict) -> bool:
        entry_start = entry.get("start")
        if not entry_start:
            return False
            
        in_range = True
        if start_date:
            in_range = in_range and entry_start >= start_date
        if end_date:
            in_range = in_range and entry_start <= end_date
            
        return in_range
    
    def _has_tag(entry: dict) -> bool:
        if tags is None:
            return True
            
        entry_tags = entry.get("tags", [])
        if not entry_tags:
            return False
            
        # Check if any of the requested tags are in the entry's tags
        return any(tag in entry_tags for tag in tags)
    
    def _duration_in_range(entry: dict) -> bool:
        duration = entry.get("duration")
        if duration is None:
            return False
            
        # Handle running time entries (negative duration)
        if duration < 0:
            return True
            
        in_range = True
        if min_duration is not None:
            in_range = in_range and duration >= min_duration
        if max_duration is not None:
            in_range = in_range and duration <= max_duration
            
        return in_range
    
    def _matches_billable(entry: dict) -> bool:
        if billable is None:
            return True
            
        entry_billable = entry.get("billable", False)
        return entry_billable == billable
    
    def _matches_workspace(entry: dict) -> bool:
        if workspace_id is None:
            return True
            
        entry_workspace_id = entry.get("workspace_id")
        return entry_workspace_id == workspace_id
    
    # Apply all filters
    filtered_entries = []
    for entry in all_entries:
        if (
            _matches_text(entry) and
            _matches_project(entry) and
            _in_date_range(entry) and
            _has_tag(entry) and
            _duration_in_range(entry) and
            _matches_billable(entry) and
            _matches_workspace(entry)
        ):
            filtered_entries.append(entry)
    
    return filtered_entries

async def full_text_search(
    client: TogglApiClient,
    query: str,
    search_fields: Optional[List[str]] = None,
    case_sensitive: bool = False
) -> Union[List[dict], str]:
    """
    Performs full-text search across time entries with customizable field searching.
    
    Args:
        client: The Toggl API client
        query: The search text
        search_fields: Fields to search (defaults to ["description"])
        case_sensitive: Whether to use case-sensitive matching
        
    Returns:
        List[dict]: List of matching time entries
        str: Error message if search fails
    """
    # Default to searching only description if not specified
    if search_fields is None:
        search_fields = ["description"] 
    
    # Get all time entries
    all_entries = await client.get("/me/time_entries")
    
    if isinstance(all_entries, str):  # Error message
        return f"Failed to retrieve entries: {all_entries}"
    
    # Define search function
    def _matches_query(entry: dict) -> bool:
        for field in search_fields:
            value = entry.get(field)
            
            # Skip fields that don't exist or aren't strings
            if value is None or not isinstance(value, str):
                continue
                
            if not case_sensitive:
                if query.lower() in value.lower():
                    return True
            else:
                if query in value:
                    return True
                    
        return False
    
    # Filter entries
    return [entry for entry in all_entries if _matches_query(entry)]
    
async def get_work_context(client: TogglApiClient) -> Union[Dict[str, Any], str]:
    """
    Retrieves comprehensive context about the user's current and recent work.
    
    This function gathers information to answer questions like "What am I working on?",
    providing context about the current time entry (if any), recent entries, and
    frequently used projects and tags.
    
    Args:
        client: The Toggl API client
        
    Returns:
        Dict: A dictionary containing work context information
        str: Error message if retrieval fails
    """
    # Get the current time entry
    current_entry = await get_current_time_entry(client)
    
    if isinstance(current_entry, str) and not current_entry.startswith("No active time entry"):
        return f"Error retrieving current time entry: {current_entry}"
        
    # Get recent time entries
    # Calculate time range for recent entries (last 7 days)
    now = datetime.datetime.now(timezone.utc)
    week_ago = now - datetime.timedelta(days=7)
    now_str = tz_converter.format_for_api(now)
    week_ago_str = tz_converter.format_for_api(week_ago)
    
    recent_entries = await get_time_entries_in_range(
        client=client,
        start_time=week_ago_str,
        end_time=now_str
    )
    
    if isinstance(recent_entries, str):
        return f"Error retrieving recent time entries: {recent_entries}"
        
    # Calculate stats
    total_tracked_duration = 0
    project_durations = {}
    project_counts = {}
    tag_counts = {}
    entry_descriptions = set()
    
    for entry in recent_entries:
        # Skip running entries for duration calculations
        duration = entry.get("duration", 0)
        if duration and duration > 0:
            total_tracked_duration += duration
            
            # Project stats
            project_id = entry.get("project_id")
            if project_id:
                project_durations[project_id] = project_durations.get(project_id, 0) + duration
                project_counts[project_id] = project_counts.get(project_id, 0) + 1
                
        # Tag stats
        tags = entry.get("tags", [])
        for tag in tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
        # Add description
        description = entry.get("description")
        if description:
            entry_descriptions.add(description)
    
    # Get project details 
    # We'll need the workspace ID - assume all entries are in the same workspace
    # If there are no recent entries, we'll need to get the default workspace
    workspace_id = None
    if recent_entries and len(recent_entries) > 0:
        first_entry = recent_entries[0]
        workspace_id = first_entry.get("workspace_id")
    
    # Process projects info
    projects_info = {}
    
    if workspace_id:
        # Get all projects in the workspace
        projects_response = await client.get(f"/workspaces/{workspace_id}/projects")
        
        if not isinstance(projects_response, str):
            # Create lookup by ID
            for project in projects_response:
                project_id = project.get("id")
                if project_id in project_durations:
                    projects_info[project_id] = {
                        "name": project.get("name"),
                        "color": project.get("color"),
                        "duration": project_durations.get(project_id, 0),
                        "count": project_counts.get(project_id, 0)
                    }
    
    # Sort data for most common
    most_used_projects = sorted(
        projects_info.values(), 
        key=lambda x: x["duration"], 
        reverse=True
    )[:5]
    
    most_used_tags = sorted(
        [{"tag": tag, "count": count} for tag, count in tag_counts.items()],
        key=lambda x: x["count"],
        reverse=True
    )[:5]
    
    # Calculate totals
    total_hours = total_tracked_duration / 3600  # Convert seconds to hours
    recent_entries_count = len(recent_entries)
    
    # Build complete context
    context = {
        "current_time_entry": current_entry if not isinstance(current_entry, str) else None,
        "current_activity": None if isinstance(current_entry, str) else {
            "description": current_entry.get("description", "No description"),
            "project": None,
            "started_at": current_entry.get("start"),
            "started_at_local": tz_converter.utc_to_local(current_entry.get("start")),
            "duration_so_far": abs(current_entry.get("duration", 0)) if current_entry.get("duration", 0) < 0 else None
        },
        "recent_work_summary": {
            "period": "Last 7 days",
            "total_entries": recent_entries_count,
            "total_hours_tracked": round(total_hours, 2),
            "most_used_projects": most_used_projects,
            "most_used_tags": most_used_tags,
            "distinct_activities": len(entry_descriptions)
        },
        "timezone_info": tz_converter.get_timezone_info(),
    }
    
    return context

async def continue_previous_work(
    client: TogglApiClient,
    time_entry_id: Optional[int] = None,
    description: Optional[str] = None,
    workspace_id: Optional[int] = None
) -> Union[Dict[str, Any], str]:
    """
    Starts a new time entry based on a previous one.
    
    This function allows users to "continue" work they were doing previously
    by creating a new time entry with the same attributes as an existing one.
    The previous entry can be identified by its ID or by its description.
    
    Args:
        client: The Toggl API client
        time_entry_id: ID of the entry to continue (optional)
        description: Description of the entry to continue (optional)
        workspace_id: Workspace ID (required if using description)
        
    Returns:
        Dict: The new time entry that was created
        str: Error message if continuation fails
    """
    # Input validation
    if time_entry_id is None and description is None:
        return "Error: Either time_entry_id or description must be provided"
        
    if description is not None and workspace_id is None:
        return "Error: workspace_id is required when using description to identify the entry"
        
    # Get the entry to continue
    entry_to_continue = None
    
    if time_entry_id is not None:
        # Get all time entries and find the one with matching ID
        all_entries = await client.get("/me/time_entries")
        
        if isinstance(all_entries, str):
            return f"Error retrieving time entries: {all_entries}"
            
        for entry in all_entries:
            if entry.get("id") == time_entry_id:
                entry_to_continue = entry
                break
                
        if entry_to_continue is None:
            return f"Error: No time entry found with ID {time_entry_id}"
            
    else:  # Using description
        # Find entry by description
        entry_id = await get_time_entry_id_by_name(
            client=client,
            time_entry_name=description,
            workspace_id=workspace_id
        )
        
        if isinstance(entry_id, str):  # Error message
            return entry_id
            
        # Get all time entries and find the one with matching ID
        all_entries = await client.get("/me/time_entries")
        
        if isinstance(all_entries, str):
            return f"Error retrieving time entries: {all_entries}"
            
        for entry in all_entries:
            if entry.get("id") == entry_id:
                entry_to_continue = entry
                break
    
    # Extract relevant fields from the previous entry
    if entry_to_continue:
        workspace_id = entry_to_continue.get("workspace_id")
        
        new_entry_data = {
            "description": entry_to_continue.get("description"),
            "tags": entry_to_continue.get("tags"),
            "project_id": entry_to_continue.get("project_id"),
            "billable": entry_to_continue.get("billable", False),
        }
        
        # Start a new entry with the same attributes
        result = await new_time_entry(
            client=client,
            workspace_id=workspace_id,
            description=new_entry_data["description"],
            tags=new_entry_data["tags"],
            project_id=new_entry_data["project_id"],
            billable=new_entry_data["billable"]
        )
        
        if isinstance(result, str):
            return f"Error creating new time entry: {result}"
            
        return {
            "new_time_entry": result[0],
            "continued_from": entry_to_continue,
            "local_time": result[1]
        }
        
    return "Error: Could not find the time entry to continue"

async def resume_time_entry(
    client: TogglApiClient,
    time_entry_id: int
) -> Union[Dict[str, Any], str]:
    """
    Resumes a stopped time entry by creating a new one with the same attributes.
    
    This is similar to continue_previous_work but specifically designed for
    resuming a previously stopped time entry.
    
    Args:
        client: The Toggl API client
        time_entry_id: ID of the entry to resume
        
    Returns:
        Dict: The new time entry that was created
        str: Error message if resumption fails
    """
    # Get all time entries and find the one with matching ID
    all_entries = await client.get("/me/time_entries")
    
    if isinstance(all_entries, str):
        return f"Error retrieving time entries: {all_entries}"
        
    entry_to_resume = None
    for entry in all_entries:
        if entry.get("id") == time_entry_id:
            entry_to_resume = entry
            break
            
    if entry_to_resume is None:
        return f"Error: No time entry found with ID {time_entry_id}"
    
    # Check if the entry is already running (has negative duration)
    if entry_to_resume.get("duration", 0) < 0:
        return f"Error: Time entry with ID {time_entry_id} is already running"
    
    # Start a new entry with the same attributes
    workspace_id = entry_to_resume.get("workspace_id")
    
    result = await new_time_entry(
        client=client,
        workspace_id=workspace_id,
        description=entry_to_resume.get("description"),
        tags=entry_to_resume.get("tags"),
        project_id=entry_to_resume.get("project_id"),
        billable=entry_to_resume.get("billable", False)
    )
    
    if isinstance(result, str):
        return f"Error creating new time entry: {result}"
        
    return {
        "new_time_entry": result[0],
        "resumed_from": entry_to_resume,
        "local_time": result[1]
    }

async def duplicate_time_entry(
    client: TogglApiClient,
    time_entry_id: int,
    start: Optional[str] = None,
    stop: Optional[str] = None
) -> Union[Dict[str, Any], str]:
    """
    Creates an exact duplicate of an existing time entry.
    
    This function creates a new time entry with the same attributes as
    an existing one, but potentially with different start and stop times.
    
    Args:
        client: The Toggl API client
        time_entry_id: ID of the entry to duplicate
        start: Optional new start time (UTC format)
        stop: Optional new stop time (UTC format)
        
    Returns:
        Dict: The duplicated time entry
        str: Error message if duplication fails
    """
    # Get all time entries and find the one with matching ID
    all_entries = await client.get("/me/time_entries")
    
    if isinstance(all_entries, str):
        return f"Error retrieving time entries: {all_entries}"
        
    entry_to_duplicate = None
    for entry in all_entries:
        if entry.get("id") == time_entry_id:
            entry_to_duplicate = entry
            break
            
    if entry_to_duplicate is None:
        return f"Error: No time entry found with ID {time_entry_id}"
    
    # Calculate duration if both start and stop are provided
    duration = entry_to_duplicate.get("duration")
    if start and stop:
        # Let the API calculate the duration
        duration = None
    
    # Create the duplicate entry
    workspace_id = entry_to_duplicate.get("workspace_id")
    
    result = await new_time_entry(
        client=client,
        workspace_id=workspace_id,
        description=entry_to_duplicate.get("description"),
        tags=entry_to_duplicate.get("tags"),
        project_id=entry_to_duplicate.get("project_id"),
        start=start or entry_to_duplicate.get("start"),
        stop=stop or entry_to_duplicate.get("stop"),
        duration=duration,
        billable=entry_to_duplicate.get("billable", False)
    )
    
    if isinstance(result, str):
        return f"Error creating duplicate time entry: {result}"
        
    return {
        "new_time_entry": result[0],
        "duplicated_from": entry_to_duplicate,
        "local_time": result[1]
    }

async def split_time_entry(
    client: TogglApiClient,
    time_entry_id: int,
    split_time: str
) -> Union[Dict[str, Any], str]:
    """
    Splits a time entry into two separate entries at the specified time.
    
    This function takes an existing time entry and splits it into two
    separate entries at the specified split time, maintaining all other
    attributes.
    
    Args:
        client: The Toggl API client
        time_entry_id: ID of the entry to split
        split_time: UTC timestamp where the split should occur
        
    Returns:
        Dict: Information about both resulting time entries
        str: Error message if split fails
    """
    # Get all time entries and find the one with matching ID
    all_entries = await client.get("/me/time_entries")
    
    if isinstance(all_entries, str):
        return f"Error retrieving time entries: {all_entries}"
        
    entry_to_split = None
    for entry in all_entries:
        if entry.get("id") == time_entry_id:
            entry_to_split = entry
            break
            
    if entry_to_split is None:
        return f"Error: No time entry found with ID {time_entry_id}"
    
    # Check if the entry is running (has negative duration)
    if entry_to_split.get("duration", 0) < 0:
        return f"Error: Cannot split a running time entry (ID {time_entry_id})"
    
    # Check if the split time is within the entry's time range
    entry_start = entry_to_split.get("start")
    entry_stop = entry_to_split.get("stop")
    
    if not entry_start or not entry_stop:
        return "Error: Time entry is missing start or stop time"
        
    if split_time <= entry_start or split_time >= entry_stop:
        return f"Error: Split time must be between the entry's start ({entry_start}) and stop ({entry_stop}) times"
    
    # Create two new entries with the split times
    workspace_id = entry_to_split.get("workspace_id")
    
    # First part: from original start to split time
    first_part = await new_time_entry(
        client=client,
        workspace_id=workspace_id,
        description=entry_to_split.get("description"),
        tags=entry_to_split.get("tags"),
        project_id=entry_to_split.get("project_id"),
        start=entry_start,
        stop=split_time,
        billable=entry_to_split.get("billable", False)
    )
    
    if isinstance(first_part, str):
        return f"Error creating first part of split: {first_part}"
    
    # Second part: from split time to original stop
    second_part = await new_time_entry(
        client=client,
        workspace_id=workspace_id,
        description=entry_to_split.get("description"),
        tags=entry_to_split.get("tags"),
        project_id=entry_to_split.get("project_id"),
        start=split_time,
        stop=entry_stop,
        billable=entry_to_split.get("billable", False)
    )
    
    if isinstance(second_part, str):
        return f"Error creating second part of split: {second_part}"
    
    # Delete the original entry
    delete_result = await delete_time_entry(
        client=client,
        time_entry_id=time_entry_id,
        workspace_id=workspace_id
    )
    
    if isinstance(delete_result, str) and not delete_result.startswith("Successfully deleted"):
        return f"Warning: Split succeeded but failed to delete original entry: {delete_result}"
    
    return {
        "first_part": first_part[0],
        "second_part": second_part[0],
        "original_entry": entry_to_split,
        "local_time": first_part[1]
    }

async def bulk_create_time_entries(
    client: TogglApiClient,
    workspace_id: int,
    entries: List[Dict[str, Any]]
) -> Union[Dict[str, Any], str]:
    """
    Creates multiple time entries in a single operation.
    
    Args:
        client: The Toggl API client
        workspace_id: The workspace ID
        entries: List of time entry data dictionaries, each containing:
            - description: Activity being tracked
            - tags: List of tags to associate (optional)
            - project_id: Associated project ID (optional)
            - start: UTC start timestamp (RFC3339)
            - stop: UTC stop timestamp (optional)
            - duration: Duration in seconds (optional, use -1 for running entry)
            - billable: Whether the task is billable (optional)
            
    Returns:
        Dict: Dictionary containing created entries and metadata
        str: Error message on failure
    """
    if workspace_id is None:
        return "Error: workspace_id must be provided to bulk_create_time_entries."
    
    # Process and create entries one by one but handle as a batch
    results = []
    errors = []
    current_local_time = tz_converter.utc_to_local(tz_converter.get_current_utc_time())
    
    for entry_data in entries:
        # Prepare the entry data
        payload = {
            "created_with": "toggl_mcp_server",
            "description": entry_data.get("description"),
            "tags": entry_data.get("tags"),
            "project_id": entry_data.get("project_id"),
            "start": entry_data.get("start"),
            "stop": entry_data.get("stop"),
            "duration": entry_data.get("duration", -1),
            "billable": entry_data.get("billable", False),
            "workspace_id": workspace_id
        }
        
        # If no start time provided, use current time
        if not payload["start"]:
            payload["start"] = tz_converter.get_current_utc_time()
        
        # Create the time entry
        endpoint = f"/workspaces/{workspace_id}/time_entries"
        response = await client.post(endpoint, payload)
        
        if isinstance(response, str):  # Error message
            errors.append({"data": entry_data, "error": response})
        else:
            results.append(response)
    
    # Return combined results
    if errors:
        return {
            "success": results,
            "errors": errors,
            "time": current_local_time
        }
    
    return {
        "entries": results,
        "time": current_local_time
    }

async def bulk_update_time_entries(
    client: TogglApiClient,
    workspace_id: int,
    entries: List[Dict[str, Any]]
) -> Union[Dict[str, Any], str]:
    """
    Updates multiple time entries in a single operation.
    
    Args:
        client: The Toggl API client
        workspace_id: The workspace ID
        entries: List of time entry update data, each containing:
            - id: Time entry ID to update
            - description: Updated description (optional)
            - tags: Updated tags (optional)
            - project_id: Updated project ID (optional)
            - start: Updated start time (optional)
            - stop: Updated stop time (optional)
            - duration: Updated duration (optional)
            - billable: Updated billable status (optional)
            
    Returns:
        Dict: Dictionary containing success and error results
        str: Error message on failure
    """
    if workspace_id is None:
        return "Error: workspace_id must be provided to bulk_update_time_entries."
    
    results = []
    errors = []
    
    for entry_data in entries:
        entry_id = entry_data.get("id")
        if not entry_id:
            errors.append({"data": entry_data, "error": "Missing time entry ID"})
            continue
        
        # Prepare update payload (only include fields to update)
        payload = {
            "created_with": "toggl_mcp_server"
        }
        
        # Add optional fields if they exist
        for field in ["description", "tags", "project_id", "start", "stop", "duration", "billable"]:
            if field in entry_data:
                payload[field] = entry_data[field]
        
        # Update the time entry
        endpoint = f"/workspaces/{workspace_id}/time_entries/{entry_id}"
        response = await client.put(endpoint, payload)
        
        if isinstance(response, str):  # Error message
            errors.append({"id": entry_id, "error": response})
        else:
            results.append(response)
    
    # Return combined results
    if errors:
        return {
            "success": results,
            "errors": errors
        }
    
    return {
        "entries": results
    }

async def bulk_delete_time_entries(
    client: TogglApiClient,
    workspace_id: int,
    time_entry_ids: List[int]
) -> Dict[str, Any]:
    """
    Deletes multiple time entries in a single operation.
    
    Args:
        client: The Toggl API client
        workspace_id: The workspace ID
        time_entry_ids: List of time entry IDs to delete
        
    Returns:
        Dict: Dictionary containing success and error results
    """
    if workspace_id is None:
        return {"error": "Error: workspace_id must be provided to bulk_delete_time_entries."}
    
    results = []
    errors = []
    
    for entry_id in time_entry_ids:
        endpoint = f"/workspaces/{workspace_id}/time_entries/{entry_id}"
        response = await client.delete(endpoint)
        
        if isinstance(response, int):  # Success (HTTP status code)
            results.append({"id": entry_id, "status": response})
        else:  # Error message
            errors.append({"id": entry_id, "error": response})
    
    # Return combined results
    return {
        "success": results,
        "errors": errors,
        "success_count": len(results),
        "error_count": len(errors)
    }