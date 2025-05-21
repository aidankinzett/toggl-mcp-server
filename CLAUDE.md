# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains a Toggl MCP Server which provides Model Context Protocol (MCP) tools for interacting with Toggl Track's time tracking service. It allows MCP clients (like Claude, Copilot, etc.) to perform Toggl operations through natural language.

## Requirements

- Python 3.11+
- Toggl Track account
- uv installed for dependency management

## Development Setup

1. First, install uv:
   ```bash
   # For MacOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # For Windows
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. Set up the project:
   ```bash
   cd toggl-mcp-server/toggl-mcp-server
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv sync
   ```

3. Create a `.env` file inside the `toggl-mcp-server` folder with either:
   ```
   EMAIL=your_toggl_email
   PASSWORD=your_toggl_password
   ```
   or
   ```
   TOGGL_API_TOKEN=***
   ```

## Running the Server

To run the server for development:
```bash
cd toggl-mcp-server
python toggl_mcp_server.py
```

For testing with MCP Inspector:
```bash
EMAIL=your_toggl_email PASSWORD=your_toggl_password mcp dev toggl_mcp_server.py
```

## Code Architecture

The server is built using Python's MCP server framework and consists of these main components:

1. **Main Server** (`toggl_mcp_server.py`): Initializes the FastMCP server and defines all tools and resources
2. **Core Functionality**:
   - Authentication handling (API token or email/password)
   - Time zone handling for accurate time entry tracking
   - API request handling with error management

3. **Tool Categories**:
   - **Project Management Tools**: Create, delete, update, and get projects
   - **Time Entry Tools**: Create, stop, delete, update, and query time entries

4. **Helper Functions**:
   - Time conversion utilities for working with UTC/local times
   - API interaction functions for each Toggl endpoint
   - Resource lookup functions to search for entities by name

The server follows a layered architecture:
- Tools (exposed to MCP clients)
- Helper functions (tool implementations)
- Core API interaction functions

## VS Code Integration

To configure the MCP Server in VS Code:

1. Create a `.vscode/mcp.json` file:
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

2. Replace `/ABSOLUTE/PATH/TO/PARENT/FOLDER/toggl-mcp-server` with the actual path.

3. Start the server from VS Code and use with Copilot in agent mode.