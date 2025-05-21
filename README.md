# Toggl MCP Server

Allows MCP clients to interact with Toggl Track, enabling time tracking, project management, and workspace operations through natural language.

## Features

The Toggl MCP Server provides a comprehensive set of tools for interacting with Toggl Track through the Model Context Protocol. Key capabilities include:

- **Project Management**: Create, update, delete, and query projects
- **Time Entry Operations**: Start, stop, update, query, and manage time entries
- **Bulk Operations**: Perform operations on multiple time entries at once
- **Advanced Search**: Find time entries with powerful filtering and full-text search
- **Context-Aware Tools**: Get rich information about your current work context
- **Automation**: Save and apply timer presets and recurring entry configurations
- **Convenience Functions**: Quickly resume, duplicate, or split time entries

### Tools

#### Project Management

- **create_project**

  - **Description**: Creates a new project in a specified Toggl workspace.
  - **Input**:
    - `name` (str): The name of the project to be created. This is a required field.
    - `workspace_name` (str, optional): The name of the workspace where the project will be created. If not provided, it defaults to the user's default workspace.
    - `active` (bool, optional): Specifies whether the project is active. Defaults to `True`.
    - `billable` (bool, optional): Specifies whether the project is billable. Defaults to `False`.
    - `client_id` (int, optional): The ID of the client associated with the project.
    - `color` (str, optional): The hex color code assigned to the project (e.g., "#FF0000").
    - `is_private` (bool, optional): Specifies whether the project is private. Defaults to `True`.
    - `start_date` (str, optional): The start date of the project in ISO 8601 format (e.g., "YYYY-MM-DD").
    - `end_date` (str, optional): The end date of the project in ISO 8601 format (e.g., "YYYY-MM-DD").
    - `estimated_hours` (int, optional): The estimated number of hours for the project.
    - `template` (bool, optional): Specifies whether the project is a template. Defaults to `False`.
    - `template_id` (int, optional): The ID of the template to use for creating the project.
  - **Output**: JSON response containing the data of the newly created project.

- **delete_project**

  - **Description**: Deletes a project identified by its name within a specified workspace.
  - **Input**:
    - `project_name` (str): The exact name of the project to be deleted. This is a required field.
    - `workspace_name` (str, optional): The name of the workspace containing the project. If not provided, it defaults to the user's default workspace.
  - **Output**: A confirmation message (str) indicating the successful deletion of the project.

- **update_projects**

  - **Description**: Performs bulk updates on multiple projects within a specified workspace using patch operations.
  - **Input**:
    - `project_names` (List[str]): A list containing the names of the projects to be updated. This is a required field.
    - `operations` (List[dict]): A list of patch operations to apply to the selected projects. Each operation is a dictionary specifying the operation type (`op`), the field path (`path`), and the new value (`value`) (e.g., `{"op": "replace", "path": "/active", "value": false}`). This is a required field.
    - `workspace_name` (str, optional): The name of the workspace containing the projects. If not provided, it defaults to the user's default workspace.
  - **Output**: JSON response containing the data of the updated projects.

- **get_all_projects**
  - **Description**: Retrieves a list of all projects within a specified workspace.
  - **Input**:
    - `workspace_name` (str, optional): The name of the workspace from which to retrieve projects. If not provided, it defaults to the user's default workspace.
  - **Output**: JSON response containing a list of project data objects found in the specified workspace.

#### Time Entry Management

- **new_time_entry**

  - **Description**: Creates a new time entry. Can be used to start a timer (if only `start` is provided or neither `start` nor `duration` are provided) or log a completed time entry (if `start` and `stop`, or `start` and `duration` are provided).
  - **Input**:
    - `description` (str): The description for the time entry.
    - `workspace_name` (str, optional): Name of the workspace. Defaults to the user's default workspace.
    - `project_name` (str, optional): Name of the project to associate the time entry with.
    - `tags` (List[str], optional): A list of tag names to apply to the time entry.
    - `start` (str, optional): The start time of the entry in local timezone format (e.g., "2023-10-26T10:00:00"). Defaults to the current time if creating a running entry.
    - `stop` (str, optional): The stop time of the entry in local timezone format. If provided, creates a completed entry.
    - `duration` (int, optional): The duration of the entry in seconds. If `start` is provided but `stop` is not, `duration` determines the stop time. If `start` is not provided, a negative duration starts a running timer.
    - `billable` (bool, optional): Whether the time entry should be marked as billable. Defaults to False.
  - **Output**: JSON response containing the data of the created time entry.

- **stop_time_entry**

  - **Description**: Stops the currently running time entry.
  - **Input**:
    - `workspace_name` (str, optional): Name of the workspace where the entry is running. Defaults to the user's default workspace.
  - **Output**: JSON response containing the data of the stopped time entry.

- **delete_time_entry**

  - **Description**: Deletes a specific time entry by its description and start time.
  - **Input**:
    - `time_entry_description` (str): The exact description of the time entry to delete.
    - `start_time` (str): The exact start time of the entry in ISO 8601 format used for identification.
    - `workspace_name` (str, optional): Name of the workspace containing the entry. Defaults to the user's default workspace.
  - **Output**: Success confirmation message (str) upon successful deletion.

- **get_current_time_entry**

  - **Description**: Fetches the details of the currently running time entry.
  - **Input**: None (implicitly uses the user's context).
  - **Output**: JSON response containing the data of the currently running time entry, or None if no time entry is currently running.

- **update_time_entry**

  - **Description**: Updates attributes of an existing time entry identified by its description and start time.
  - **Input**:
    - `time_entry_description` (str): The current description of the time entry to update.
    - `start_time` (str): The exact start time of the entry in ISO 8601 format used for identification.
    - `workspace_name` (str, optional): Name of the workspace containing the entry. Defaults to the user's default workspace.
    - `new_description` (str, optional): New description for the time entry.
    - `project_name` (str, optional): New project name to associate with the entry. Set to empty string "" to remove project association.
    - `tags` (List[str], optional): A new list of tag names. This will replace all existing tags. Provide an empty list `[]` to remove all tags.
    - `new_start` (str, optional): New start time in local timezone format.
    - `new_stop` (str, optional): New stop time in local timezone format.
    - `billable` (bool, optional): New billable status.
  - **Output**: JSON response containing the data of the updated time entry.

- **get_time_entries_for_range**
  - **Description**: Retrieves time entries within a specified date range, defined by offsets from the current day.
  - **Input**:
    - `from_day_offset` (int): The start day offset from today (e.g., 0 for today, -1 for yesterday, -7 for a week ago).
    - `to_day_offset` (int): The end day offset from today (e.g., 0 for today, 1 for tomorrow). The range includes both the start and end dates.
    - `workspace_name` (str, optional): Name of the workspace to fetch entries from. Defaults to the user's default workspace.
  - **Output**: JSON response containing a list of time entries found within the specified date range.
  
#### Bulk Operations

- **bulk_create_time_entries**
  - **Description**: Creates multiple time entries in a single operation.
  - **Input**:
    - `entries` (List[Dict]): List of time entry objects, each containing description, project_name, tags, etc.
    - `workspace_name` (str, optional): Name of the workspace. Defaults to user's default workspace.
  - **Output**: JSON response containing the created time entries with success/error details.

- **bulk_update_time_entries**
  - **Description**: Updates multiple time entries in a single operation.
  - **Input**:
    - `entries` (List[Dict]): List of time entry update objects with either ID or description to identify entries.
    - `workspace_name` (str, optional): Name of the workspace. Defaults to user's default workspace.
  - **Output**: JSON response containing the updated time entries with success/error details.

- **bulk_delete_time_entries**
  - **Description**: Deletes multiple time entries in a single operation.
  - **Input**:
    - `entry_identifiers` (List[Union[int, str]]): List of time entry IDs or descriptions to delete.
    - `are_descriptions` (bool): Whether identifiers are descriptions (True) or IDs (False).
    - `workspace_name` (str, optional): Name of the workspace. Defaults to user's default workspace.
  - **Output**: JSON response containing results of the deletion operation.

#### Advanced Search

- **search_time_entries**
  - **Description**: Performs full-text search across time entries.
  - **Input**:
    - `query` (str): Text to search for in time entries.
    - `fields` (List[str], optional): Fields to search in (defaults to "description").
    - `case_sensitive` (bool, optional): Whether to perform case-sensitive search. Defaults to False.
  - **Output**: JSON response containing matching time entries and search metadata.

- **advanced_search_time_entries**
  - **Description**: Performs comprehensive multi-criteria filtering of time entries.
  - **Input**:
    - `search_text` (str, optional): Text to search in descriptions.
    - `project_names` (List[str], optional): List of project names to filter by.
    - `start_date` (str, optional): Start of date range in local timezone.
    - `end_date` (str, optional): End of date range in local timezone.
    - `tags` (List[str], optional): List of tags to filter by.
    - `min_duration_minutes` (float, optional): Minimum duration in minutes.
    - `max_duration_minutes` (float, optional): Maximum duration in minutes.
    - `billable` (bool, optional): Filter by billable status.
    - `case_sensitive` (bool, optional): Whether text search is case-sensitive. Defaults to False.
    - `exact_match` (bool, optional): Whether text must match exactly. Defaults to False.
    - `workspace_name` (str, optional): Workspace name to search in.
  - **Output**: JSON response containing matching time entries and search criteria details.

#### Context-Aware Tools

- **what_am_i_working_on**
  - **Description**: Provides comprehensive information about current and recent work activities.
  - **Input**: None.
  - **Output**: JSON response containing current time entry details, recent work summary, most used projects and tags, and natural language summary.

- **continue_previous_work**
  - **Description**: Continues a previous time entry by starting a new one with the same attributes.
  - **Input**:
    - `description` (str, optional): Description of the entry to continue.
    - `time_entry_id` (int, optional): ID of the entry to continue.
    - `workspace_name` (str, optional): Name of the workspace containing the entry.
  - **Output**: JSON response containing the new time entry and reference to the continued entry.

#### Automation Features

- **save_timer_preset**
  - **Description**: Saves a time entry configuration as a preset for future use.
  - **Input**:
    - `name` (str): Name for the preset.
    - `description` (str, optional): Description for entries created with this preset.
    - `project_name` (str, optional): Project name for the preset.
    - `workspace_name` (str, optional): Workspace name for the preset.
    - `tags` (List[str], optional): List of tags to apply.
    - `billable` (bool, optional): Whether entries are billable.
  - **Output**: JSON response containing the saved preset data.

- **start_timer_with_preset**
  - **Description**: Starts a new time entry using a saved preset configuration.
  - **Input**:
    - `preset_name` (str): Name of the preset to use.
  - **Output**: JSON response containing the new time entry data.

- **list_timer_presets**
  - **Description**: Gets all saved timer presets.
  - **Input**: None.
  - **Output**: JSON response containing all timer presets.

- **create_recurring_entry**
  - **Description**: Creates a recurring time entry configuration.
  - **Input**:
    - `description` (str): Description for recurring time entries.
    - `schedule` (Dict): Dictionary defining recurrence pattern.
    - `project_name` (str, optional): Project to associate with the entries.
    - `workspace_name` (str, optional): Workspace name.
    - `tags` (List[str], optional): List of tags to apply.
    - `billable` (bool, optional): Whether entries are billable.
    - `duration_minutes` (int, optional): Default duration in minutes.
  - **Output**: JSON response containing the created recurring entry configuration.

- **run_recurring_entry**
  - **Description**: Manually runs a recurring entry configuration to create a time entry.
  - **Input**:
    - `entry_id` (str): ID of the recurring entry to run.
    - `start_time` (str, optional): Custom start time.
    - `end_time` (str, optional): Custom end time.
  - **Output**: JSON response containing the created time entry data.

#### Convenience Functions

- **resume_time_entry**
  - **Description**: Resumes a previously stopped time entry by creating a new one with the same attributes.
  - **Input**:
    - `time_entry_id` (int): ID of the time entry to resume.
  - **Output**: JSON response containing the new time entry data.

- **duplicate_time_entry**
  - **Description**: Creates an exact duplicate of an existing time entry.
  - **Input**:
    - `time_entry_id` (int): ID of the time entry to duplicate.
    - `start_time` (str, optional): Custom start time for the duplicate.
    - `end_time` (str, optional): Custom end time for the duplicate.
  - **Output**: JSON response containing the duplicated time entry data.

- **split_time_entry**
  - **Description**: Splits a time entry into two separate entries at the specified time.
  - **Input**:
    - `time_entry_id` (int): ID of the time entry to split.
    - `split_time` (str): Time to split at (ISO format in local timezone).
  - **Output**: JSON response containing information about both resulting time entries.

## Project Structure

The Toggl MCP Server is organized into the following modules:

- **api/**: Contains the API client for Toggl
  - `client.py`: Main API client class with HTTP methods

- **helpers/**: Contains helper functions for different Toggl entities
  - `projects.py`: Functions for managing Toggl projects
  - `time_entries.py`: Functions for managing Toggl time entries
  - `workspaces.py`: Functions for managing Toggl workspaces
  - `automation.py`: Functions for presets and recurring entries

- **tools/**: Houses MCP tool definitions
  - `project_tools.py`: MCP tools for project management
  - `time_entry_tools.py`: MCP tools for time entry management
  - `automation_tools.py`: MCP tools for automation features

- **utils/**: Utility modules
  - `timezone.py`: Timezone conversion and formatting utilities
  - `storage.py`: Persistent storage for presets and configurations

- **toggl_mcp_server.py**: Main entry point that registers tools and resources

### Timezone Handling

The server includes a robust timezone handling system that:

1. **Provides Consistent Formats**: Uses standardized formats for timestamps:
   - UTC API Format: `YYYY-MM-DDThh:mm:ss.000Z` (for Toggl API)
   - Local Display Format: `YYYY-MM-DD hh:mm:ss TZ` (for user display)

2. **Automatically Converts Between Timezones**:
   - User timestamps are assumed to be in the local system timezone
   - Timestamps are automatically converted to UTC for API requests
   - API responses include both UTC and local timezone formatted timestamps

3. **Handles Various Input Formats**: Parses and normalizes user-provided timestamps

4. **Enriches API Responses**: Adds local time information to all timestamp fields in API responses

All timezone handling is centralized in the `TimezoneConverter` class to ensure consistency across the application.

## Getting Started

### Prerequisites

- Python 3.11+
- Toggl Track account
- uv installed for dependency management

### Environment Variables

Create a `.env` file inside of the `toggl-mcp-server` folder with either:

```bash
EMAIL=your_toggl_email
PASSWORD=your_toggl_password
```

or

```bash
TOGGL_API_TOKEN=***
```

### Installation

First install uv:
For MacOS/Linux:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
For Windows:
```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Make sure to restart your terminal afterwards to ensure that the uv command gets picked up.

Now let's clone the repository and set up the project:

```bash
git clone [repository-url]
cd toggl-mcp-server/toggl-mcp-server
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync
```

### Integration with Development Tools

#### VS Code + GitHub Copilot Setup

1. Configure the MCP Server in `.vscode/mcp.json`:

```json
"servers": {
  "toggl": {
    "type": "stdio",
    "command": "uv",
    "args": [
      "--directory",
      "/ABSOLUTE/PATH/TO/PARENT/FOLDER/toggl-mcp-server",
      "run",
      "toggl_mcp_server.py"],
    "envFile": "/ABSOLUTE/PATH/TO/PARENT/FOLDER/toggl-mcp-server/.env"
  }
}
```

2. Update the configuration:

   - Replace `/ABSOLUTE/PATH/TO/PARENT/FOLDER/toggl-mcp-server` with the absolute path to the server
   - You may need to put the full path to the uv executable in the command field. You can get this by running which uv on MacOS/Linux or where uv on Windows

3. Enable the server:
   - Look for the start button when hovering over the server configuration `/.vscode/mcp.json`
   - Click start to let Copilot discover available tools
   - Switch to agent mode in Copilot

For detailed setup instructions, see:

- [MCP Servers in VS Code](https://code.visualstudio.com/docs/copilot/chat/mcp-servers)
- [Copilot Agent Mode](https://code.visualstudio.com/docs/copilot/chat/chat-agent-mode)

### Additional MCP Client Integration

The Toggl MCP Server works with any MCP-compatible client. For integration steps:

1. For Claude Desktop, visit the [MCP Quick Start Guide](https://modelcontextprotocol.io/quickstart/user)
2. For other MCP clients, consult their respective documentation for server configuration

Note: Configuration typically involves specifying the server path and environment variables similar to the VS Code setup above.

### Testing with MCP Inspector

To run in development:

```bash
EMAIL=your_toggl_email PASSWORD=your_toggl_password mcp dev toggl_mcp_server.py
```

## License

This MCP server is licensed under the MIT License.