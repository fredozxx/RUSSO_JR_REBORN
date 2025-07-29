#!/usr/bin/env python3
"""
Mode Shifter - Detects changes in Discord commands and adjusts strategies
Updates mode config files and modifies execution order in task_router.py
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

class OperationalMode(Enum):
    ACTIVE = "active"
    PASSIVE = "passive" 
    LEARNING = "learning"
    MAINTENANCE = "maintenance"
    EVOLUTION = "evolution"

class GoalType(Enum):
    LEARN = "learn"
    OPTIMIZE = "optimize"
    MAINTAIN = "maintain"
    EVOLVE = "evolve"

class ModeShifter:
    def __init__(self):
        self.project_root = project_root
        self.configs_dir = self.project_root / "logs" / "configs"
        self.logs_dir = self.project_root / "logs"
        self.deploy_dir = self.project_root / "deploy"
        
        # Current state
        self.current_mode = OperationalMode.LEARNING
        self.current_goal = None
        self.mode_history = []
        
        # Mode configurations
        self.mode_configs = self.load_mode_configurations()
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Initialize logging system"""
        self.logs_dir.mkdir(exist_ok=True)
        log_file = self.logs_dir / f"mode_shifter_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_mode_configurations(self):
        """Load mode-specific configurations"""
        return {
            OperationalMode.ACTIVE: {
                "priority_modules": ["data_collector", "task_executor", "discord_listener"],
                "execution_frequency": 300,  # 5 minutes
                "max_concurrent_tasks": 5,
                "resource_usage": "high",
                "monitoring_level": "detailed",
                "auto_responses": True
            },
            OperationalMode.PASSIVE: {
                "priority_modules": ["health_check", "status_report"],
                "execution_frequency": 3600,  # 1 hour
                "max_concurrent_tasks": 2,
                "resource_usage": "low",
                "monitoring_level": "basic",
                "auto_responses": False
            },
            OperationalMode.LEARNING: {
                "priority_modules": ["learning_module", "data_analyzer", "pattern_analyzer"],
                "execution_frequency": 900,  # 15 minutes
                "max_concurrent_tasks": 3,
                "resource_usage": "medium",
                "monitoring_level": "detailed",
                "auto_responses": True,
                "focus_areas": ["data_analysis", "pattern_recognition", "knowledge_building"]
            },
            OperationalMode.MAINTENANCE: {
                "priority_modules": ["log_rotator", "backup_manager", "cleanup_old_files"],
                "execution_frequency": 1800,  # 30 minutes
                "max_concurrent_tasks": 2,
                "resource_usage": "low",
                "monitoring_level": "basic",
                "auto_responses": False,
                "maintenance_tasks": ["cleanup", "optimization", "health_checks"]
            },
            OperationalMode.EVOLUTION: {
                "priority_modules": ["auto_upgrader", "capability_enhancer", "architecture_updater"],
                "execution_frequency": 600,  # 10 minutes
                "max_concurrent_tasks": 4,
                "resource_usage": "high",
                "monitoring_level": "detailed",
                "auto_responses": True,
                "evolution_focus": ["self_improvement", "capability_expansion", "efficiency"]
            }
        }
    
    def load_current_mode_config(self):
        """Load the current mode configuration from file"""
        mode_config_path = self.configs_dir / "mode_config.json"
        
        if mode_config_path.exists():
            try:
                with open(mode_config_path, 'r') as f:
                    config = json.load(f)
                    
                # Update current state from config
                self.current_mode = OperationalMode(config.get("current_mode", "learning"))
                self.current_goal = config.get("current_goal")
                self.mode_history = config.get("mode_history", [])
                
                self.logger.info(f"Loaded mode config: {self.current_mode.value}")
                return config
                
            except Exception as e:
                self.logger.error(f"Failed to load mode config: {e}")
                return self.create_default_mode_config()
        else:
            return self.create_default_mode_config()
    
    def create_default_mode_config(self):
        """Create default mode configuration"""
        default_config = {
            "current_mode": self.current_mode.value,
            "current_goal": self.current_goal,
            "mode_history": [],
            "last_updated": datetime.now().isoformat(),
            "auto_mode_switching": True,
            "mode_switch_conditions": {
                "error_threshold": 5,
                "performance_threshold": 0.7,
                "idle_timeout": 7200  # 2 hours
            }
        }
        
        self.save_mode_config(default_config)
        return default_config
    
    def save_mode_config(self, config):
        """Save mode configuration to file"""
        self.configs_dir.mkdir(parents=True, exist_ok=True)
        mode_config_path = self.configs_dir / "mode_config.json"
        
        try:
            with open(mode_config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.logger.info("Mode configuration saved")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save mode config: {e}")
            return False
    
    def detect_mode_change_request(self):
        """Detect mode change requests from Discord commands or system conditions"""
        mode_changes = []
        
        # Check Discord command logs for mode changes
        discord_log = self.logs_dir / f"discord_listener_{datetime.now().strftime('%Y%m%d')}.log"
        if discord_log.exists():
            try:
                with open(discord_log, 'r') as f:
                    content = f.read()
                
                # Look for mode change commands
                import re
                mode_patterns = [
                    r'Mode command from user .+: (\w+)',
                    r'Goal command from user .+: (\w+)',
                    r'/mode (\w+)',
                    r'/goal (\w+)'
                ]
                
                for pattern in mode_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        if match in [mode.value for mode in OperationalMode]:
                            mode_changes.append({
                                "type": "mode_change",
                                "target": match,
                                "source": "discord_command",
                                "timestamp": datetime.now().isoformat()
                            })
                        elif match in [goal.value for goal in GoalType]:
                            mode_changes.append({
                                "type": "goal_change", 
                                "target": match,
                                "source": "discord_command",
                                "timestamp": datetime.now().isoformat()
                            })
                            
            except Exception as e:
                self.logger.error(f"Failed to parse Discord logs: {e}")
        
        # Check system conditions for automatic mode switching
        auto_changes = self.detect_automatic_mode_changes()
        mode_changes.extend(auto_changes)
        
        return mode_changes
    
    def detect_automatic_mode_changes(self):
        """Detect conditions that should trigger automatic mode changes"""
        auto_changes = []
        
        try:
            # Check error rates
            error_count = self.count_recent_errors()
            if error_count > 5 and self.current_mode != OperationalMode.MAINTENANCE:
                auto_changes.append({
                    "type": "mode_change",
                    "target": "maintenance",
                    "source": "high_error_rate",
                    "reason": f"Error count: {error_count}",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Check if system has been idle
            last_activity = self.get_last_activity_time()
            if last_activity and (datetime.now() - last_activity).total_seconds() > 7200:  # 2 hours
                if self.current_mode == OperationalMode.ACTIVE:
                    auto_changes.append({
                        "type": "mode_change",
                        "target": "passive",
                        "source": "idle_timeout",
                        "reason": "System idle for 2+ hours",
                        "timestamp": datetime.now().isoformat()
                    })
            
            # Check performance metrics
            performance = self.get_system_performance()
            if performance and performance < 0.7:
                if self.current_mode != OperationalMode.MAINTENANCE:
                    auto_changes.append({
                        "type": "mode_change",
                        "target": "maintenance",
                        "source": "low_performance",
                        "reason": f"Performance: {performance:.2f}",
                        "timestamp": datetime.now().isoformat()
                    })
                    
        except Exception as e:
            self.logger.error(f"Failed to detect automatic mode changes: {e}")
        
        return auto_changes
    
    def count_recent_errors(self):
        """Count errors in the last hour"""
        error_count = 0
        cutoff_time = datetime.now().timestamp() - 3600  # 1 hour ago
        
        try:
            for log_file in self.logs_dir.glob("*.log"):
                if log_file.stat().st_mtime > cutoff_time:
                    with open(log_file, 'r') as f:
                        content = f.read()
                        error_count += content.count("ERROR")
                        error_count += content.count("CRITICAL")
        except Exception:
            pass
        
        return error_count
    
    def get_last_activity_time(self):
        """Get the timestamp of the last system activity"""
        try:
            latest_time = None
            for log_file in self.logs_dir.glob("*.log"):
                file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                if latest_time is None or file_time > latest_time:
                    latest_time = file_time
            return latest_time
        except Exception:
            return None
    
    def get_system_performance(self):
        """Get current system performance metric"""
        try:
            # Check task execution success rate
            executor_log = self.logs_dir / f"task_executor_{datetime.now().strftime('%Y%m%d')}.log"
            if executor_log.exists():
                with open(executor_log, 'r') as f:
                    content = f.read()
                
                success_count = content.count("completed successfully")
                failure_count = content.count("failed after")
                
                if success_count + failure_count > 0:
                    return success_count / (success_count + failure_count)
            
            return None
        except Exception:
            return None
    
    def apply_mode_change(self, mode_change):
        """Apply a mode or goal change"""
        change_type = mode_change.get("type")
        target = mode_change.get("target")
        source = mode_change.get("source")
        
        self.logger.info(f"Applying {change_type}: {target} (source: {source})")
        
        if change_type == "mode_change":
            return self.switch_mode(target, source, mode_change.get("reason"))
        elif change_type == "goal_change":
            return self.set_goal(target, source)
        
        return False
    
    def switch_mode(self, new_mode, source="manual", reason=None):
        """Switch to a new operational mode"""
        try:
            new_mode_enum = OperationalMode(new_mode)
        except ValueError:
            self.logger.error(f"Invalid mode: {new_mode}")
            return False
        
        if new_mode_enum == self.current_mode:
            self.logger.info(f"Already in mode: {new_mode}")
            return True
        
        old_mode = self.current_mode
        self.current_mode = new_mode_enum
        
        # Record mode change in history
        mode_change_record = {
            "from_mode": old_mode.value,
            "to_mode": new_mode_enum.value,
            "source": source,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
        
        self.mode_history.append(mode_change_record)
        
        # Update mode configuration file
        config = {
            "current_mode": self.current_mode.value,
            "current_goal": self.current_goal,
            "mode_history": self.mode_history,
            "last_updated": datetime.now().isoformat(),
            "auto_mode_switching": True
        }
        
        if self.save_mode_config(config):
            # Update task router priorities
            self.update_task_router_priorities()
            
            # Update brain runner frequency
            self.update_brain_runner_frequency()
            
            self.logger.info(f"Successfully switched from {old_mode.value} to {new_mode_enum.value}")
            return True
        else:
            # Revert mode change if save failed
            self.current_mode = old_mode
            self.logger.error(f"Failed to save mode config, reverting to {old_mode.value}")
            return False
    
    def set_goal(self, new_goal, source="manual"):
        """Set a new goal and adjust mode accordingly"""
        try:
            new_goal_enum = GoalType(new_goal)
        except ValueError:
            self.logger.error(f"Invalid goal: {new_goal}")
            return False
        
        old_goal = self.current_goal
        self.current_goal = new_goal_enum.value
        
        # Suggest mode changes based on goal
        goal_mode_mapping = {
            GoalType.LEARN: OperationalMode.LEARNING,
            GoalType.OPTIMIZE: OperationalMode.ACTIVE,
            GoalType.MAINTAIN: OperationalMode.MAINTENANCE,
            GoalType.EVOLVE: OperationalMode.EVOLUTION
        }
        
        suggested_mode = goal_mode_mapping.get(new_goal_enum)
        if suggested_mode and suggested_mode != self.current_mode:
            self.logger.info(f"Goal '{new_goal}' suggests mode change to '{suggested_mode.value}'")
            self.switch_mode(suggested_mode.value, f"goal_based_{source}", f"Goal: {new_goal}")
        
        self.logger.info(f"Goal changed from '{old_goal}' to '{new_goal}'")
        return True
    
    def update_task_router_priorities(self):
        """Update task_router.py with new priority configurations"""
        mode_config = self.mode_configs.get(self.current_mode, {})
        priority_modules = mode_config.get("priority_modules", [])
        
        # Create priority adjustment data
        priority_data = {
            "mode": self.current_mode.value,
            "priority_modules": priority_modules,
            "max_concurrent_tasks": mode_config.get("max_concurrent_tasks", 3),
            "execution_frequency": mode_config.get("execution_frequency", 900),
            "updated": datetime.now().isoformat()
        }
        
        # Save priority configuration
        priority_config_path = self.configs_dir / "task_priority_config.json"
        try:
            with open(priority_config_path, 'w') as f:
                json.dump(priority_data, f, indent=2)
            
            self.logger.info(f"Updated task router priorities for mode: {self.current_mode.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update task router priorities: {e}")
            return False
    
    def update_brain_runner_frequency(self):
        """Update auto_brain_runner.py execution frequency"""
        mode_config = self.mode_configs.get(self.current_mode, {})
        execution_frequency = mode_config.get("execution_frequency", 900)
        
        # Create brain runner configuration
        runner_config = {
            "mode": self.current_mode.value,
            "execution_frequency": execution_frequency,
            "resource_usage": mode_config.get("resource_usage", "medium"),
            "monitoring_level": mode_config.get("monitoring_level", "basic"),
            "updated": datetime.now().isoformat()
        }
        
        # Save runner configuration
        runner_config_path = self.configs_dir / "brain_runner_config.json"
        try:
            with open(runner_config_path, 'w') as f:
                json.dump(runner_config, f, indent=2)
            
            self.logger.info(f"Updated brain runner frequency: {execution_frequency}s")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update brain runner config: {e}")
            return False
    
    def run_mode_shift_cycle(self):
        """Run a complete mode shifting cycle"""
        self.logger.info("Starting mode shift cycle")
        
        # Load current configuration
        self.load_current_mode_config()
        
        # Detect change requests
        mode_changes = self.detect_mode_change_request()
        
        if not mode_changes:
            self.logger.info("No mode changes detected")
            return True
        
        self.logger.info(f"Processing {len(mode_changes)} mode change requests")
        
        # Apply changes
        changes_applied = 0
        for change in mode_changes:
            if self.apply_mode_change(change):
                changes_applied += 1
        
        self.logger.info(f"Applied {changes_applied}/{len(mode_changes)} mode changes")
        return changes_applied > 0
    
    def get_current_status(self):
        """Get current mode and goal status"""
        return {
            "current_mode": self.current_mode.value,
            "current_goal": self.current_goal,
            "mode_history": self.mode_history[-5:],  # Last 5 changes
            "system_performance": self.get_system_performance(),
            "error_count": self.count_recent_errors(),
            "last_activity": self.get_last_activity_time().isoformat() if self.get_last_activity_time() else None
        }

def main(task_info=None):
    """Main entry point for mode shifter"""
    shifter = ModeShifter()
    return shifter.run_mode_shift_cycle()

if __name__ == "__main__":
    result = main()
    print(f"Mode shift result: {result}")
