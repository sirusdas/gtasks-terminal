"""
Undo manager for interactive mode operations.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from gtasks_cli.models.task import Task
from gtasks_cli.utils.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class UndoOperation:
    """Represents a reversible operation"""
    description: str
    timestamp: datetime
    # Function to call to undo the operation
    undo_func: Callable[[], bool]
    # Metadata about the operation
    metadata: Dict[str, Any] = None

class UndoManager:
    """Manages undo history and operations"""
    
    def __init__(self, max_history: int = 20):
        self.history: List[UndoOperation] = []
        self.max_history = max_history
        
    def push_operation(self, description: str, undo_func: Callable[[], bool], metadata: Dict[str, Any] = None):
        """
        Register an operation that can be undone.
        
        Args:
            description: Human-readable description of what was done
            undo_func: Function that, when called, reverts the change
            metadata: Optional extra info
        """
        op = UndoOperation(
            description=description,
            timestamp=datetime.now(),
            undo_func=undo_func,
            metadata=metadata or {}
        )
        
        self.history.append(op)
        
        # Trim history if needed
        if len(self.history) > self.max_history:
            self.history.pop(0)
            
        logger.debug(f"Pushed undo operation: {description}")
        
    def pop_undo(self) -> Optional[UndoOperation]:
        """Get and remove the last operation"""
        if not self.history:
            return None
        return self.history.pop()
    
    def peek_undo(self) -> Optional[UndoOperation]:
        """Look at the last operation without removing it"""
        if not self.history:
            return None
        return self.history[-1]
    
    def clear(self):
        """Clear history"""
        self.history.clear()
        
    @property
    def can_undo(self) -> bool:
        """Check if undo is available"""
        return len(self.history) > 0

# Global instance
undo_manager = UndoManager()
