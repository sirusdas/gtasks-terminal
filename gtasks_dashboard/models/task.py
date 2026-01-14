"""
Task Models
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TaskPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class HybridTags:
    bracket: List[str]
    hash: List[str]
    user: List[str]
    
    @classmethod
    def from_dict(cls, data: Dict[str, List[str]]) -> 'HybridTags':
        return cls(
            bracket=data.get('bracket', []),
            hash=data.get('hash', []),
            user=data.get('user', [])
        )
    
    def to_list(self) -> List[str]:
        return self.bracket + self.hash + self.user


@dataclass
class Account:
    id: str
    name: str
    email: str
    account_type: str
    is_active: bool
    task_count: int = 0
    completed_count: int = 0
    completion_rate: float = 0.0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Account':
        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            email=data.get('email', ''),
            account_type=data.get('type', data.get('account_type', 'General')),
            is_active=data.get('isActive', data.get('is_active', True)),
            task_count=data.get('taskCount', data.get('task_count', 0)),
            completed_count=data.get('completedCount', data.get('completed_count', 0)),
            completion_rate=data.get('completionRate', data.get('completion_rate', 0.0))
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'type': self.account_type,
            'isActive': self.is_active,
            'taskCount': self.task_count,
            'completedCount': self.completed_count,
            'completionRate': self.completion_rate
        }


@dataclass
class Task:
    id: str
    title: str
    description: str
    due: Optional[str]
    priority: str
    status: str
    tags: List[str]
    account: str
    notes: Optional[str] = None
    created_at: Optional[str] = None
    modified_at: Optional[str] = None
    hybrid_tags: Optional[HybridTags] = None
    calculated_priority: Optional[str] = None
    project: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    is_deleted: bool = False
    
    @property
    def has_dependencies(self) -> bool:
        return len(self.dependencies) > 0
    
    @property
    def is_overdue(self) -> bool:
        if not self.due or self.status == TaskStatus.COMPLETED.value:
            return False
        from datetime import datetime
        try:
            due_date = datetime.strptime(self.due, '%Y-%m-%d')
            return due_date < datetime.now()
        except (ValueError, TypeError):
            return False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        hybrid = data.get('hybrid_tags')
        if hybrid and isinstance(hybrid, dict):
            hybrid = HybridTags.from_dict(hybrid)
        
        return cls(
            id=data.get('id', ''),
            title=data.get('title', ''),
            description=data.get('description', '') or '',
            due=data.get('due'),
            priority=data.get('priority', 'medium'),
            status=data.get('status', 'pending'),
            tags=data.get('tags', []),
            account=data.get('account', ''),
            notes=data.get('notes'),
            created_at=data.get('created_at'),
            modified_at=data.get('modified_at'),
            hybrid_tags=hybrid,
            calculated_priority=data.get('calculated_priority'),
            project=data.get('project'),
            dependencies=data.get('dependencies', []),
            is_deleted=data.get('is_deleted', False)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        hybrid_dict = None
        if self.hybrid_tags:
            hybrid_dict = {
                'bracket': self.hybrid_tags.bracket,
                'hash': self.hybrid_tags.hash,
                'user': self.hybrid_tags.user
            }
        
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'due': self.due,
            'priority': self.priority,
            'status': self.status,
            'tags': self.tags,
            'account': self.account,
            'notes': self.notes,
            'created_at': self.created_at,
            'modified_at': self.modified_at,
            'hybrid_tags': hybrid_dict,
            'calculated_priority': self.calculated_priority,
            'project': self.project,
            'dependencies': self.dependencies,
            'has_dependencies': self.has_dependencies,
            'is_deleted': self.is_deleted
        }


@dataclass
class DashboardStats:
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    critical_tasks: int
    high_priority_tasks: int
    overdue_tasks: int
    completion_rate: float
    
    @classmethod
    def from_tasks(cls, tasks: List[Task]) -> 'DashboardStats':
        total = len(tasks)
        completed = len([t for t in tasks if t.status == TaskStatus.COMPLETED.value])
        pending = len([t for t in tasks if t.status == TaskStatus.PENDING.value])
        in_progress = len([t for t in tasks if t.status == TaskStatus.IN_PROGRESS.value])
        critical = len([t for t in tasks if t.calculated_priority == TaskPriority.CRITICAL.value])
        high = len([t for t in tasks if t.calculated_priority == TaskPriority.HIGH.value])
        overdue = len([t for t in tasks if t.is_overdue])
        
        return cls(
            total_tasks=total,
            completed_tasks=completed,
            pending_tasks=pending,
            in_progress_tasks=in_progress,
            critical_tasks=critical,
            high_priority_tasks=high,
            overdue_tasks=overdue,
            completion_rate=(completed / total * 100) if total > 0 else 0.0
        )
