#!/usr/bin/env python3
"""
Brain Loader - Loads configurations, metadata, and knowledge files into memory
Used by auto_brain_runner.py before brain cycles begin
"""

import os
import sys
import json
import logging
import pickle
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

class BrainLoader:
    def __init__(self):
        self.project_root = project_root
        self.brain_scripts_dir = self.project_root / "brain_scripts"
        self.configs_dir = self.project_root / "logs" / "configs"
        self.data_streams_dir = self.project_root / "data_streams"
        self.logs_dir = self.project_root / "logs"
        
        # Memory storage
        self.loaded_configs = {}
        self.loaded_metadata = {}
        self.brain_stats = {}
        self.knowledge_base = {}
        self.memory_files = {}
        
        # Setup logging
        self.setup_logging()
        
        # Load state
        self.load_timestamp = None
        self.last_load_successful = False
        
    def setup_logging(self):
        """Initialize logging system"""
        self.logs_dir.mkdir(exist_ok=True)
        log_file = self.logs_dir / f"brain_loader_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_script_registry(self) -> Dict[str, Any]:
        """Load script registry configuration"""
        registry_path = self.configs_dir / "script_registry.json"
        
        if not registry_path.exists():
            self.logger.warning("Script registry not found, creating default")
            return self.create_default_registry()
        
        try:
            with open(registry_path, 'r') as f:
                registry = json.load(f)
            
            self.logger.info(f"Loaded script registry with {len(registry)} modules")
            return registry
            
        except Exception as e:
            self.logger.error(f"Failed to load script registry: {e}")
            return {}
    
    def create_default_registry(self) -> Dict[str, Any]:
        """Create a default script registry"""
        default_registry = {
            "learning_module": {
                "name": "learning_module",
                "version": "1.0.0",
                "enabled": True,
                "type": "AI",
                "description": "Core learning and adaptation module"
            },
            "data_collector": {
                "name": "data_collector", 
                "version": "1.0.0",
                "enabled": True,
                "type": "data",
                "description": "Collects data from various sources"
            }
        }
        
        # Save default registry
        registry_path = self.configs_dir / "script_registry.json"
        try:
            self.configs_dir.mkdir(parents=True, exist_ok=True)
            with open(registry_path, 'w') as f:
                json.dump(default_registry, f, indent=2)
            self.logger.info("Created default script registry")
        except Exception as e:
            self.logger.error(f"Failed to save default registry: {e}")
        
        return default_registry
    
    def load_brain_config(self) -> Dict[str, Any]:
        """Load brain configuration and statistics"""
        brain_config_path = self.configs_dir / "brain_config.json"
        
        if not brain_config_path.exists():
            self.logger.info("Brain config not found, creating default")
            return self.create_default_brain_config()
        
        try:
            with open(brain_config_path, 'r') as f:
                brain_config = json.load(f)
            
            self.logger.info("Loaded brain configuration")
            return brain_config
            
        except Exception as e:
            self.logger.error(f"Failed to load brain config: {e}")
            return self.create_default_brain_config()
    
    def create_default_brain_config(self) -> Dict[str, Any]:
        """Create default brain configuration"""
        default_config = {
            "version": "1.0.0",
            "created": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "statistics": {
                "total_cycles": 0,
                "successful_cycles": 0,
                "failed_cycles": 0,
                "total_modules_executed": 0,
                "average_cycle_duration": 0.0,
                "last_cycle_time": None
            },
            "performance_metrics": {
                "memory_usage": 0,
                "cpu_usage": 0,
                "success_rate": 100.0,
                "error_rate": 0.0
            },
            "learning_stats": {
                "concepts_learned": 0,
                "patterns_recognized": 0,
                "knowledge_base_size": 0,
                "last_learning_session": None
            },
            "operational_settings": {
                "max_memory_usage_mb": 1024,
                "max_execution_time_minutes": 60,
                "auto_learning_enabled": True,
                "auto_optimization_enabled": True,
                "debug_mode": False
            }
        }
        
        # Save default config
        brain_config_path = self.configs_dir / "brain_config.json"
        try:
            self.configs_dir.mkdir(parents=True, exist_ok=True)
            with open(brain_config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            self.logger.info("Created default brain configuration")
        except Exception as e:
            self.logger.error(f"Failed to save default brain config: {e}")
        
        return default_config
    
    def load_mode_config(self) -> Dict[str, Any]:
        """Load current mode configuration"""
        mode_config_path = self.configs_dir / "mode_config.json"
        
        if not mode_config_path.exists():
            self.logger.info("Mode config not found, using defaults")
            return {
                "current_mode": "learning",
                "current_goal": None,
                "mode_history": [],
                "auto_mode_switching": True
            }
        
        try:
            with open(mode_config_path, 'r') as f:
                mode_config = json.load(f)
            
            self.logger.info(f"Loaded mode config: {mode_config.get('current_mode', 'unknown')}")
            return mode_config
            
        except Exception as e:
            self.logger.error(f"Failed to load mode config: {e}")
            return {}
    
    def load_task_priority_config(self) -> Dict[str, Any]:
        """Load task priority configuration"""
        priority_config_path = self.configs_dir / "task_priority_config.json"
        
        if not priority_config_path.exists():
            return {}
        
        try:
            with open(priority_config_path, 'r') as f:
                priority_config = json.load(f)
            
            self.logger.info("Loaded task priority configuration")
            return priority_config
            
        except Exception as e:
            self.logger.error(f"Failed to load task priority config: {e}")
            return {}
    
    def load_memory_files(self) -> Dict[str, Any]:
        """Load .mem and knowledge files"""
        memory_data = {}
        
        # Look for .mem files in various directories
        search_dirs = [
            self.data_streams_dir,
            self.configs_dir,
            self.brain_scripts_dir,
            self.project_root
        ]
        
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
                
            # Load .mem files (pickled data)
            for mem_file in search_dir.glob("*.mem"):
                try:
                    with open(mem_file, 'rb') as f:
                        data = pickle.load(f)
                    
                    memory_data[mem_file.stem] = {
                        "type": "memory",
                        "data": data,
                        "path": str(mem_file),
                        "loaded_at": datetime.now().isoformat()
                    }
                    
                    self.logger.info(f"Loaded memory file: {mem_file.name}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to load memory file {mem_file}: {e}")
            
            # Load knowledge files (.knowledge, .kb, .txt with specific naming)
            knowledge_patterns = ["*.knowledge", "*.kb", "*knowledge*.txt", "*brain*.txt"]
            
            for pattern in knowledge_patterns:
                for knowledge_file in search_dir.glob(pattern):
                    try:
                        with open(knowledge_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        memory_data[knowledge_file.stem] = {
                            "type": "knowledge",
                            "data": content,
                            "path": str(knowledge_file),
                            "loaded_at": datetime.now().isoformat(),
                            "size": len(content)
                        }
                        
                        self.logger.info(f"Loaded knowledge file: {knowledge_file.name}")
                        
                    except Exception as e:
                        self.logger.error(f"Failed to load knowledge file {knowledge_file}: {e}")
        
        self.logger.info(f"Loaded {len(memory_data)} memory/knowledge files")
        return memory_data
    
    def load_data_streams(self) -> Dict[str, Any]:
        """Load data from data_streams directory"""
        data_streams = {}
        
        if not self.data_streams_dir.exists():
            self.logger.info("Data streams directory not found")
            return data_streams
        
        # Load JSON data files
        for json_file in self.data_streams_dir.glob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                data_streams[json_file.stem] = {
                    "type": "json_data",
                    "data": data,
                    "path": str(json_file),
                    "loaded_at": datetime.now().isoformat()
                }
                
                self.logger.info(f"Loaded data stream: {json_file.name}")
                
            except Exception as e:
                self.logger.error(f"Failed to load data stream {json_file}: {e}")
        
        # Load CSV data files
        for csv_file in self.data_streams_dir.glob("*.csv"):
            try:
                # Simple CSV reading without pandas dependency
                with open(csv_file, 'r') as f:
                    lines = f.readlines()
                
                if lines:
                    headers = lines[0].strip().split(',')
                    rows = []
                    for line in lines[1:]:
                        rows.append(line.strip().split(','))
                    
                    data_streams[csv_file.stem] = {
                        "type": "csv_data",
                        "headers": headers,
                        "data": rows,
                        "path": str(csv_file),
                        "loaded_at": datetime.now().isoformat(),
                        "rows": len(rows)
                    }
                    
                    self.logger.info(f"Loaded CSV data: {csv_file.name} ({len(rows)} rows)")
                
            except Exception as e:
                self.logger.error(f"Failed to load CSV data {csv_file}: {e}")
        
        # Load text data files
        for txt_file in self.data_streams_dir.glob("*.txt"):
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                data_streams[txt_file.stem] = {
                    "type": "text_data",
                    "data": content,
                    "path": str(txt_file),
                    "loaded_at": datetime.now().isoformat(),
                    "size": len(content)
                }
                
                self.logger.info(f"Loaded text data: {txt_file.name}")
                
            except Exception as e:
                self.logger.error(f"Failed to load text data {txt_file}: {e}")
        
        self.logger.info(f"Loaded {len(data_streams)} data streams")
        return data_streams
    
    def update_brain_stats(self, cycle_info: Dict[str, Any]):
        """Update brain statistics after a cycle"""
        if "statistics" not in self.brain_stats:
            self.brain_stats["statistics"] = {}
        
        stats = self.brain_stats["statistics"]
        
        # Update cycle statistics
        stats["total_cycles"] = stats.get("total_cycles", 0) + 1
        
        if cycle_info.get("success", False):
            stats["successful_cycles"] = stats.get("successful_cycles", 0) + 1
        else:
            stats["failed_cycles"] = stats.get("failed_cycles", 0) + 1
        
        # Update execution statistics
        modules_executed = cycle_info.get("modules_executed", 0)
        stats["total_modules_executed"] = stats.get("total_modules_executed", 0) + modules_executed
        
        # Update timing
        cycle_duration = cycle_info.get("duration", 0)
        total_cycles = stats["total_cycles"]
        current_avg = stats.get("average_cycle_duration", 0)
        
        # Calculate new average
        stats["average_cycle_duration"] = ((current_avg * (total_cycles - 1)) + cycle_duration) / total_cycles
        stats["last_cycle_time"] = datetime.now().isoformat()
        
        # Update performance metrics
        if "performance_metrics" not in self.brain_stats:
            self.brain_stats["performance_metrics"] = {}
        
        perf = self.brain_stats["performance_metrics"]
        perf["success_rate"] = (stats["successful_cycles"] / stats["total_cycles"]) * 100
        perf["error_rate"] = (stats["failed_cycles"] / stats["total_cycles"]) * 100
        
        # Save updated stats
        self.save_brain_stats()
    
    def save_brain_stats(self):
        """Save brain statistics to file"""
        brain_config_path = self.configs_dir / "brain_config.json"
        
        try:
            self.brain_stats["last_updated"] = datetime.now().isoformat()
            
            with open(brain_config_path, 'w') as f:
                json.dump(self.brain_stats, f, indent=2)
            
            self.logger.debug("Brain statistics saved")
            
        except Exception as e:
            self.logger.error(f"Failed to save brain statistics: {e}")
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get summary of loaded memory and configurations"""
        return {
            "configs_loaded": len(self.loaded_configs),
            "metadata_entries": len(self.loaded_metadata),
            "memory_files": len(self.memory_files),
            "knowledge_entries": len([k for k, v in self.memory_files.items() if v.get("type") == "knowledge"]),
            "data_streams": len([k for k, v in self.memory_files.items() if "data" in v.get("type", "")]),
            "load_timestamp": self.load_timestamp,
            "last_load_successful": self.last_load_successful,
            "brain_stats_available": bool(self.brain_stats)
        }
    
    def run_full_load(self) -> Dict[str, Any]:
        """Run complete brain loading cycle"""
        self.logger.info("Starting brain loading cycle")
        self.load_timestamp = datetime.now()
        
        try:
            # Load all configurations
            self.loaded_configs["script_registry"] = self.load_script_registry()
            self.loaded_configs["brain_config"] = self.load_brain_config()
            self.loaded_configs["mode_config"] = self.load_mode_config()
            self.loaded_configs["task_priority_config"] = self.load_task_priority_config()
            
            # Store brain stats reference
            self.brain_stats = self.loaded_configs["brain_config"]
            
            # Load memory and knowledge files
            self.memory_files = self.load_memory_files()
            
            # Load data streams
            data_streams = self.load_data_streams()
            self.memory_files.update(data_streams)
            
            # Build knowledge base
            self.knowledge_base = {
                name: data["data"] 
                for name, data in self.memory_files.items() 
                if data.get("type") == "knowledge"
            }
            
            self.last_load_successful = True
            
            # Create summary
            summary = {
                "success": True,
                "load_timestamp": self.load_timestamp.isoformat(),
                "configs_loaded": len(self.loaded_configs),
                "memory_files_loaded": len(self.memory_files),
                "knowledge_base_entries": len(self.knowledge_base),
                "total_memory_items": len(self.memory_files)
            }
            
            self.logger.info(f"Brain loading completed successfully: {summary}")
            return summary
            
        except Exception as e:
            self.last_load_successful = False
            error_msg = f"Brain loading failed: {e}"
            self.logger.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "load_timestamp": self.load_timestamp.isoformat() if self.load_timestamp else None
            }
    
    def get_config(self, config_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific configuration"""
        return self.loaded_configs.get(config_name)
    
    def get_memory_data(self, memory_name: str) -> Optional[Any]:
        """Get specific memory data"""
        memory_entry = self.memory_files.get(memory_name)
        return memory_entry.get("data") if memory_entry else None
    
    def get_knowledge(self, knowledge_name: str) -> Optional[str]:
        """Get specific knowledge content"""
        return self.knowledge_base.get(knowledge_name)
    
    def is_loaded(self) -> bool:
        """Check if brain data has been loaded"""
        return self.last_load_successful and self.load_timestamp is not None

def main(task_info=None):
    """Main entry point for brain loader"""
    loader = BrainLoader()
    result = loader.run_full_load()
    
    # If called with task_info, update cycle stats
    if task_info and result.get("success"):
        cycle_info = {
            "success": True,
            "modules_executed": 1,
            "duration": 0.1,  # Minimal duration for loading
            "task_id": task_info.get("id")
        }
        loader.update_brain_stats(cycle_info)
    
    return result

if __name__ == "__main__":
    result = main()
    print(f"Brain loading result: {result}")
