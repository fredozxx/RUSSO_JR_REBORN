#!/usr/bin/env python3
"""
Task Router - Dynamic task routing for Russo Jr
Routes tasks based on triggers, schedules, and Discord commands
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from enum import Enum

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

class TaskType(Enum):
    UTILITY = "utility"
    DATA = "data"
    AI = "ai"
    LEARNING = "learning"
    MAINTENANCE = "maintenance"

class TaskPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

class TaskRouter:
    def __init__(self):
        self.project_root = project_root
        self.brain_scripts_dir = self.project_root / "brain_scripts"
        self.configs_dir = self.project_root / "logs" / "configs"
        self.logs_dir = self.project_root / "logs"
        
        # Setup logging
        self.setup_logging()
        
        # Task queue and routing rules
        self.task_queue = []
        self.routing_rules = {}
        self.load_routing_config()
        
    def setup_logging(self):
        """Initialize logging system"""
        self.logs_dir.mkdir(exist_ok=True)
        log_file = self.logs_dir / f"task_router_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_routing_config(self):
        """Load routing configuration and script registry"""
        registry_path = self.configs_dir / "script_registry.json"
        if registry_path.exists():
            try:
                with open(registry_path, 'r') as f:
                    self.script_registry = json.load(f)
                    self.logger.info("Loaded script registry")
            except Exception as e:
                self.logger.error(f"Failed to load script registry: {e}")
                self.script_registry = {}
        else:
            self.script_registry = {}
    
    def add_task(self, task_name, task_type=TaskType.UTILITY, priority=TaskPriority.NORMAL, 
                 trigger_source="manual", metadata=None):
        """Add a task to the routing queue"""
        task = {
            "id": f"{task_name}_{datetime.now().timestamp()}",
            "name": task_name,
            "type": task_type.value if isinstance(task_type, TaskType) else task_type,
            "priority": priority.value if isinstance(priority, TaskPriority) else priority,
            "trigger_source": trigger_source,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
            "status": "queued"
        }
        
        self.task_queue.append(task)
        self.logger.info(f"Added task: {task['name']} (ID: {task['id']})")
        return task["id"]
    
    def route_discord_command(self, command, args=None, user_id=None):
        """Route Discord commands to appropriate tasks"""
        args = args or []
        
        command_routing = {
            "teach": {
                "task_name": "learning_module",
                "task_type": TaskType.LEARNING,
                "priority": TaskPriority.HIGH
            },
            "flush": {
                "task_name": "memory_flush",
                "task_type": TaskType.MAINTENANCE,
                "priority": TaskPriority.NORMAL
            },
            "goal": {
                "task_name": "goal_setter",
                "task_type": TaskType.AI,
                "priority": TaskPriority.HIGH
            },
            "mode": {
                "task_name": "mode_switcher",
                "task_type": TaskType.UTILITY,
                "priority": TaskPriority.NORMAL
            },
            "status": {
                "task_name": "status_report",
                "task_type": TaskType.UTILITY,
                "priority": TaskPriority.LOW
            },
            "analyze": {
                "task_name": "data_analyzer",
                "task_type": TaskType.DATA,
                "priority": TaskPriority.NORMAL
            }
        }
        
        if command in command_routing:
            route_info = command_routing[command]
            metadata = {
                "discord_command": command,
                "args": args,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
            
            task_id = self.add_task(
                task_name=route_info["task_name"],
                task_type=route_info["task_type"],
                priority=route_info["priority"],
                trigger_source="discord",
                metadata=metadata
            )
            
            self.logger.info(f"Routed Discord command '{command}' to task {task_id}")
            return task_id
        else:
            self.logger.warning(f"Unknown Discord command: {command}")
            return None
    
    def route_by_schedule(self, schedule_type="hourly"):
        """Route tasks based on schedule triggers"""
        schedule_routing = {
            "hourly": ["data_collector", "health_check"],
            "daily": ["log_rotator", "backup_manager"],
            "weekly": ["deep_analysis", "model_training"],
            "monthly": ["full_backup", "performance_review"]
        }
        
        if schedule_type in schedule_routing:
            for task_name in schedule_routing[schedule_type]:
                self.add_task(
                    task_name=task_name,
                    task_type=TaskType.MAINTENANCE,
                    priority=TaskPriority.LOW,
                    trigger_source=f"schedule_{schedule_type}"
                )
            
            self.logger.info(f"Added {len(schedule_routing[schedule_type])} scheduled tasks ({schedule_type})")
    
    def route_by_goal(self, goal_type, context=None):
        """Route tasks based on AI goals and objectives"""
        goal_routing = {
            "learn": {
                "tasks": ["data_collector", "pattern_analyzer", "knowledge_updater"],
                "priority": TaskPriority.HIGH
            },
            "optimize": {
                "tasks": ["performance_analyzer", "code_optimizer", "efficiency_checker"],
                "priority": TaskPriority.NORMAL
            },
            "maintain": {
                "tasks": ["health_check", "cleanup_old_files", "update_configs"],
                "priority": TaskPriority.LOW
            },
            "evolve": {
                "tasks": ["self_modifier", "capability_enhancer", "architecture_updater"],
                "priority": TaskPriority.URGENT
            }
        }
        
        if goal_type in goal_routing:
            route_info = goal_routing[goal_type]
            for task_name in route_info["tasks"]:
                metadata = {
                    "goal_type": goal_type,
                    "context": context,
                    "auto_generated": True
                }
                
                self.add_task(
                    task_name=task_name,
                    task_type=TaskType.AI,
                    priority=route_info["priority"],
                    trigger_source="goal_based",
                    metadata=metadata
                )
            
            self.logger.info(f"Routed {len(route_info['tasks'])} tasks for goal: {goal_type}")
    
    def get_next_task(self):
        """Get the next highest priority task from the queue"""
        if not self.task_queue:
            return None
        
        # Sort by priority (higher number = higher priority)
        self.task_queue.sort(key=lambda x: x["priority"], reverse=True)
        
        # Get the highest priority task
        next_task = self.task_queue.pop(0)
        next_task["status"] = "dispatched"
        
        self.logger.info(f"Dispatching task: {next_task['name']} (Priority: {next_task['priority']})")
        return next_task
    
    def find_script_for_task(self, task_name):
        """Find the appropriate script file for a given task"""
        # Check script registry first
        if task_name in self.script_registry:
            script_info = self.script_registry[task_name]
            if script_info.get("enabled", True):
                return script_info
        
        # Fallback: look for script file directly
        script_path = self.brain_scripts_dir / f"{task_name}.py"
        if script_path.exists():
            return {
                "name": task_name,
                "path": str(script_path),
                "type": "unknown",
                "enabled": True
            }
        
        self.logger.warning(f"No script found for task: {task_name}")
        return None
    
    def route_and_dispatch(self, max_tasks=5):
        """Route and dispatch up to max_tasks from the queue"""
        dispatched = []
        
        for _ in range(min(max_tasks, len(self.task_queue))):
            task = self.get_next_task()
            if task:
                script_info = self.find_script_for_task(task["name"])
                if script_info:
                    task["script_info"] = script_info
                    dispatched.append(task)
                else:
                    self.logger.error(f"Cannot dispatch task {task['name']}: no script found")
        
        return dispatched
    
    def get_queue_status(self):
        """Get current queue status and statistics"""
        total_tasks = len(self.task_queue)
        by_priority = {}
        by_type = {}
        
        for task in self.task_queue:
            priority = task["priority"]
            task_type = task["type"]
            
            by_priority[priority] = by_priority.get(priority, 0) + 1
            by_type[task_type] = by_type.get(task_type, 0) + 1
        
        return {
            "total_tasks": total_tasks,
            "by_priority": by_priority,
            "by_type": by_type,
            "queue": self.task_queue
        }

if __name__ == "__main__":
    router = TaskRouter()
    
    # Example usage
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "test":
            # Test routing
            router.route_discord_command("teach", ["new concept"])
            router.route_by_goal("learn", "testing context")
            router.route_by_schedule("hourly")
            
            print("Queue status:", router.get_queue_status())
            
            # Dispatch some tasks
            dispatched = router.route_and_dispatch(3)
            print(f"Dispatched {len(dispatched)} tasks")
