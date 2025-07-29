#!/usr/bin/env python3
"""
Auto Brain Runner - Orchestrator for Russo Jr's brain logic
Runs brain modules every few hours, manages configs, and fetches data
"""

import os
import sys
import time
import json
import logging
import importlib.util
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

class AutoBrainRunner:
    def __init__(self):
        self.project_root = project_root
        self.brain_scripts_dir = self.project_root / "brain_scripts"
        self.configs_dir = self.project_root / "logs" / "configs"
        self.data_streams_dir = self.project_root / "data_streams"
        self.logs_dir = self.project_root / "logs"
        
        # Setup logging
        self.setup_logging()
        
        # Runtime state
        self.last_run = None
        self.run_interval = 3600  # 1 hour default
        self.active_modules = []
        
    def setup_logging(self):
        """Initialize logging system"""
        self.logs_dir.mkdir(exist_ok=True)
        log_file = self.logs_dir / f"auto_brain_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_script_registry(self):
        """Load the script registry configuration"""
        registry_path = self.configs_dir / "script_registry.json"
        if not registry_path.exists():
            self.logger.warning("Script registry not found, creating empty registry")
            return {}
            
        try:
            with open(registry_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load script registry: {e}")
            return {}
    
    def discover_brain_modules(self):
        """Discover available modules in brain_scripts directory"""
        if not self.brain_scripts_dir.exists():
            self.logger.warning("Brain scripts directory not found")
            return []
            
        modules = []
        for file_path in self.brain_scripts_dir.glob("*.py"):
            if file_path.name.startswith("__"):
                continue
            modules.append({
                "name": file_path.stem,
                "path": str(file_path),
                "modified": file_path.stat().st_mtime
            })
        
        self.logger.info(f"Discovered {len(modules)} brain modules")
        return modules
    
    def load_module(self, module_info):
        """Dynamically load a brain module"""
        try:
            spec = importlib.util.spec_from_file_location(
                module_info["name"], 
                module_info["path"]
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        except Exception as e:
            self.logger.error(f"Failed to load module {module_info['name']}: {e}")
            return None
    
    def execute_brain_cycle(self):
        """Execute one complete brain cycle"""
        self.logger.info("Starting brain cycle execution")
        
        # Load registry and discover modules
        registry = self.load_script_registry()
        available_modules = self.discover_brain_modules()
        
        executed_count = 0
        for module_info in available_modules:
            module_name = module_info["name"]
            
            # Check if module is enabled in registry
            if module_name in registry:
                if not registry[module_name].get("enabled", True):
                    self.logger.info(f"Skipping disabled module: {module_name}")
                    continue
            
            # Load and execute module
            module = self.load_module(module_info)
            if module and hasattr(module, 'main'):
                try:
                    self.logger.info(f"Executing module: {module_name}")
                    module.main()
                    executed_count += 1
                except Exception as e:
                    self.logger.error(f"Module {module_name} execution failed: {e}")
            else:
                self.logger.warning(f"Module {module_name} has no main() function")
        
        self.logger.info(f"Brain cycle completed. Executed {executed_count} modules")
        self.last_run = datetime.now()
    
    def should_run(self):
        """Check if it's time for another brain cycle"""
        if self.last_run is None:
            return True
        
        time_since_last = datetime.now() - self.last_run
        return time_since_last.total_seconds() >= self.run_interval
    
    def run_forever(self):
        """Main loop - run brain cycles continuously"""
        self.logger.info("Auto Brain Runner started")
        
        while True:
            try:
                if self.should_run():
                    self.execute_brain_cycle()
                else:
                    # Sleep for a short time before checking again
                    time.sleep(60)  # Check every minute
                    
            except KeyboardInterrupt:
                self.logger.info("Auto Brain Runner stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in main loop: {e}")
                time.sleep(300)  # Wait 5 minutes before retrying
    
    def run_once(self):
        """Run a single brain cycle (useful for testing)"""
        self.logger.info("Running single brain cycle")
        self.execute_brain_cycle()

if __name__ == "__main__":
    runner = AutoBrainRunner()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        runner.run_once()
    else:
        runner.run_forever()
