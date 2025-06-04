"""
Inventory Management System for BGE Save Editor
Handles item and equipment editing and management
"""

import copy
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from undo_system import undo_system, ActionType

class ItemType(Enum):
    """Types of items in BGE"""
    WEAPON = "weapon"
    TOOL = "tool"
    CONSUMABLE = "consumable"
    KEY_ITEM = "key_item"
    UPGRADE = "upgrade"
    PHOTO = "photo"
    MISC = "misc"

class ItemRarity(Enum):
    """Item rarity levels"""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"

@dataclass
class ItemInfo:
    """Information about an inventory item"""
    id: str
    name: str
    description: str
    item_type: ItemType
    rarity: ItemRarity
    max_stack: int = 1
    value: int = 0
    tradeable: bool = True
    
@dataclass
class InventoryItem:
    """An item in the inventory with quantity"""
    item_info: ItemInfo
    quantity: int = 1
    equipped: bool = False
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class InventoryManager:
    """
    Manages inventory data in BGE save files
    
    Features:
    - Item discovery and management
    - Equipment tracking
    - Quantity management
    - Item database with descriptions
    - Batch operations with undo support
    """
    
    def __init__(self):
        self.item_database = self._initialize_item_database()
        self.save_data = None
        self.inventory_items: Dict[str, InventoryItem] = {}
        
    def _initialize_item_database(self) -> Dict[str, ItemInfo]:
        """Initialize the database of known items"""
        items = {}
        
        # Weapons
        weapons = [
            ("dai_jo", "Dai-Jo Staff", "Jade's signature weapon", ItemRarity.COMMON, 1, 0),
            ("super_dai_jo", "Super Dai-Jo", "Upgraded Dai-Jo with more power", ItemRarity.RARE, 1, 100),
            ("disc_launcher", "Disc Launcher", "Ranged weapon for combat", ItemRarity.UNCOMMON, 1, 50),
        ]
        
        for item_id, name, desc, rarity, max_stack, value in weapons:
            items[item_id] = ItemInfo(
                id=item_id,
                name=name,
                description=desc,
                item_type=ItemType.WEAPON,
                rarity=rarity,
                max_stack=max_stack,
                value=value
            )
        
        # Tools
        tools = [
            ("camera", "Camera", "For taking photos and scanning", ItemRarity.COMMON, 1, 0),
            ("gyrodisk_launcher", "Gyrodisk Launcher", "Tool for activating switches", ItemRarity.COMMON, 1, 0),
            ("neutralizing_spray", "Neutralizing Spray", "Disables force fields", ItemRarity.UNCOMMON, 1, 25),
            ("space_engine", "Space Engine", "Allows space travel", ItemRarity.EPIC, 1, 500),
            ("k_bups", "K-Bups", "Hovercraft upgrade parts", ItemRarity.RARE, 10, 100),
        ]
        
        for item_id, name, desc, rarity, max_stack, value in tools:
            items[item_id] = ItemInfo(
                id=item_id,
                name=name,
                description=desc,
                item_type=ItemType.TOOL,
                rarity=rarity,
                max_stack=max_stack,
                value=value
            )
        
        # Consumables
        consumables = [
            ("starkos", "Starkos", "Health restoration item", ItemRarity.COMMON, 99, 10),
            ("super_starkos", "Super Starkos", "Full health restoration", ItemRarity.UNCOMMON, 10, 50),
            ("pa_system_key", "PA System Key", "Access key for announcements", ItemRarity.RARE, 1, 0),
        ]
        
        for item_id, name, desc, rarity, max_stack, value in consumables:
            items[item_id] = ItemInfo(
                id=item_id,
                name=name,
                description=desc,
                item_type=ItemType.CONSUMABLE,
                rarity=rarity,
                max_stack=max_stack,
                value=value
            )
        
        # Key Items
        key_items = [
            ("lighthouse_key", "Lighthouse Key", "Key to the lighthouse", ItemRarity.RARE, 1, 0),
            ("factory_pass", "Factory Pass", "Access pass for the factory", ItemRarity.RARE, 1, 0),
            ("moon_key", "Moon Key", "Key to moon base areas", ItemRarity.EPIC, 1, 0),
            ("domz_detector", "DomZ Detector", "Detects DomZ presence", ItemRarity.LEGENDARY, 1, 0),
        ]
        
        for item_id, name, desc, rarity, max_stack, value in key_items:
            items[item_id] = ItemInfo(
                id=item_id,
                name=name,
                description=desc,
                item_type=ItemType.KEY_ITEM,
                rarity=rarity,
                max_stack=max_stack,
                value=value,
                tradeable=False
            )
        
        # Upgrades
        upgrades = [
            ("health_upgrade_1", "Health Heart 1", "Increases maximum health", ItemRarity.UNCOMMON, 1, 0),
            ("health_upgrade_2", "Health Heart 2", "Further health increase", ItemRarity.RARE, 1, 0),
            ("health_upgrade_3", "Health Heart 3", "Maximum health upgrade", ItemRarity.EPIC, 1, 0),
            ("speed_upgrade", "Speed Boots", "Increases movement speed", ItemRarity.RARE, 1, 0),
            ("jump_upgrade", "Jump Boots", "Increases jump height", ItemRarity.RARE, 1, 0),
        ]
        
        for item_id, name, desc, rarity, max_stack, value in upgrades:
            items[item_id] = ItemInfo(
                id=item_id,
                name=name,
                description=desc,
                item_type=ItemType.UPGRADE,
                rarity=rarity,
                max_stack=max_stack,
                value=value,
                tradeable=False
            )
        
        # Photos (special category)
        photos = [
            ("photo_001", "Hillys Landscape", "Beautiful view of Hillys", ItemRarity.COMMON, 1, 5),
            ("photo_002", "Factory Interior", "Industrial photography", ItemRarity.COMMON, 1, 5),
            ("photo_003", "Rare Species", "Photo of rare creature", ItemRarity.RARE, 1, 25),
            ("photo_004", "DomZ Evidence", "Proof of DomZ activity", ItemRarity.EPIC, 1, 100),
        ]
        
        for item_id, name, desc, rarity, max_stack, value in photos:
            items[item_id] = ItemInfo(
                id=item_id,
                name=name,
                description=desc,
                item_type=ItemType.PHOTO,
                rarity=rarity,
                max_stack=max_stack,
                value=value
            )
        
        return items
    
    def set_save_data(self, save_data: Dict):
        """Set the save data to work with"""
        self.save_data = save_data
        self._load_inventory_from_save()
    
    def _load_inventory_from_save(self):
        """Load inventory data from save file"""
        if not self.save_data:
            return
        
        self.inventory_items.clear()
        
        # Look for inventory data in various possible locations
        inventory_paths = [
            ["inventaire"],
            ["inventory"],
            ["items"],
            ["player", "inventory"],
            ["player", "items"],
            ["character", "inventory"]
        ]
        
        for path in inventory_paths:
            inventory_data = self._get_nested_value(self.save_data, path)
            if inventory_data:
                self._parse_inventory_data(inventory_data)
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
    
    def _parse_inventory_data(self, inventory_data: Any):
        """Parse inventory data from save file"""
        if isinstance(inventory_data, dict):
            for item_id, item_data in inventory_data.items():
                self._parse_item_data(item_id, item_data)
        elif isinstance(inventory_data, list):
            # List of items
            for item_data in inventory_data:
                if isinstance(item_data, dict) and "id" in item_data:
                    self._parse_item_data(item_data["id"], item_data)
    
    def _parse_item_data(self, item_id: str, item_data: Any):
        """Parse individual item data"""
        # Get item info from database or create unknown item
        if item_id in self.item_database:
            item_info = self.item_database[item_id]
        else:
            item_info = self._create_unknown_item(item_id)
        
        # Parse quantity and other data
        if isinstance(item_data, dict):
            quantity = item_data.get("quantity", item_data.get("count", 1))
            equipped = item_data.get("equipped", item_data.get("active", False))
            metadata = {k: v for k, v in item_data.items() 
                       if k not in ["quantity", "count", "equipped", "active"]}
        else:
            quantity = int(item_data) if isinstance(item_data, (int, float)) else 1
            equipped = False
            metadata = {}
        
        self.inventory_items[item_id] = InventoryItem(
            item_info=item_info,
            quantity=max(1, int(quantity)),
            equipped=bool(equipped),
            metadata=metadata
        )
    
    def _create_unknown_item(self, item_id: str) -> ItemInfo:
        """Create an unknown item found in save data"""
        item_info = ItemInfo(
            id=item_id,
            name=f"Unknown Item ({item_id})",
            description="Item found in save data",
            item_type=ItemType.MISC,
            rarity=ItemRarity.COMMON,
            max_stack=99,
            value=0
        )
        self.item_database[item_id] = item_info
        return item_info
    
    def get_all_items(self) -> List[InventoryItem]:
        """Get all items in inventory"""
        return list(self.inventory_items.values())
    
    def get_items_by_type(self, item_type: ItemType) -> List[InventoryItem]:
        """Get items of a specific type"""
        return [item for item in self.inventory_items.values() 
                if item.item_info.item_type == item_type]
    
    def get_equipped_items(self) -> List[InventoryItem]:
        """Get all equipped items"""
        return [item for item in self.inventory_items.values() if item.equipped]
    
    def get_inventory_stats(self) -> Dict[str, Any]:
        """Get statistics about the inventory"""
        all_items = list(self.inventory_items.values())
        
        stats = {
            "total_items": len(all_items),
            "total_quantity": sum(item.quantity for item in all_items),
            "equipped_items": len([item for item in all_items if item.equipped]),
            "total_value": sum(item.item_info.value * item.quantity for item in all_items),
            "by_type": {},
            "by_rarity": {}
        }
        
        # Stats by type
        for item_type in ItemType:
            type_items = [item for item in all_items if item.item_info.item_type == item_type]
            stats["by_type"][item_type.value] = {
                "count": len(type_items),
                "total_quantity": sum(item.quantity for item in type_items)
            }
        
        # Stats by rarity
        for rarity in ItemRarity:
            rarity_items = [item for item in all_items if item.item_info.rarity == rarity]
            stats["by_rarity"][rarity.value] = {
                "count": len(rarity_items),
                "total_quantity": sum(item.quantity for item in rarity_items)
            }
        
        return stats
    
    def add_item(self, item_id: str, quantity: int = 1, equipped: bool = False) -> bool:
        """
        Add an item to the inventory
        
        Args:
            item_id: ID of the item to add
            quantity: Quantity to add
            equipped: Whether the item should be equipped
            
        Returns:
            True if successful, False otherwise
        """
        if item_id not in self.item_database:
            return False
        
        item_info = self.item_database[item_id]
        
        # Record action for undo
        old_item = self.inventory_items.get(item_id)
        old_quantity = old_item.quantity if old_item else 0
        new_quantity = old_quantity + quantity
        
        # Check max stack
        if new_quantity > item_info.max_stack:
            new_quantity = item_info.max_stack
            quantity = new_quantity - old_quantity
        
        if quantity <= 0:
            return False
        
        undo_system.record_action(
            action_type=ActionType.INVENTORY_ADD,
            path=["inventaire", item_id],
            old_value=old_quantity,
            new_value=new_quantity,
            description=f"Added {quantity}x {item_info.name}",
            metadata={"item_id": item_id, "quantity": quantity}
        )
        
        # Add or update item
        if item_id in self.inventory_items:
            self.inventory_items[item_id].quantity = new_quantity
            if equipped:
                self.inventory_items[item_id].equipped = True
        else:
            self.inventory_items[item_id] = InventoryItem(
                item_info=item_info,
                quantity=new_quantity,
                equipped=equipped
            )
        
        # Update save data
        self._update_save_data_item(item_id)
        return True
    
    def remove_item(self, item_id: str, quantity: int = None) -> bool:
        """
        Remove an item from the inventory
        
        Args:
            item_id: ID of the item to remove
            quantity: Quantity to remove (None = remove all)
            
        Returns:
            True if successful, False otherwise
        """
        if item_id not in self.inventory_items:
            return False
        
        current_item = self.inventory_items[item_id]
        old_quantity = current_item.quantity
        
        if quantity is None:
            new_quantity = 0
            quantity = old_quantity
        else:
            new_quantity = max(0, old_quantity - quantity)
            quantity = old_quantity - new_quantity
        
        if quantity <= 0:
            return False
        
        # Record action for undo
        undo_system.record_action(
            action_type=ActionType.INVENTORY_REMOVE,
            path=["inventaire", item_id],
            old_value=old_quantity,
            new_value=new_quantity if new_quantity > 0 else None,
            description=f"Removed {quantity}x {current_item.item_info.name}",
            metadata={"item_id": item_id, "quantity": quantity}
        )
        
        # Update or remove item
        if new_quantity > 0:
            current_item.quantity = new_quantity
        else:
            del self.inventory_items[item_id]
        
        # Update save data
        self._update_save_data_item(item_id, new_quantity if new_quantity > 0 else None)
        return True
    
    def set_item_equipped(self, item_id: str, equipped: bool) -> bool:
        """
        Set the equipped status of an item
        
        Args:
            item_id: ID of the item
            equipped: Whether the item should be equipped
            
        Returns:
            True if successful, False otherwise
        """
        if item_id not in self.inventory_items:
            return False
        
        item = self.inventory_items[item_id]
        old_equipped = item.equipped
        
        if old_equipped == equipped:
            return True  # No change needed
        
        # Record action for undo
        action = "Equipped" if equipped else "Unequipped"
        undo_system.record_action(
            action_type=ActionType.INVENTORY_MODIFY,
            path=["inventaire", item_id, "equipped"],
            old_value=old_equipped,
            new_value=equipped,
            description=f"{action} {item.item_info.name}",
            metadata={"item_id": item_id, "property": "equipped"}
        )
        
        # Update item
        item.equipped = equipped
        
        # Update save data
        self._update_save_data_item(item_id)
        return True
    
    def _update_save_data_item(self, item_id: str, quantity: int = None):
        """Update an item in the save data"""
        if not self.save_data:
            return
        
        # Ensure inventory section exists
        if "inventaire" not in self.save_data:
            self.save_data["inventaire"] = {}
        
        if quantity is None and item_id in self.inventory_items:
            # Update existing item
            item = self.inventory_items[item_id]
            self.save_data["inventaire"][item_id] = {
                "quantity": item.quantity,
                "equipped": item.equipped,
                **item.metadata
            }
        elif quantity is None:
            # Remove item
            if item_id in self.save_data["inventaire"]:
                del self.save_data["inventaire"][item_id]
        else:
            # Set specific quantity
            if quantity > 0:
                item = self.inventory_items.get(item_id)
                self.save_data["inventaire"][item_id] = {
                    "quantity": quantity,
                    "equipped": item.equipped if item else False,
                    **(item.metadata if item else {})
                }
            else:
                if item_id in self.save_data["inventaire"]:
                    del self.save_data["inventaire"][item_id]
    
    def add_all_items(self) -> int:
        """
        Add all known items to inventory
        
        Returns:
            Number of items added
        """
        undo_system.start_batch("Add all items")
        
        added_count = 0
        for item_id, item_info in self.item_database.items():
            if item_id not in self.inventory_items:
                if self.add_item(item_id, 1):
                    added_count += 1
        
        undo_system.end_batch()
        return added_count
    
    def clear_inventory(self) -> int:
        """
        Clear all items from inventory
        
        Returns:
            Number of items removed
        """
        undo_system.start_batch("Clear inventory")
        
        removed_count = 0
        item_ids = list(self.inventory_items.keys())
        for item_id in item_ids:
            if self.remove_item(item_id):
                removed_count += 1
        
        undo_system.end_batch()
        return removed_count
    
    def search_items(self, query: str) -> List[InventoryItem]:
        """
        Search items by name, description, or type
        
        Args:
            query: Search query
            
        Returns:
            List of matching items
        """
        query = query.lower()
        results = []
        
        for item in self.inventory_items.values():
            if (query in item.item_info.name.lower() or 
                query in item.item_info.description.lower() or 
                query in item.item_info.item_type.value.lower() or
                query in item.item_info.id.lower()):
                results.append(item)
        
        return results

# Global inventory manager instance
inventory_manager = InventoryManager()