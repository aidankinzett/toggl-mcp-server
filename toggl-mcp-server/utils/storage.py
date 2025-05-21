"""
Storage utilities for persisting user preferences and presets.

This module provides a simple file-based storage mechanism for saving 
and retrieving user presets for timer configurations and recurring entries.
"""

import os
import json
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

class PresetStorage:
    """
    Handles persistence of timer presets and recurring entries.
    
    Uses a simple JSON file-based storage mechanism in the user's home directory
    to save and load presets across sessions.
    """
    
    STORAGE_DIR = os.path.expanduser("~/.toggl_mcp")
    PRESETS_FILE = "presets.json"
    RECURRING_FILE = "recurring.json"
    
    def __init__(self):
        """Initialize the storage and ensure directories exist."""
        # Create storage directory if it doesn't exist
        os.makedirs(self.STORAGE_DIR, exist_ok=True)
        
        # Initialize the presets file if it doesn't exist
        presets_path = os.path.join(self.STORAGE_DIR, self.PRESETS_FILE)
        if not os.path.exists(presets_path):
            self._save_json(presets_path, {"version": 1, "presets": []})
            
        # Initialize the recurring entries file if it doesn't exist
        recurring_path = os.path.join(self.STORAGE_DIR, self.RECURRING_FILE)
        if not os.path.exists(recurring_path):
            self._save_json(recurring_path, {"version": 1, "recurring_entries": []})
    
    def _save_json(self, filepath: str, data: Dict[str, Any]) -> bool:
        """
        Save data to a JSON file.
        
        Args:
            filepath: Path to the file
            data: Dictionary data to save
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving to {filepath}: {e}")
            return False
    
    def _load_json(self, filepath: str) -> Optional[Dict[str, Any]]:
        """
        Load data from a JSON file.
        
        Args:
            filepath: Path to the file
            
        Returns:
            Dict or None: Loaded data or None if load failed
        """
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading from {filepath}: {e}")
            return None
    
    def save_preset(self, preset: Dict[str, Any]) -> bool:
        """
        Save a timer preset.
        
        Args:
            preset: Dictionary containing preset data with at least 'name' key
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        if not preset.get('name'):
            return False
            
        # Load existing presets
        presets_path = os.path.join(self.STORAGE_DIR, self.PRESETS_FILE)
        data = self._load_json(presets_path)
        
        if not data:
            data = {"version": 1, "presets": []}
            
        # Check if this preset already exists
        presets = data.get("presets", [])
        for i, existing in enumerate(presets):
            if existing.get("name") == preset["name"]:
                # Update existing preset
                presets[i] = preset
                break
        else:
            # Add new preset
            presets.append(preset)
            
        data["presets"] = presets
        
        # Save back to file
        return self._save_json(presets_path, data)
    
    def get_preset(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific timer preset by name.
        
        Args:
            name: Name of the preset to retrieve
            
        Returns:
            Dict or None: The preset data or None if not found
        """
        presets_path = os.path.join(self.STORAGE_DIR, self.PRESETS_FILE)
        data = self._load_json(presets_path)
        
        if not data:
            return None
            
        # Find preset by name
        for preset in data.get("presets", []):
            if preset.get("name") == name:
                return preset
                
        return None
    
    def get_all_presets(self) -> List[Dict[str, Any]]:
        """
        Get all saved timer presets.
        
        Returns:
            List: List of preset dictionaries
        """
        presets_path = os.path.join(self.STORAGE_DIR, self.PRESETS_FILE)
        data = self._load_json(presets_path)
        
        if not data:
            return []
            
        return data.get("presets", [])
    
    def delete_preset(self, name: str) -> bool:
        """
        Delete a timer preset by name.
        
        Args:
            name: Name of the preset to delete
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        presets_path = os.path.join(self.STORAGE_DIR, self.PRESETS_FILE)
        data = self._load_json(presets_path)
        
        if not data:
            return False
            
        # Filter out the preset to delete
        presets = data.get("presets", [])
        new_presets = [p for p in presets if p.get("name") != name]
        
        if len(new_presets) == len(presets):
            # Nothing was removed
            return False
            
        data["presets"] = new_presets
        
        # Save back to file
        return self._save_json(presets_path, data)
    
    def save_recurring_entry(self, recurring_entry: Dict[str, Any]) -> bool:
        """
        Save a recurring time entry configuration.
        
        Args:
            recurring_entry: Dictionary containing recurring entry data with at least 'id' key
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        if not recurring_entry.get('id'):
            return False
            
        # Load existing recurring entries
        recurring_path = os.path.join(self.STORAGE_DIR, self.RECURRING_FILE)
        data = self._load_json(recurring_path)
        
        if not data:
            data = {"version": 1, "recurring_entries": []}
            
        # Check if this entry already exists
        entries = data.get("recurring_entries", [])
        for i, existing in enumerate(entries):
            if existing.get("id") == recurring_entry["id"]:
                # Update existing entry
                entries[i] = recurring_entry
                break
        else:
            # Add new entry
            entries.append(recurring_entry)
            
        data["recurring_entries"] = entries
        
        # Save back to file
        return self._save_json(recurring_path, data)
    
    def get_recurring_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific recurring entry by ID.
        
        Args:
            entry_id: ID of the recurring entry to retrieve
            
        Returns:
            Dict or None: The recurring entry data or None if not found
        """
        recurring_path = os.path.join(self.STORAGE_DIR, self.RECURRING_FILE)
        data = self._load_json(recurring_path)
        
        if not data:
            return None
            
        # Find entry by ID
        for entry in data.get("recurring_entries", []):
            if entry.get("id") == entry_id:
                return entry
                
        return None
    
    def get_all_recurring_entries(self) -> List[Dict[str, Any]]:
        """
        Get all saved recurring entries.
        
        Returns:
            List: List of recurring entry dictionaries
        """
        recurring_path = os.path.join(self.STORAGE_DIR, self.RECURRING_FILE)
        data = self._load_json(recurring_path)
        
        if not data:
            return []
            
        return data.get("recurring_entries", [])
    
    def delete_recurring_entry(self, entry_id: str) -> bool:
        """
        Delete a recurring entry by ID.
        
        Args:
            entry_id: ID of the recurring entry to delete
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        recurring_path = os.path.join(self.STORAGE_DIR, self.RECURRING_FILE)
        data = self._load_json(recurring_path)
        
        if not data:
            return False
            
        # Filter out the entry to delete
        entries = data.get("recurring_entries", [])
        new_entries = [e for e in entries if e.get("id") != entry_id]
        
        if len(new_entries) == len(entries):
            # Nothing was removed
            return False
            
        data["recurring_entries"] = new_entries
        
        # Save back to file
        return self._save_json(recurring_path, data)

# Create a global instance for import
preset_storage = PresetStorage()