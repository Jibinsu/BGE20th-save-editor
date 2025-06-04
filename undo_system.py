"""
Undo/Redo system for BGE Save Editor
Provides comprehensive change tracking and reversal capabilities
"""

import copy
import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

class ActionType(Enum):
    """Types of actions that can be undone/redone"""
    VALUE_CHANGE = "value_change"
    PEARL_ADD = "pearl_add"
    PEARL_REMOVE = "pearl_remove"
    INVENTORY_ADD = "inventory_add"
    INVENTORY_REMOVE = "inventory_remove"
    INVENTORY_MODIFY = "inventory_modify"
    COMPANION_MODIFY = "companion_modify"
    BATCH_OPERATION = "batch_operation"

@dataclass
class UndoAction:
    """Represents a single undoable action"""
    action_type: ActionType
    timestamp: float
    description: str
    path: List[str]  # Path to the data in the save structure
    old_value: Any
    new_value: Any
    metadata: Dict[str, Any] = None  # Additional context data
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class UndoRedoSystem:
    """
    Comprehensive undo/redo system for save file modifications
    
    Features:
    - Unlimited undo/redo history
    - Batch operations support
    - Memory-efficient deep copying
    - Action descriptions for UI
    - Automatic cleanup of old actions
    """
    
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.undo_stack: List[UndoAction] = []
        self.redo_stack: List[UndoAction] = []
        self.batch_mode = False
        self.batch_actions: List[UndoAction] = []
        self.change_callbacks: List[Callable] = []
        
    def add_change_callback(self, callback: Callable):
        """Add a callback to be called when undo/redo state changes"""
        self.change_callbacks.append(callback)
    
    def _notify_change(self):
        """Notify all callbacks that the undo/redo state has changed"""
        for callback in self.change_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"Error in undo/redo callback: {e}")
    
    def record_action(self, action_type: ActionType, path: List[str], 
                     old_value: Any, new_value: Any, description: str = None,
                     metadata: Dict[str, Any] = None) -> None:
        """
        Record an action for undo/redo
        
        Args:
            action_type: Type of action being performed
            path: Path to the data in the save structure
            old_value: Value before the change
            new_value: Value after the change
            description: Human-readable description of the action
            metadata: Additional context data
        """
        if description is None:
            description = self._generate_description(action_type, path, old_value, new_value)
        
        action = UndoAction(
            action_type=action_type,
            timestamp=time.time(),
            description=description,
            path=path.copy(),
            old_value=copy.deepcopy(old_value),
            new_value=copy.deepcopy(new_value),
            metadata=metadata or {}
        )
        
        if self.batch_mode:
            self.batch_actions.append(action)
        else:
            self._add_action(action)
    
    def _add_action(self, action: UndoAction):
        """Add an action to the undo stack"""
        self.undo_stack.append(action)
        self.redo_stack.clear()  # Clear redo stack when new action is added
        
        # Limit history size
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
        
        self._notify_change()
    
    def start_batch(self, description: str = "Batch operation"):
        """Start a batch operation - all actions will be grouped together"""
        self.batch_mode = True
        self.batch_actions.clear()
        self.batch_description = description
    
    def end_batch(self):
        """End a batch operation and add all actions as a single undoable unit"""
        if not self.batch_mode:
            return
        
        self.batch_mode = False
        
        if self.batch_actions:
            # Create a batch action that contains all individual actions
            batch_action = UndoAction(
                action_type=ActionType.BATCH_OPERATION,
                timestamp=time.time(),
                description=self.batch_description,
                path=[],
                old_value=None,
                new_value=None,
                metadata={"actions": self.batch_actions.copy()}
            )
            self._add_action(batch_action)
        
        self.batch_actions.clear()
    
    def can_undo(self) -> bool:
        """Check if undo is possible"""
        return len(self.undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Check if redo is possible"""
        return len(self.redo_stack) > 0
    
    def get_undo_description(self) -> Optional[str]:
        """Get description of the next undo action"""
        if self.can_undo():
            return self.undo_stack[-1].description
        return None
    
    def get_redo_description(self) -> Optional[str]:
        """Get description of the next redo action"""
        if self.can_redo():
            return self.redo_stack[-1].description
        return None
    
    def undo(self, data: Dict) -> bool:
        """
        Undo the last action
        
        Args:
            data: The save data dictionary to modify
            
        Returns:
            True if undo was successful, False otherwise
        """
        if not self.can_undo():
            return False
        
        action = self.undo_stack.pop()
        
        try:
            if action.action_type == ActionType.BATCH_OPERATION:
                # Undo all actions in the batch in reverse order
                batch_actions = action.metadata.get("actions", [])
                for batch_action in reversed(batch_actions):
                    self._apply_action_reverse(batch_action, data)
            else:
                self._apply_action_reverse(action, data)
            
            self.redo_stack.append(action)
            self._notify_change()
            return True
            
        except Exception as e:
            # If undo fails, put the action back
            self.undo_stack.append(action)
            print(f"Undo failed: {e}")
            return False
    
    def redo(self, data: Dict) -> bool:
        """
        Redo the last undone action
        
        Args:
            data: The save data dictionary to modify
            
        Returns:
            True if redo was successful, False otherwise
        """
        if not self.can_redo():
            return False
        
        action = self.redo_stack.pop()
        
        try:
            if action.action_type == ActionType.BATCH_OPERATION:
                # Redo all actions in the batch in original order
                batch_actions = action.metadata.get("actions", [])
                for batch_action in batch_actions:
                    self._apply_action_forward(batch_action, data)
            else:
                self._apply_action_forward(action, data)
            
            self.undo_stack.append(action)
            self._notify_change()
            return True
            
        except Exception as e:
            # If redo fails, put the action back
            self.redo_stack.append(action)
            print(f"Redo failed: {e}")
            return False
    
    def _apply_action_reverse(self, action: UndoAction, data: Dict):
        """Apply an action in reverse (undo)"""
        self._set_value_at_path(data, action.path, action.old_value)
    
    def _apply_action_forward(self, action: UndoAction, data: Dict):
        """Apply an action forward (redo)"""
        self._set_value_at_path(data, action.path, action.new_value)
    
    def _set_value_at_path(self, data: Dict, path: List[str], value: Any):
        """Set a value at the specified path in the data structure"""
        if not path:
            return
        
        current = data
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        if value is None and path[-1] in current:
            del current[path[-1]]
        else:
            current[path[-1]] = copy.deepcopy(value)
    
    def _generate_description(self, action_type: ActionType, path: List[str], 
                            old_value: Any, new_value: Any) -> str:
        """Generate a human-readable description for an action"""
        path_str = " → ".join(path) if path else "root"
        
        if action_type == ActionType.VALUE_CHANGE:
            return f"Changed {path_str}: {old_value} → {new_value}"
        elif action_type == ActionType.PEARL_ADD:
            return f"Added pearl: {new_value}"
        elif action_type == ActionType.PEARL_REMOVE:
            return f"Removed pearl: {old_value}"
        elif action_type == ActionType.INVENTORY_ADD:
            return f"Added item to inventory: {new_value}"
        elif action_type == ActionType.INVENTORY_REMOVE:
            return f"Removed item from inventory: {old_value}"
        elif action_type == ActionType.INVENTORY_MODIFY:
            return f"Modified inventory item: {path_str}"
        elif action_type == ActionType.COMPANION_MODIFY:
            return f"Modified companion data: {path_str}"
        else:
            return f"Modified {path_str}"
    
    def clear_history(self):
        """Clear all undo/redo history"""
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.batch_actions.clear()
        self.batch_mode = False
        self._notify_change()
    
    def get_history_info(self) -> Dict[str, Any]:
        """Get information about the current undo/redo state"""
        return {
            "undo_count": len(self.undo_stack),
            "redo_count": len(self.redo_stack),
            "can_undo": self.can_undo(),
            "can_redo": self.can_redo(),
            "undo_description": self.get_undo_description(),
            "redo_description": self.get_redo_description(),
            "batch_mode": self.batch_mode,
            "batch_actions_count": len(self.batch_actions) if self.batch_mode else 0
        }

# Global undo system instance
undo_system = UndoRedoSystem()