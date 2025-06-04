"""
Pearls Management System for BGE Save Editor
Handles collectible pearl editing and management
"""

import copy
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from undo_system import undo_system, ActionType

class PearlType(Enum):
    """Types of pearls in BGE"""
    REGULAR = "regular"
    ALPHA = "alpha"
    SPECIAL = "special"
    STORY = "story"

@dataclass
class PearlInfo:
    """Information about a pearl"""
    id: str
    name: str
    description: str
    pearl_type: PearlType
    location: str
    collected: bool
    value: int = 1
    
class PearlsManager:
    """
    Manages pearl collection data in BGE save files
    
    Features:
    - Pearl discovery and enumeration
    - Collection status management
    - Pearl type classification
    - Location tracking
    - Batch operations with undo support
    """
    
    def __init__(self):
        self.pearl_database = self._initialize_pearl_database()
        self.save_data = None
        
    def _initialize_pearl_database(self) -> Dict[str, PearlInfo]:
        """Initialize the database of known pearls"""
        pearls = {}
        
        # Regular pearls (common collectibles)
        regular_pearls = [
            ("perle_001", "Factory Pearl 1", "Pearl found in the factory area", "Factory"),
            ("perle_002", "Factory Pearl 2", "Hidden pearl in factory ventilation", "Factory"),
            ("perle_003", "City Pearl 1", "Pearl in the main city area", "Hillys City"),
            ("perle_004", "City Pearl 2", "Pearl near the lighthouse", "Hillys City"),
            ("perle_005", "Pedestrian District Pearl", "Pearl in residential area", "Pedestrian District"),
            ("perle_006", "Black Isle Pearl", "Pearl on Black Isle", "Black Isle"),
            ("perle_007", "Volcano Pearl", "Pearl near the volcano", "Volcano"),
            ("perle_008", "Moon Pearl", "Pearl on the moon base", "Moon"),
            ("perle_009", "Akuda Bar Pearl", "Pearl hidden in Akuda Bar", "Akuda Bar"),
            ("perle_010", "Mammago Garage Pearl", "Pearl at Mammago's garage", "Mammago Garage"),
        ]
        
        for pearl_id, name, desc, location in regular_pearls:
            pearls[pearl_id] = PearlInfo(
                id=pearl_id,
                name=name,
                description=desc,
                pearl_type=PearlType.REGULAR,
                location=location,
                collected=False
            )
        
        # Alpha pearls (special boss/challenge pearls)
        alpha_pearls = [
            ("alpha_001", "Reaper Alpha Pearl", "Pearl from defeating the Reaper", "Factory"),
            ("alpha_002", "Cyclops Alpha Pearl", "Pearl from Cyclops boss", "Black Isle"),
            ("alpha_003", "Domz Alpha Pearl", "Pearl from Domz creature", "Moon"),
            ("alpha_004", "Racing Alpha Pearl", "Pearl from winning races", "Various"),
            ("alpha_005", "Photography Alpha Pearl", "Pearl from photo missions", "Various"),
        ]
        
        for pearl_id, name, desc, location in alpha_pearls:
            pearls[pearl_id] = PearlInfo(
                id=pearl_id,
                name=name,
                description=desc,
                pearl_type=PearlType.ALPHA,
                location=location,
                collected=False,
                value=3  # Alpha pearls are worth more
            )
        
        # Story pearls (main quest pearls)
        story_pearls = [
            ("story_001", "Jade's First Pearl", "Starting pearl", "Lighthouse"),
            ("story_002", "Pey'j's Pearl", "Pearl from Pey'j", "Lighthouse"),
            ("story_003", "Double H Pearl", "Pearl from Double H", "Akuda Bar"),
            ("story_004", "Final Pearl", "Last story pearl", "Moon"),
        ]
        
        for pearl_id, name, desc, location in story_pearls:
            pearls[pearl_id] = PearlInfo(
                id=pearl_id,
                name=name,
                description=desc,
                pearl_type=PearlType.STORY,
                location=location,
                collected=False,
                value=1
            )
        
        return pearls
    
    def set_save_data(self, save_data: Dict):
        """Set the save data to work with"""
        self.save_data = save_data
        self._update_pearl_status()
    
    def _update_pearl_status(self):
        """Update pearl collection status from save data"""
        if not self.save_data:
            return
        
        # Look for pearl data in various possible locations
        pearl_paths = [
            ["perles"],
            ["collectibles", "perles"],
            ["inventory", "perles"],
            ["progression", "perles"],
            ["player", "perles"]
        ]
        
        for path in pearl_paths:
            pearl_data = self._get_nested_value(self.save_data, path)
            if pearl_data:
                self._parse_pearl_data(pearl_data)
                break
    
    def _get_nested_value(self, data: Dict, path: List[str]) -> Any:
        """Get a value from nested dictionary using path"""
        current = data
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current
    
    def _parse_pearl_data(self, pearl_data: Any):
        """Parse pearl data from save file"""
        if isinstance(pearl_data, dict):
            for key, value in pearl_data.items():
                if key in self.pearl_database:
                    self.pearl_database[key].collected = bool(value)
                elif key.startswith("perle") or "pearl" in key.lower():
                    # Unknown pearl, add to database
                    self._add_unknown_pearl(key, value)
        elif isinstance(pearl_data, list):
            # List of collected pearl IDs
            for pearl_id in pearl_data:
                if pearl_id in self.pearl_database:
                    self.pearl_database[pearl_id].collected = True
    
    def _add_unknown_pearl(self, pearl_id: str, value: Any):
        """Add an unknown pearl found in save data"""
        self.pearl_database[pearl_id] = PearlInfo(
            id=pearl_id,
            name=f"Unknown Pearl ({pearl_id})",
            description="Pearl found in save data",
            pearl_type=PearlType.REGULAR,
            location="Unknown",
            collected=bool(value)
        )
    
    def get_all_pearls(self) -> List[PearlInfo]:
        """Get all pearls sorted by type and name"""
        pearls = list(self.pearl_database.values())
        
        # Sort by type priority, then by name
        type_priority = {
            PearlType.STORY: 0,
            PearlType.ALPHA: 1,
            PearlType.SPECIAL: 2,
            PearlType.REGULAR: 3
        }
        
        return sorted(pearls, key=lambda p: (type_priority[p.pearl_type], p.name))
    
    def get_pearls_by_type(self, pearl_type: PearlType) -> List[PearlInfo]:
        """Get pearls of a specific type"""
        return [p for p in self.pearl_database.values() if p.pearl_type == pearl_type]
    
    def get_collected_pearls(self) -> List[PearlInfo]:
        """Get all collected pearls"""
        return [p for p in self.pearl_database.values() if p.collected]
    
    def get_uncollected_pearls(self) -> List[PearlInfo]:
        """Get all uncollected pearls"""
        return [p for p in self.pearl_database.values() if not p.collected]
    
    def get_pearl_stats(self) -> Dict[str, Any]:
        """Get statistics about pearl collection"""
        all_pearls = list(self.pearl_database.values())
        collected = [p for p in all_pearls if p.collected]
        
        stats = {
            "total_pearls": len(all_pearls),
            "collected_pearls": len(collected),
            "uncollected_pearls": len(all_pearls) - len(collected),
            "collection_percentage": (len(collected) / len(all_pearls) * 100) if all_pearls else 0,
            "total_value": sum(p.value for p in collected),
            "by_type": {}
        }
        
        # Stats by type
        for pearl_type in PearlType:
            type_pearls = [p for p in all_pearls if p.pearl_type == pearl_type]
            type_collected = [p for p in type_pearls if p.collected]
            
            stats["by_type"][pearl_type.value] = {
                "total": len(type_pearls),
                "collected": len(type_collected),
                "percentage": (len(type_collected) / len(type_pearls) * 100) if type_pearls else 0
            }
        
        return stats
    
    def set_pearl_collected(self, pearl_id: str, collected: bool, 
                           description: str = None) -> bool:
        """
        Set the collection status of a pearl
        
        Args:
            pearl_id: ID of the pearl
            collected: Whether the pearl is collected
            description: Custom description for undo
            
        Returns:
            True if successful, False otherwise
        """
        if pearl_id not in self.pearl_database:
            return False
        
        pearl = self.pearl_database[pearl_id]
        old_status = pearl.collected
        
        if old_status == collected:
            return True  # No change needed
        
        # Record action for undo
        if description is None:
            action = "Collected" if collected else "Uncollected"
            description = f"{action} pearl: {pearl.name}"
        
        # Find the path to the pearl in save data
        pearl_path = self._find_pearl_path(pearl_id)
        if pearl_path:
            undo_system.record_action(
                action_type=ActionType.PEARL_ADD if collected else ActionType.PEARL_REMOVE,
                path=pearl_path,
                old_value=old_status,
                new_value=collected,
                description=description,
                metadata={"pearl_id": pearl_id, "pearl_name": pearl.name}
            )
        
        # Update pearl status
        pearl.collected = collected
        
        # Update save data
        self._update_save_data_pearl(pearl_id, collected)
        
        return True
    
    def _find_pearl_path(self, pearl_id: str) -> Optional[List[str]]:
        """Find the path to a pearl in the save data"""
        if not self.save_data:
            return None
        
        # Common pearl data locations
        possible_paths = [
            ["perles", pearl_id],
            ["collectibles", "perles", pearl_id],
            ["inventory", "perles", pearl_id],
            ["progression", "perles", pearl_id],
            ["player", "perles", pearl_id]
        ]
        
        for path in possible_paths:
            if self._path_exists(self.save_data, path[:-1]):
                return path
        
        # Default to creating in perles section
        return ["perles", pearl_id]
    
    def _path_exists(self, data: Dict, path: List[str]) -> bool:
        """Check if a path exists in the data structure"""
        current = data
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return False
        return True
    
    def _update_save_data_pearl(self, pearl_id: str, collected: bool):
        """Update the pearl status in save data"""
        if not self.save_data:
            return
        
        # Ensure perles section exists
        if "perles" not in self.save_data:
            self.save_data["perles"] = {}
        
        if collected:
            self.save_data["perles"][pearl_id] = True
        else:
            if pearl_id in self.save_data["perles"]:
                del self.save_data["perles"][pearl_id]
    
    def collect_all_pearls(self) -> int:
        """
        Collect all pearls
        
        Returns:
            Number of pearls that were newly collected
        """
        undo_system.start_batch("Collect all pearls")
        
        newly_collected = 0
        for pearl in self.pearl_database.values():
            if not pearl.collected:
                if self.set_pearl_collected(pearl.id, True):
                    newly_collected += 1
        
        undo_system.end_batch()
        return newly_collected
    
    def uncollect_all_pearls(self) -> int:
        """
        Uncollect all pearls
        
        Returns:
            Number of pearls that were uncollected
        """
        undo_system.start_batch("Uncollect all pearls")
        
        newly_uncollected = 0
        for pearl in self.pearl_database.values():
            if pearl.collected:
                if self.set_pearl_collected(pearl.id, False):
                    newly_uncollected += 1
        
        undo_system.end_batch()
        return newly_uncollected
    
    def collect_pearls_by_type(self, pearl_type: PearlType) -> int:
        """
        Collect all pearls of a specific type
        
        Returns:
            Number of pearls that were newly collected
        """
        type_name = pearl_type.value.title()
        undo_system.start_batch(f"Collect all {type_name} pearls")
        
        newly_collected = 0
        for pearl in self.get_pearls_by_type(pearl_type):
            if not pearl.collected:
                if self.set_pearl_collected(pearl.id, True):
                    newly_collected += 1
        
        undo_system.end_batch()
        return newly_collected
    
    def search_pearls(self, query: str) -> List[PearlInfo]:
        """
        Search pearls by name, description, or location
        
        Args:
            query: Search query
            
        Returns:
            List of matching pearls
        """
        query = query.lower()
        results = []
        
        for pearl in self.pearl_database.values():
            if (query in pearl.name.lower() or 
                query in pearl.description.lower() or 
                query in pearl.location.lower() or
                query in pearl.id.lower()):
                results.append(pearl)
        
        return results

# Global pearls manager instance
pearls_manager = PearlsManager()