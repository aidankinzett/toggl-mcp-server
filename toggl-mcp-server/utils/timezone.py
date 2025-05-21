"""
Timezone handling utilities for the Toggl MCP Server.
This module provides consistent timezone conversion and formatting
for timestamps used in Toggl API interactions.
"""

import datetime
from datetime import timezone, timedelta
from typing import Tuple, Any, Dict
from tzlocal import get_localzone

# Standard timestamp formats
UTC_API_FORMAT = "%Y-%m-%dT%H:%M:%S.000Z"  # Format required by Toggl API
LOCAL_DISPLAY_FORMAT = "%Y-%m-%d %H:%M:%S %Z"  # Human-readable format with timezone
ISO_FORMAT = "%Y-%m-%dT%H:%M:%S"  # ISO 8601 format without timezone


class TimezoneConverter:
    """
    Handles all timezone conversions consistently throughout the application.
    """

    def __init__(self):
        """Initialize with system's local timezone, falling back to UTC if unavailable."""
        try:
            self.local_tz = get_localzone()
            print(f"Using system timezone: {self.local_tz}")
        except Exception as e:
            print(f"Warning: Failed to get system timezone: {e}, falling back to UTC")
            self.local_tz = timezone.utc

    def get_timezone_info(self) -> dict:
        """
        Get information about the system timezone.

        Returns:
            dict: Information about the timezone including name, offset from UTC
        """
        now = datetime.datetime.now(self.local_tz)
        return {
            "timezone_name": str(self.local_tz),
            "timezone_offset": now.strftime("%z"),
            "current_time": now.strftime(LOCAL_DISPLAY_FORMAT),
        }

    def get_current_utc_time(self) -> str:
        """
        Get the current UTC time formatted as required by Toggl API.

        Returns:
            str: The current UTC time in RFC 3339 format. Example: '2025-04-09T16:15:22.000Z'
        """
        now = datetime.datetime.now(timezone.utc)
        return now.strftime(UTC_API_FORMAT)

    def local_to_utc(self, local_time_str: str) -> Tuple[str, Dict[str, Any]]:
        """
        Convert a local timestamp string to UTC format for the Toggl API.

        Args:
            local_time_str (str): A timestamp in local time (various formats supported)

        Returns:
            Tuple[str, Dict]: The UTC timestamp and debug information
        """
        debug_info = {
            "original_input": local_time_str,
            "conversion_applied": False,
            "system_timezone": str(self.local_tz),
        }

        if not local_time_str:
            return None, debug_info

        try:
            # Clean up input string to handle variations
            clean_time_str = local_time_str.split(".")[0].replace("Z", "")

            # Parse the timestamp assuming it's in local time
            assumed_local_naive_dt = datetime.datetime.fromisoformat(clean_time_str)

            # Apply timezone
            if hasattr(self.local_tz, "localize"):
                # pytz style
                assumed_local_dt = self.local_tz.localize(
                    assumed_local_naive_dt, is_dst=None
                )
            else:
                # datetime.timezone style
                assumed_local_dt = assumed_local_naive_dt.replace(tzinfo=self.local_tz)

            # Convert to UTC
            utc_dt = assumed_local_dt.astimezone(timezone.utc)
            utc_time_str = self.format_for_api(utc_dt)

            debug_info["conversion_applied"] = True
            debug_info["converted_utc"] = utc_time_str

            return utc_time_str, debug_info

        except Exception as e:
            debug_info["error"] = str(e)
            return local_time_str, debug_info

    def utc_to_local(self, utc_time_str: str) -> str:
        """
        Convert a UTC timestamp string to local time for display.

        Args:
            utc_time_str (str): A UTC timestamp (e.g., '2025-04-09T15:37:50.000Z')

        Returns:
            str: Human-readable local time string with timezone info
        """
        if not utc_time_str:
            return None

        try:
            # Handle various UTC timestamp formats
            utc_dt = None
            if utc_time_str.endswith("Z"):
                if "." in utc_time_str:
                    utc_dt = datetime.datetime.strptime(
                        utc_time_str, "%Y-%m-%dT%H:%M:%S.%fZ"
                    )
                else:
                    utc_dt = datetime.datetime.strptime(
                        utc_time_str, "%Y-%m-%dT%H:%M:%SZ"
                    )
            elif "+" in utc_time_str:
                utc_dt = datetime.datetime.fromisoformat(
                    utc_time_str.replace("Z", "+00:00")
                )
            else:
                # Assume UTC if no timezone specified
                utc_dt = datetime.datetime.fromisoformat(utc_time_str)

            utc_dt = utc_dt.replace(tzinfo=timezone.utc)
            local_dt = utc_dt.astimezone(self.local_tz)

            return local_dt.strftime(LOCAL_DISPLAY_FORMAT)

        except ValueError as e:
            return f"Invalid timestamp format: {e}"

    def format_for_api(self, dt: datetime.datetime) -> str:
        """
        Format a datetime object for Toggl API (ISO 8601 with milliseconds and Z).

        Args:
            dt: The datetime object to format

        Returns:
            str: Formatted timestamp string
        """
        return dt.strftime(UTC_API_FORMAT)

    def get_date_range(self, days_offset: int) -> Tuple[str, str]:
        """
        Get start and end timestamps for a specific day in UTC format for API.

        Args:
            days_offset (int): Day offset from today (0=today, -1=yesterday)

        Returns:
            Tuple[str, str]: UTC start and end timestamps
        """
        # Get current date in local time
        local_now = datetime.datetime.now(self.local_tz)
        target_date = local_now.date() + timedelta(days=days_offset)

        # Create datetime at midnight local time
        start_dt_local = datetime.datetime.combine(
            target_date, datetime.time.min, tzinfo=self.local_tz
        )
        end_dt_local = start_dt_local + timedelta(days=1)

        # Convert to UTC for API call
        start_dt_utc = start_dt_local.astimezone(timezone.utc)
        end_dt_utc = end_dt_local.astimezone(timezone.utc)

        return self.format_for_api(start_dt_utc), self.format_for_api(end_dt_utc)

    def enrich_time_entry_with_local_times(self, entry: Dict) -> Dict:
        """
        Add local time versions of timestamp fields in a time entry.

        Args:
            entry (Dict): A time entry dictionary from the Toggl API

        Returns:
            Dict: The same dictionary with added local time fields
        """
        if not entry:
            return entry

        if "start" in entry and entry["start"]:
            entry["start_local"] = self.utc_to_local(entry["start"])

        if "stop" in entry and entry["stop"]:
            entry["stop_local"] = self.utc_to_local(entry["stop"])

        return entry


# Create a global instance for import
tz_converter = TimezoneConverter()
