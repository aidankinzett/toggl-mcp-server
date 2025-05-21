"""
MCP tool definitions for Toggl time entries.

This module provides MCP tools for managing Toggl time entries, including
creating, stopping, deleting, updating, and querying time entries.
"""

from typing import List, Union, Optional, Dict, Any
from mcp.server.fastmcp import FastMCP
from api.client import TogglApiClient
from utils.timezone import tz_converter
from helpers.time_entries import (
    get_time_entry_id_by_name,
    new_time_entry as helper_new_time_entry,
    stop_time_entry as helper_stop_time_entry,
    delete_time_entry as helper_delete_time_entry,
    get_current_time_entry as helper_get_current_time_entry,
    update_time_entry as helper_update_time_entry,
    get_time_entries_in_range,
    bulk_create_time_entries as helper_bulk_create_time_entries,
    bulk_update_time_entries as helper_bulk_update_time_entries,
    bulk_delete_time_entries as helper_bulk_delete_time_entries
)
from helpers.projects import get_project_id_by_name
from helpers.workspaces import get_default_workspace_id, get_workspace_id_by_name

def register_time_entry_tools(mcp: FastMCP, api_client: TogglApiClient):
    """
    Register all time entry-related MCP tools.
    
    Args:
        mcp: The FastMCP instance
        api_client: The Toggl API client instance
    """
    
    @mcp.tool()
    async def new_time_entry(
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        project_name: Optional[str] = None,
        start: Optional[str] = None,
        stop: Optional[str] = None,
        duration: Optional[int] = -1,
        billable: Optional[bool] = False,
        workspace_name: Optional[str] = None
    ) -> dict:
        """
        Create a Toggl Track time entry with flexible options for live or past tracking.

        If `workspace_name` is not provided, set it as None.

        Duration is in seconds. Set to -1 for live tracking for the current time entry.
        
        Use this tool to start a new entry (live tracking) or log a completed activity with precise timing.

        Examples:
        - "Track 'Writing docs' starting now"
        - "Log 2 hours spent on 'MCP Server' yesterday tagged ['Toggl', 'backend']"

        Args:
            description (str, optional): What the time entry is about.
            tags (List[str], optional): List of tags (names only).
            project_name (str, optional): Name of the associated project.
            start (str, optional): ISO 8601 start time in local timezone.
            stop (str, optional): ISO 8601 stop time in local timezone.
            duration (int, optional): Duration in seconds. Set to -1 for live tracking.
            billable (bool, optional): Whether this is billable time.
            workspace_name (str, optional): Name of the workspace. Defaults to user's default workspace if omitted.

        Returns:
            dict: Toggl API response on success.
            dict: Error message on failure.
        """
        if workspace_name is None:
            workspace_id = await get_default_workspace_id(api_client)
        else:
            workspace_id = await get_workspace_id_by_name(api_client, workspace_name)

        if isinstance(workspace_id, str):
            return {"error": workspace_id}
        if workspace_id is None: 
            return {"error": "Could not determine workspace ID."}

        project_id = None 
        if project_name is not None:
            project_id_or_error = await get_project_id_by_name(api_client, project_name, workspace_id)
            if isinstance(project_id_or_error, str):
                return {"error": project_id_or_error}
            else:
                project_id = project_id_or_error

        # Convert timestamps from local to UTC format
        debug_info = {"system_timezone": tz_converter.get_timezone_info()["timezone_name"]}
        
        # Convert start time
        final_start_for_api = None
        if start:
            final_start_for_api, start_debug = tz_converter.local_to_utc(start)
            debug_info.update({
                "original_start_input": start,
                "start_conversion": start_debug
            })
        
        # Convert stop time
        final_stop_for_api = None
        if stop:
            final_stop_for_api, stop_debug = tz_converter.local_to_utc(stop)
            debug_info.update({
                "original_stop_input": stop,
                "stop_conversion": stop_debug
            })

        # Call helper with converted timestamps
        toggl_time_entry = await helper_new_time_entry(
            client=api_client,
            workspace_id=workspace_id,
            description=description,
            tags=tags,
            project_id=project_id,
            start=final_start_for_api,
            stop=final_stop_for_api,
            duration=duration if start else -1,  # Pass original duration
            billable=billable
        )

        # Handle response
        if isinstance(toggl_time_entry, str) and toggl_time_entry.startswith("Error:"):
            return {"error": toggl_time_entry, "debug_info": debug_info}
        if not isinstance(toggl_time_entry, tuple) or len(toggl_time_entry) != 2:
            return {"error": f"Unexpected response format from helper_new_time_entry: {toggl_time_entry}", "debug_info": debug_info}

        toggl_time_entry_response, api_call_local_time = toggl_time_entry
        
        return {
            "toggle_time_entry_response": toggl_time_entry_response,
            "api_call_local_time": api_call_local_time,
            "debug_info": debug_info
        }

    @mcp.tool()
    async def stopping_time_entry(time_entry_name: str, workspace_name: Optional[str] = None) -> Union[dict, str]:
        """
        Stop a currently running time entry by name.

        This function looks up the time entry by its description, retrieves its ID, and then calls the Toggl API to stop it.

        If `workspace_name` is not provided, set it as None.

        Args:
            time_entry_name (str): Description of the currently running time entry to stop.
            workspace_name (str, optional): Name of the workspace. Defaults to the user's default workspace.

        Returns:
            dict: JSON response from the Toggl API if successful.
            str: An error message if the request fails or no matching time entry is found.
        """
        if workspace_name is None:
            workspace_id = await get_default_workspace_id(api_client)
        else:
            workspace_id = await get_workspace_id_by_name(api_client, workspace_name)

        if isinstance(workspace_id, str):  # Error message
            return workspace_id
        
        time_entry_id = await get_time_entry_id_by_name(api_client, time_entry_name, workspace_id)

        if isinstance(time_entry_id, str): # Error message
            return time_entry_id

        stopping_time_entry_response = await helper_stop_time_entry(
            client=api_client,
            time_entry_id=time_entry_id, 
            workspace_id=workspace_id
        )

        if isinstance(stopping_time_entry_response, str) and stopping_time_entry_response == "Time entry not found":
            return "Time entry not found!"
        elif isinstance(stopping_time_entry_response, dict):
            # Add local time versions of timestamps
            result = tz_converter.enrich_time_entry_with_local_times(stopping_time_entry_response)
            return result
        else:
            return "ERROR"

    @mcp.tool()
    async def delete_time_entry(time_entry_name: str, workspace_name: Optional[str]=None) -> str:
        """
        Deletes a time entry by its description.

        This permanently removes the time entry from the workspace, so use with caution.

        If `workspace_name` is not provided, set it as None.

        Args:
            time_entry_name (str): Description of the time entry to delete.
            workspace_name (str, optional): Name of the workspace. Defaults to the user's default workspace.

        Returns:
            str: A success message if deleted, or an error string if it fails.
        """
        if workspace_name is None:
            workspace_id = await get_default_workspace_id(api_client)
        else:
            workspace_id = await get_workspace_id_by_name(api_client, workspace_name)

        if isinstance(workspace_id, str):  # Error message
            return workspace_id

        time_entry_id = await get_time_entry_id_by_name(api_client, time_entry_name, workspace_id)
        
        if isinstance(time_entry_id, str):  # Error message
            return time_entry_id
        
        delete_status = await helper_delete_time_entry(
            client=api_client,
            time_entry_id=time_entry_id, 
            workspace_id=workspace_id
        )

        if isinstance(delete_status, int):
            return f"Successfully deleted the time entry with time_entry_id: {time_entry_id}"
        elif isinstance(delete_status, str) and delete_status == "Time Entry not found/accessible":
            return f"Time entry with time_entry_id {time_entry_id} was not found or is inaccessible."
        else:
            return f"Failed to delete time_entry {time_entry_id}. Details: {delete_status}"

    @mcp.tool()
    async def get_current_time_entry() -> Union[dict, str]:
        """
        Fetch the currently running time entry for the authenticated Toggl user.

        This helper function queries the Toggl Track API for the active (i.e., currently ongoing) time entry associated with the authenticated user.
        It is useful for determining what the user is currently working on, displaying real-time status, or stopping/modifying the active session.

        Args:
        - None.

        Returns:
        - `dict`: JSON object describing the currently running time entry, or containing `data: None` if none is active.
        - `str`: Descriptive error message if the request fails due to authorization, connectivity, or internal server errors.
        """
        current_time_entry_data = await helper_get_current_time_entry(api_client)

        if isinstance(current_time_entry_data, str):
            return current_time_entry_data
        
        # Use timezone utility to consistently handle timezone info and conversion
        response = {
            "time_entry": current_time_entry_data,
            "timezone_info": tz_converter.get_timezone_info()
        }
        
        # Add local timezone versions of timestamp fields
        if current_time_entry_data:
            entry = tz_converter.enrich_time_entry_with_local_times(current_time_entry_data)
            response["time_entry"] = entry
        
        return response

    @mcp.tool()
    async def updating_time_entry(
        time_entry_name: str, 
        workspace_name: Optional[str]=None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None, 
        project_id: Optional[int] = None, 
        start: Optional[str] = None, 
        stop: Optional[str] = None,  
        duration: Optional[int] = None,
        billable: Optional[bool] = None
    ) -> Union[dict, str]:
        """
        Update one or more attributes of an existing time entry in the Toggl Track workspace.

        If `workspace_name` is not provided, set it as None.

        Args:
            time_entry_name (str): Description of the time entry to update.
            workspace_name (str, optional): Name of the workspace. Defaults to the user's default.
            description (str, optional): New description.
            tags (List[str], optional): New list of tags.
            project_id (int, optional): New project ID.
            start (str, optional): New start timestamp in local timezone (ISO 8601).
            stop (str, optional): New stop timestamp in local timezone.
            duration (int, optional): Duration in seconds.
            billable (bool, optional): Whether the entry is billable.

        Returns:
            dict: JSON response from Toggl if update is successful.
            str: Error message on failure.
        """
        if workspace_name is None:
            workspace_id = await get_default_workspace_id(api_client)
        else:
            workspace_id = await get_workspace_id_by_name(api_client, workspace_name)

        if isinstance(workspace_id, str):  # Error message
            return workspace_id
        
        time_entry_id = await get_time_entry_id_by_name(api_client, time_entry_name, workspace_id)
        
        if isinstance(time_entry_id, str):  # Error message
            return time_entry_id

        # Convert timestamps from local to UTC format for the API
        debug_info = {"time_entry_id": time_entry_id}
        
        # Convert start time if provided
        api_start = None
        if start:
            api_start, start_debug = tz_converter.local_to_utc(start)
            debug_info["start_conversion"] = start_debug
        
        # Convert stop time if provided
        api_stop = None
        if stop:
            api_stop, stop_debug = tz_converter.local_to_utc(stop)
            debug_info["stop_conversion"] = stop_debug

        response = await helper_update_time_entry(
            client=api_client,
            time_entry_id=time_entry_id,
            workspace_id=workspace_id,
            description=description,
            tags=tags,
            project_id=project_id,
            start=api_start,
            stop=api_stop,
            duration=duration,
            billable=billable
        )

        # If the response is a dictionary, enrich it with local time info
        if isinstance(response, dict):
            response = tz_converter.enrich_time_entry_with_local_times(response)
            response["debug_info"] = debug_info
            response["timezone_info"] = tz_converter.get_timezone_info()

        return response

    @mcp.tool()
    async def get_time_entries_for_range(
        from_day_offset: Optional[int] = 0,
        to_day_offset: Optional[int] = 0,
    ) -> Union[Dict[str, Any], str]:
        """
        Retrieves time entries for the authenticated Toggl user within a specific UTC day range.

        This tool allows you to query all entries from a specific day or over multiple days,
        using day offsets from today.

        Examples:
        - To get entries for today: `from_day_offset=0`, `to_day_offset=0`
        - For yesterday only: `from_day_offset=-1`, `to_day_offset=-1`
        - For the last two days: `from_day_offset=-1`, `to_day_offset=0`

        Args:
            from_day_offset (int, optional): Days offset before today for the start of the range. Defaults to 0 (today).
            to_day_offset (int, optional): Days offset before today for the end of the range. Defaults to 0 (today).

        Returns:
            Dict: Object containing time entries and timezone info
            str: Error message if retrieval or filtering fails.
        """
        from_day_offset = from_day_offset if from_day_offset is not None else 0
        to_day_offset = to_day_offset if to_day_offset is not None else 0

        # Use timezone utility to get date range
        start_time, end_time = tz_converter.get_date_range(from_day_offset)
        if to_day_offset != from_day_offset:
            _, end_time = tz_converter.get_date_range(to_day_offset)

        # Get time entries in the specified range
        entries = await get_time_entries_in_range(
            client=api_client,
            start_time=start_time,
            end_time=end_time
        )

        if isinstance(entries, str):  # Error message
            return entries

        # Use the utility's enrichment function to add local times consistently
        enriched_entries = [tz_converter.enrich_time_entry_with_local_times(entry) for entry in entries]
        
        # Return with consistent timezone info
        return {
            "time_entries": enriched_entries,
            "timezone_info": tz_converter.get_timezone_info()
        }
        
    @mcp.tool()
    async def bulk_create_time_entries(
        entries: List[Dict[str, Any]],
        workspace_name: Optional[str] = None
    ) -> Union[Dict[str, Any], str]:
        """
        Create multiple time entries in one operation. This is useful for batch logging 
        several activities at once.
        
        If `workspace_name` is not provided, set it as None.
        
        Example use cases:
        - Log multiple work segments from a day
        - Import time entries from another system
        - Record multiple similar activities with slight differences
        
        Args:
            entries: List of time entry objects, each containing:
                - description: Activity description (optional)
                - tags: List of tags (optional)
                - project_name: Name of the project (optional)
                - start: Start time in local timezone (optional)
                - stop: Stop time in local timezone (optional)
                - duration: Duration in seconds (optional)
                - billable: Whether entry is billable (optional)
            workspace_name: Name of the workspace (defaults to user's default)
            
        Returns:
            Dict: Results of the bulk creation operation
            str: Error message if the operation fails
        """
        # Get workspace ID
        if workspace_name is None:
            workspace_id = await get_default_workspace_id(api_client)
        else:
            workspace_id = await get_workspace_id_by_name(api_client, workspace_name)
            
        if isinstance(workspace_id, str):
            return workspace_id
            
        # Process entries to convert project names to IDs and timestamps
        processed_entries = []
        for entry in entries:
            processed_entry = entry.copy()
            
            # Convert project name to ID if provided
            if "project_name" in entry and entry["project_name"]:
                project_id = await get_project_id_by_name(
                    api_client, 
                    entry["project_name"], 
                    workspace_id
                )
                
                if isinstance(project_id, str):  # Error 
                    return f"Error with project '{entry['project_name']}': {project_id}"
                    
                processed_entry["project_id"] = project_id
                del processed_entry["project_name"]
                
            # Convert timestamps from local to UTC
            if "start" in entry and entry["start"]:
                utc_start, start_debug = tz_converter.local_to_utc(entry["start"])
                processed_entry["start"] = utc_start
                
            if "stop" in entry and entry["stop"]:
                utc_stop, stop_debug = tz_converter.local_to_utc(entry["stop"])
                processed_entry["stop"] = utc_stop
                
            processed_entries.append(processed_entry)
            
        # Call helper function to create entries
        result = await helper_bulk_create_time_entries(
            client=api_client,
            workspace_id=workspace_id,
            entries=processed_entries
        )
        
        if isinstance(result, str):
            return result
            
        # Enrich response entries with local time
        if "entries" in result:
            result["entries"] = [
                tz_converter.enrich_time_entry_with_local_times(entry)
                for entry in result["entries"]
            ]
            
        if "success" in result:
            result["success"] = [
                tz_converter.enrich_time_entry_with_local_times(entry)
                for entry in result["success"]
            ]
            
        result["timezone_info"] = tz_converter.get_timezone_info()
        return result
        
    @mcp.tool()
    async def bulk_update_time_entries(
        entries: List[Dict[str, Any]],
        workspace_name: Optional[str] = None
    ) -> Union[Dict[str, Any], str]:
        """
        Update multiple time entries at once.
        
        If `workspace_name` is not provided, set it as None.
        
        This is useful for making the same changes to multiple entries or updating
        several entries at once.
        
        Each entry in the list must include either an "id" field or a "description" field
        to identify which time entry to update.
        
        Args:
            entries: List of time entry update objects, each containing:
                - id: Time entry ID to update, or
                - description: Time entry description to identify
                And any of the following fields to update:
                - new_description: New description
                - tags: New list of tags
                - project_name: New project name
                - start: New start time (local timezone)
                - stop: New stop time (local timezone)
                - duration: New duration in seconds
                - billable: New billable status
            workspace_name: Name of workspace (defaults to user's default)
            
        Returns:
            Dict: Results of the bulk update operation
            str: Error message if operation fails
        """
        # Get workspace ID
        if workspace_name is None:
            workspace_id = await get_default_workspace_id(api_client)
        else:
            workspace_id = await get_workspace_id_by_name(api_client, workspace_name)
            
        if isinstance(workspace_id, str):
            return workspace_id
            
        # Process entries to resolve IDs, project names, timestamps
        processed_entries = []
        for entry in entries:
            processed_entry = {}
            
            # Get entry ID either directly or by description
            if "id" in entry:
                processed_entry["id"] = entry["id"]
            elif "description" in entry:
                entry_id = await get_time_entry_id_by_name(
                    api_client,
                    entry["description"],
                    workspace_id
                )
                
                if isinstance(entry_id, str):  # Error
                    return f"Error identifying entry '{entry['description']}': {entry_id}"
                    
                processed_entry["id"] = entry_id
            else:
                return "Each entry must contain either 'id' or 'description' to identify the time entry"
                
            # Handle description update
            if "new_description" in entry:
                processed_entry["description"] = entry["new_description"]
                
            # Copy over simple fields
            for field in ["tags", "duration", "billable"]:
                if field in entry:
                    processed_entry[field] = entry[field]
                    
            # Convert project name to ID if provided
            if "project_name" in entry:
                project_id = await get_project_id_by_name(
                    api_client,
                    entry["project_name"],
                    workspace_id
                )
                
                if isinstance(project_id, str):  # Error
                    return f"Error with project '{entry['project_name']}': {project_id}"
                    
                processed_entry["project_id"] = project_id
                
            # Convert timestamps from local to UTC
            if "start" in entry:
                utc_start, _ = tz_converter.local_to_utc(entry["start"])
                processed_entry["start"] = utc_start
                
            if "stop" in entry:
                utc_stop, _ = tz_converter.local_to_utc(entry["stop"])
                processed_entry["stop"] = utc_stop
                
            processed_entries.append(processed_entry)
            
        # Call helper function to update entries
        result = await helper_bulk_update_time_entries(
            client=api_client,
            workspace_id=workspace_id,
            entries=processed_entries
        )
        
        if isinstance(result, str):
            return result
            
        # Enrich response entries with local time
        if "entries" in result:
            result["entries"] = [
                tz_converter.enrich_time_entry_with_local_times(entry)
                for entry in result["entries"]
            ]
            
        if "success" in result:
            result["success"] = [
                tz_converter.enrich_time_entry_with_local_times(entry)
                for entry in result["success"]
            ]
            
        result["timezone_info"] = tz_converter.get_timezone_info()
        return result
        
    @mcp.tool()
    async def bulk_delete_time_entries(
        entry_identifiers: List[Union[int, str]],
        are_descriptions: bool = False,
        workspace_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delete multiple time entries in one operation.
        
        If `workspace_name` is not provided, set it as None.
        
        This allows you to remove multiple entries at once, either by their IDs
        or by their descriptions.
        
        Args:
            entry_identifiers: List of time entry IDs or descriptions
            are_descriptions: Whether the identifiers are descriptions (True) or IDs (False)
            workspace_name: Name of workspace (defaults to user's default)
            
        Returns:
            Dict: Results of the deletion operation
        """
        # Get workspace ID
        if workspace_name is None:
            workspace_id = await get_default_workspace_id(api_client)
        else:
            workspace_id = await get_workspace_id_by_name(api_client, workspace_name)
            
        if isinstance(workspace_id, str):
            return {"error": workspace_id}
            
        # Convert descriptions to IDs if needed
        entry_ids = []
        if are_descriptions:
            for description in entry_identifiers:
                entry_id = await get_time_entry_id_by_name(
                    api_client,
                    description,
                    workspace_id
                )
                
                if isinstance(entry_id, str):  # Error
                    return {"error": f"Error identifying entry '{description}': {entry_id}"}
                    
                entry_ids.append(entry_id)
        else:
            # Assume the identifiers are already IDs
            entry_ids = [int(id) for id in entry_identifiers]
            
        # Call helper function to delete entries
        result = await helper_bulk_delete_time_entries(
            client=api_client,
            workspace_id=workspace_id,
            time_entry_ids=entry_ids
        )
        
        return result