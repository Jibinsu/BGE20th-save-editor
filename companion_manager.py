"""
Companion Management System for BGE Save Editor
Handles pet and companion data editing
"""

import copy
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from undo_system import undo_system, ActionType

class CompanionType(Enum):
    """Types of companions in BGE"""
    PET = "pet"
    ALLY = "ally"
    VEHICLE = "vehicle"
    SUMMON = "summon"

class CompanionStatus(Enum):
    """Status of companions"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    INJURED = "injured"
    MISSING = "missing"
    AVAILABLE = "available"

@dataclass
class CompanionInfo:
    """Information about a companion"""
    id: str
    name: str
    description: str
    companion_type: CompanionType
    max_health: float = 100.0
    max_energy: float = 100.0
    abilities: List[str] = None
    
    def __post_init__(self):
        if self.abilities is None:
            self.abilities = []

@dataclass
class CompanionData:
    """Current data for a companion"""
    companion_info: CompanionInfo
    status: CompanionStatus = CompanionStatus.AVAILABLE
    health: float = 100.0
    energy: float = 100.0
    experience: int = 0
    level: int = 1
    loyalty: float = 100.0
    equipped_items: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.equipped_items is None:
            self.equipped_items = []
        if self.metadata is None:
            self.metadata = {}

class CompanionManager:
    """
    Manages companion data in BGE save files
    
    Features:
    - Companion discovery and management
    - Health and energy management
    - Status tracking
    - Equipment management
    - Experience and leveling
    - Loyalty system
    """
    
    def __init__(self):
        self.companion_database = self._initialize_companion_database()
        self.save_data = None
        self.companions: Dict[str, CompanionData] = {}
        
    def _initialize_companion_database(self) -> Dict[str, CompanionInfo]:
        """Initialize the database of known companions"""
        companions = {}
        
        # Main allies
        allies = [
            ("peyj", "Pey'j", "Jade's uncle and trusted companion", ["repair", "hack", "boost"]),
            ("double_h", "Double H", "IRIS agent and ally", ["combat", "shield", "investigate"]),
            ("hh", "HH", "Double H's alternate form", ["stealth", "infiltrate", "analyze"]),
        ]
        
        for comp_id, name, desc, abilities in allies:
            companions[comp_id] = CompanionInfo(
                id=comp_id,
                name=name,
                description=desc,
                companion_type=CompanionType.ALLY,
                max_health=150.0,
                max_energy=120.0,
                abilities=abilities
            )
        
        # Vehicles/Pets
        vehicles = [
            ("beluga", "Beluga", "Jade's hovercraft", ["transport", "boost", "jump"]),
            ("space_beluga", "Space Beluga", "Upgraded Beluga for space travel", ["space_travel", "boost", "shield"]),
            ("mammago_ship", "Mammago's Ship", "Mammago's delivery vehicle", ["cargo", "speed", "stealth"]),
        ]
        
        for comp_id, name, desc, abilities in vehicles:
            companions[comp_id] = CompanionInfo(
                id=comp_id,
                name=name,
                description=desc,
                companion_type=CompanionType.VEHICLE,
                max_health=200.0,
                max_energy=150.0,
                abilities=abilities
            )
        
        # Pets/Animals
        pets = [
            ("woofie", "Woofie", "Loyal dog companion", ["fetch", "guard", "track"]),
            ("ming_tzu", "Ming-Tzu", "Wise old turtle", ["wisdom", "slow_time", "guidance"]),
            ("fehn", "Fehn", "Agile cat companion", ["stealth", "climb", "hunt"]),
            ("rhino", "Rhino", "Strong rhino ally", ["charge", "break_walls", "intimidate"]),
        ]
        
        for comp_id, name, desc, abilities in pets:
            companions[comp_id] = CompanionInfo(
                id=comp_id,
                name=name,
                description=desc,
                companion_type=CompanionType.PET,
                max_health=80.0,
                max_energy=100.0,
                abilities=abilities
            )
        
        # Special summons
        summons = [
            ("spirit_jade", "Spirit of Jade", "Jade's spiritual form", ["phase", "energy_blast", "heal"]),
            ("domz_spirit", "Purified DomZ", "Converted DomZ ally", ["corrupt", "infect", "drain"]),
        ]
        
        for comp_id, name, desc, abilities in summons:
            companions[comp_id] = CompanionInfo(
                id=comp_id,
                name=name,
                description=desc,
                companion_type=CompanionType.SUMMON,
                max_health=120.0,
                max_energy=200.0,
                abilities=abilities
            )
        
        return companions
    
    def set_save_data(self, save_data: Dict):
        """Set the save data to work with"""
        self.save_data = save_data
        self._load_companions_from_save()
    
    def _load_companions_from_save(self):
        """Load companion data from save file"""
        if not self.save_data:
            return
        
        self.companions.clear()
        
        # Look for companion data in various possible locations
        companion_paths = [
            ["companions"],
            ["compagnons"],
            ["allies"],
            ["pets"],
            ["vehicles"],
            ["player", "companions"],
            ["character", "companions"]
        ]
        
        for path in companion_paths:
            companion_data = self._get_nested_value(self.save_data, path)
            if companion_data:
                self._parse_companion_data(companion_data)
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
    
    def _parse_companion_data(self, companion_data: Any):
        """Parse companion data from save file"""
        if isinstance(companion_data, dict):
            for comp_id, comp_data in companion_data.items():
                self._parse_individual_companion(comp_id, comp_data)
        elif isinstance(companion_data, list):
            # List of companions
            for comp_data in companion_data:
                if isinstance(comp_data, dict) and "id" in comp_data:
                    self._parse_individual_companion(comp_data["id"], comp_data)
    
    def _parse_individual_companion(self, comp_id: str, comp_data: Any):
        """Parse individual companion data"""
        # Get companion info from database or create unknown companion
        if comp_id in self.companion_database:
            companion_info = self.companion_database[comp_id]
        else:
            companion_info = self._create_unknown_companion(comp_id)
        
        # Parse companion data
        if isinstance(comp_data, dict):
            status_str = comp_data.get("status", comp_data.get("etat", "available"))
            try:
                status = CompanionStatus(status_str)
            except ValueError:
                status = CompanionStatus.AVAILABLE
            
            health = float(comp_data.get("health", comp_data.get("vie", companion_info.max_health)))
            energy = float(comp_data.get("energy", comp_data.get("energie", companion_info.max_energy)))
            experience = int(comp_data.get("experience", comp_data.get("exp", 0)))
            level = int(comp_data.get("level", comp_data.get("niveau", 1)))
            loyalty = float(comp_data.get("loyalty", comp_data.get("fidelite", 100.0)))
            
            equipped_items = comp_data.get("equipped_items", comp_data.get("objets_equipes", []))
            if not isinstance(equipped_items, list):
                equipped_items = []
            
            metadata = {k: v for k, v in comp_data.items() 
                       if k not in ["status", "etat", "health", "vie", "energy", "energie", 
                                   "experience", "exp", "level", "niveau", "loyalty", "fidelite", 
                                   "equipped_items", "objets_equipes"]}
        else:
            # Simple presence indicator
            status = CompanionStatus.ACTIVE if comp_data else CompanionStatus.INACTIVE
            health = companion_info.max_health
            energy = companion_info.max_energy
            experience = 0
            level = 1
            loyalty = 100.0
            equipped_items = []
            metadata = {}
        
        self.companions[comp_id] = CompanionData(
            companion_info=companion_info,
            status=status,
            health=min(health, companion_info.max_health),
            energy=min(energy, companion_info.max_energy),
            experience=experience,
            level=max(1, level),
            loyalty=max(0.0, min(100.0, loyalty)),
            equipped_items=equipped_items,
            metadata=metadata
        )
    
    def _create_unknown_companion(self, comp_id: str) -> CompanionInfo:
        """Create an unknown companion found in save data"""
        companion_info = CompanionInfo(
            id=comp_id,
            name=f"Unknown Companion ({comp_id})",
            description="Companion found in save data",
            companion_type=CompanionType.PET,
            max_health=100.0,
            max_energy=100.0,
            abilities=[]
        )
        self.companion_database[comp_id] = companion_info
        return companion_info
    
    def get_all_companions(self) -> List[CompanionData]:
        """Get all companions"""
        return list(self.companions.values())
    
    def get_companions_by_type(self, companion_type: CompanionType) -> List[CompanionData]:
        """Get companions of a specific type"""
        return [comp for comp in self.companions.values() 
                if comp.companion_info.companion_type == companion_type]
    
    def get_active_companions(self) -> List[CompanionData]:
        """Get all active companions"""
        return [comp for comp in self.companions.values() 
                if comp.status == CompanionStatus.ACTIVE]
    
    def get_companion_stats(self) -> Dict[str, Any]:
        """Get statistics about companions"""
        all_companions = list(self.companions.values())
        
        stats = {
            "total_companions": len(all_companions),
            "active_companions": len([c for c in all_companions if c.status == CompanionStatus.ACTIVE]),
            "average_health": sum(c.health for c in all_companions) / len(all_companions) if all_companions else 0,
            "average_loyalty": sum(c.loyalty for c in all_companions) / len(all_companions) if all_companions else 0,
            "total_experience": sum(c.experience for c in all_companions),
            "by_type": {},
            "by_status": {}
        }
        
        # Stats by type
        for comp_type in CompanionType:
            type_companions = [c for c in all_companions if c.companion_info.companion_type == comp_type]
            stats["by_type"][comp_type.value] = {
                "count": len(type_companions),
                "active": len([c for c in type_companions if c.status == CompanionStatus.ACTIVE])
            }
        
        # Stats by status
        for status in CompanionStatus:
            status_companions = [c for c in all_companions if c.status == status]
            stats["by_status"][status.value] = len(status_companions)
        
        return stats
    
    def set_companion_status(self, comp_id: str, status: CompanionStatus) -> bool:
        """Set the status of a companion"""
        if comp_id not in self.companions:
            return False
        
        companion = self.companions[comp_id]
        old_status = companion.status
        
        if old_status == status:
            return True  # No change needed
        
        # Record action for undo
        undo_system.record_action(
            action_type=ActionType.COMPANION_MODIFY,
            path=["companions", comp_id, "status"],
            old_value=old_status.value,
            new_value=status.value,
            description=f"Changed {companion.companion_info.name} status: {old_status.value} → {status.value}",
            metadata={"companion_id": comp_id, "property": "status"}
        )
        
        companion.status = status
        self._update_save_data_companion(comp_id)
        return True
    
    def set_companion_health(self, comp_id: str, health: float) -> bool:
        """Set the health of a companion"""
        if comp_id not in self.companions:
            return False
        
        companion = self.companions[comp_id]
        old_health = companion.health
        new_health = max(0.0, min(health, companion.companion_info.max_health))
        
        if abs(old_health - new_health) < 0.01:
            return True  # No significant change
        
        # Record action for undo
        undo_system.record_action(
            action_type=ActionType.COMPANION_MODIFY,
            path=["companions", comp_id, "health"],
            old_value=old_health,
            new_value=new_health,
            description=f"Changed {companion.companion_info.name} health: {old_health:.1f} → {new_health:.1f}",
            metadata={"companion_id": comp_id, "property": "health"}
        )
        
        companion.health = new_health
        self._update_save_data_companion(comp_id)
        return True
    
    def set_companion_energy(self, comp_id: str, energy: float) -> bool:
        """Set the energy of a companion"""
        if comp_id not in self.companions:
            return False
        
        companion = self.companions[comp_id]
        old_energy = companion.energy
        new_energy = max(0.0, min(energy, companion.companion_info.max_energy))
        
        if abs(old_energy - new_energy) < 0.01:
            return True  # No significant change
        
        # Record action for undo
        undo_system.record_action(
            action_type=ActionType.COMPANION_MODIFY,
            path=["companions", comp_id, "energy"],
            old_value=old_energy,
            new_value=new_energy,
            description=f"Changed {companion.companion_info.name} energy: {old_energy:.1f} → {new_energy:.1f}",
            metadata={"companion_id": comp_id, "property": "energy"}
        )
        
        companion.energy = new_energy
        self._update_save_data_companion(comp_id)
        return True
    
    def set_companion_loyalty(self, comp_id: str, loyalty: float) -> bool:
        """Set the loyalty of a companion"""
        if comp_id not in self.companions:
            return False
        
        companion = self.companions[comp_id]
        old_loyalty = companion.loyalty
        new_loyalty = max(0.0, min(100.0, loyalty))
        
        if abs(old_loyalty - new_loyalty) < 0.01:
            return True  # No significant change
        
        # Record action for undo
        undo_system.record_action(
            action_type=ActionType.COMPANION_MODIFY,
            path=["companions", comp_id, "loyalty"],
            old_value=old_loyalty,
            new_value=new_loyalty,
            description=f"Changed {companion.companion_info.name} loyalty: {old_loyalty:.1f}% → {new_loyalty:.1f}%",
            metadata={"companion_id": comp_id, "property": "loyalty"}
        )
        
        companion.loyalty = new_loyalty
        self._update_save_data_companion(comp_id)
        return True
    
    def set_companion_level(self, comp_id: str, level: int) -> bool:
        """Set the level of a companion"""
        if comp_id not in self.companions:
            return False
        
        companion = self.companions[comp_id]
        old_level = companion.level
        new_level = max(1, min(50, level))  # Level cap at 50
        
        if old_level == new_level:
            return True  # No change needed
        
        # Record action for undo
        undo_system.record_action(
            action_type=ActionType.COMPANION_MODIFY,
            path=["companions", comp_id, "level"],
            old_value=old_level,
            new_value=new_level,
            description=f"Changed {companion.companion_info.name} level: {old_level} → {new_level}",
            metadata={"companion_id": comp_id, "property": "level"}
        )
        
        companion.level = new_level
        self._update_save_data_companion(comp_id)
        return True
    
    def heal_all_companions(self) -> int:
        """Heal all companions to full health and energy"""
        undo_system.start_batch("Heal all companions")
        
        healed_count = 0
        for comp_id, companion in self.companions.items():
            if companion.health < companion.companion_info.max_health or companion.energy < companion.companion_info.max_energy:
                self.set_companion_health(comp_id, companion.companion_info.max_health)
                self.set_companion_energy(comp_id, companion.companion_info.max_energy)
                healed_count += 1
        
        undo_system.end_batch()
        return healed_count
    
    def activate_all_companions(self) -> int:
        """Activate all companions"""
        undo_system.start_batch("Activate all companions")
        
        activated_count = 0
        for comp_id, companion in self.companions.items():
            if companion.status != CompanionStatus.ACTIVE:
                self.set_companion_status(comp_id, CompanionStatus.ACTIVE)
                activated_count += 1
        
        undo_system.end_batch()
        return activated_count
    
    def max_loyalty_all_companions(self) -> int:
        """Set all companions to maximum loyalty"""
        undo_system.start_batch("Maximize all companion loyalty")
        
        updated_count = 0
        for comp_id, companion in self.companions.items():
            if companion.loyalty < 100.0:
                self.set_companion_loyalty(comp_id, 100.0)
                updated_count += 1
        
        undo_system.end_batch()
        return updated_count
    
    def _update_save_data_companion(self, comp_id: str):
        """Update a companion in the save data"""
        if not self.save_data or comp_id not in self.companions:
            return
        
        # Ensure companions section exists
        if "companions" not in self.save_data:
            self.save_data["companions"] = {}
        
        companion = self.companions[comp_id]
        self.save_data["companions"][comp_id] = {
            "status": companion.status.value,
            "health": companion.health,
            "energy": companion.energy,
            "experience": companion.experience,
            "level": companion.level,
            "loyalty": companion.loyalty,
            "equipped_items": companion.equipped_items.copy(),
            **companion.metadata
        }
    
    def search_companions(self, query: str) -> List[CompanionData]:
        """
        Search companions by name, description, or type
        
        Args:
            query: Search query
            
        Returns:
            List of matching companions
        """
        query = query.lower()
        results = []
        
        for companion in self.companions.values():
            if (query in companion.companion_info.name.lower() or 
                query in companion.companion_info.description.lower() or 
                query in companion.companion_info.companion_type.value.lower() or
                query in companion.companion_info.id.lower()):
                results.append(companion)
        
        return results

# Global companion manager instance
companion_manager = CompanionManager()