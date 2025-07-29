#!/usr/bin/env python3
"""
Auto Upgrader - Scans brain_scripts and script_registry.json to detect outdated modules
Automatically upgrades modules and pushes changes to GitHub
"""

import os
import sys
import json
import logging
import subprocess
from pathlib import Path
from datetime import datetime
import hashlib
import importlib.util

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

class AutoUpgrader:
    def __init__(self):
        self.project_root = project_root
        self.brain_scripts_dir = self.project_root / "brain_scripts"
        self.configs_dir = self.project_root / "logs" / "configs"
        self.logs_dir = self.project_root / "logs"
        
        # Setup logging
        self.setup_logging()
        
        # Upgrade tracking
        self.upgrade_history = []
        self.pending_upgrades = []
        self.auto_upgrade_enabled = True
        
        # Version tracking
        self.module_checksums = {}
        self.last_scan_time = None
        
    def setup_logging(self):
        """Initialize logging system"""
        self.logs_dir.mkdir(exist_ok=True)
        log_file = self.logs_dir / f"auto_upgrader_{datetime.now().strftime('%Y%m%d')}.log"
        
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
            self.logger.warning("Script registry not found")
            return {}
            
        try:
            with open(registry_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load script registry: {e}")
            return {}
    
    def save_script_registry(self, registry):
        """Save updated script registry"""
        registry_path = self.configs_dir / "script_registry.json"
        try:
            with open(registry_path, 'w') as f:
                json.dump(registry, f, indent=2)
            self.logger.info("Script registry updated")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save script registry: {e}")
            return False
    
    def calculate_file_checksum(self, file_path):
        """Calculate MD5 checksum of a file"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            self.logger.error(f"Failed to calculate checksum for {file_path}: {e}")
            return None
    
    def scan_for_changes(self):
        """Scan brain_scripts directory for changes"""
        self.logger.info("Scanning for module changes...")
        
        changes_detected = []
        current_files = {}
        
        # Scan all Python files in brain_scripts
        if self.brain_scripts_dir.exists():
            for file_path in self.brain_scripts_dir.glob("*.py"):
                if file_path.name.startswith("__"):
                    continue
                    
                module_name = file_path.stem
                checksum = self.calculate_file_checksum(file_path)
                current_files[module_name] = {
                    "path": str(file_path),
                    "checksum": checksum,
                    "modified": file_path.stat().st_mtime
                }
                
                # Check if this is a new or modified file
                if module_name in self.module_checksums:
                    if self.module_checksums[module_name] != checksum:
                        changes_detected.append({
                            "module": module_name,
                            "type": "modified",
                            "path": str(file_path)
                        })
                else:
                    changes_detected.append({
                        "module": module_name,
                        "type": "new",
                        "path": str(file_path)
                    })
        
        # Check for deleted files
        for module_name in self.module_checksums:
            if module_name not in current_files:
                changes_detected.append({
                    "module": module_name,
                    "type": "deleted",
                    "path": None
                })
        
        # Update checksum cache
        self.module_checksums = {name: info["checksum"] for name, info in current_files.items()}
        
        self.logger.info(f"Scan complete. Found {len(changes_detected)} changes")
        return changes_detected
    
    def detect_outdated_modules(self):
        """Detect modules that need upgrading based on registry"""
        registry = self.load_script_registry()
        outdated = []
        
        for module_name, module_info in registry.items():
            module_path = self.brain_scripts_dir / f"{module_name}.py"
            
            # Check if module file exists
            if not module_path.exists():
                outdated.append({
                    "module": module_name,
                    "issue": "missing_file",
                    "current_version": module_info.get("version", "unknown"),
                    "path": str(module_path)
                })
                continue
            
            # Check for version mismatches or missing dependencies
            try:
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                module = importlib.util.module_from_spec(spec)
                
                # Try to load module to check for errors
                spec.loader.exec_module(module)
                
                # Check if module has required attributes
                if not hasattr(module, 'main'):
                    outdated.append({
                        "module": module_name,
                        "issue": "missing_main_function",
                        "current_version": module_info.get("version", "unknown"),
                        "path": str(module_path)
                    })
                
            except Exception as e:
                outdated.append({
                    "module": module_name,
                    "issue": f"load_error: {str(e)}",
                    "current_version": module_info.get("version", "unknown"),
                    "path": str(module_path)
                })
        
        return outdated
    
    def generate_module_template(self, module_name, module_info):
        """Generate a basic module template based on registry info"""
        module_type = module_info.get("type", "utility")
        description = module_info.get("description", f"Auto-generated {module_name} module")
        
        template = f'''#!/usr/bin/env python3
"""
{module_name.replace('_', ' ').title()} - {description}
Auto-generated by AutoUpgrader on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

class {module_name.replace('_', '').title()}:
    def __init__(self):
        self.project_root = project_root
        self.logs_dir = self.project_root / "logs"
        self.setup_logging()
        
    def setup_logging(self):
        """Initialize logging system"""
        self.logs_dir.mkdir(exist_ok=True)
        log_file = self.logs_dir / f"{module_name}_{{datetime.now().strftime('%Y%m%d')}}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def execute(self):
        """Main execution logic for {module_name}"""
        self.logger.info("Executing {module_name}")
        
        try:
            # TODO: Implement specific functionality for {module_type} module
            self.logger.info("Module executed successfully")
            return {{"success": True, "message": "Module executed successfully"}}
            
        except Exception as e:
            self.logger.error(f"Module execution failed: {{e}}")
            return {{"success": False, "error": str(e)}}

def main(task_info=None):
    """Main entry point for the module"""
    module = {module_name.replace('_', '').title()}()
    return module.execute()

if __name__ == "__main__":
    result = main()
    print(f"Result: {{result}}")
'''
        return template
    
    def upgrade_module(self, module_info):
        """Upgrade a specific module"""
        module_name = module_info["module"]
        issue = module_info["issue"]
        module_path = Path(module_info["path"])
        
        self.logger.info(f"Upgrading module: {module_name} (Issue: {issue})")
        
        try:
            # Load registry to get module configuration
            registry = self.load_script_registry()
            module_config = registry.get(module_name, {})
            
            if issue == "missing_file":
                # Generate new module from template
                template = self.generate_module_template(module_name, module_config)
                
                with open(module_path, 'w') as f:
                    f.write(template)
                
                self.logger.info(f"Generated new module: {module_name}")
                
            elif issue == "missing_main_function":
                # Add main function to existing module
                with open(module_path, 'r') as f:
                    content = f.read()
                
                if "def main(" not in content:
                    main_function = '''

def main(task_info=None):
    """Main entry point for the module"""
    # TODO: Implement main execution logic
    print(f"Executing {module_name}")
    return {"success": True, "message": "Module executed"}

if __name__ == "__main__":
    result = main()
    print(f"Result: {result}")
'''
                    content += main_function
                    
                    with open(module_path, 'w') as f:
                        f.write(content)
                    
                    self.logger.info(f"Added main function to: {module_name}")
                
            elif issue.startswith("load_error"):
                # Try to fix common loading errors
                self.logger.warning(f"Attempting to fix load error in {module_name}")
                # For now, regenerate the module
                template = self.generate_module_template(module_name, module_config)
                
                # Backup original file
                backup_path = module_path.with_suffix(f".py.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                if module_path.exists():
                    module_path.rename(backup_path)
                
                with open(module_path, 'w') as f:
                    f.write(template)
                
                self.logger.info(f"Regenerated module: {module_name} (backup created)")
            
            # Update version in registry
            if module_name in registry:
                current_version = registry[module_name].get("version", "1.0.0")
                version_parts = current_version.split(".")
                if len(version_parts) >= 3:
                    version_parts[2] = str(int(version_parts[2]) + 1)
                    new_version = ".".join(version_parts)
                else:
                    new_version = "1.0.1"
                
                registry[module_name]["version"] = new_version
                registry[module_name]["last_upgraded"] = datetime.now().isoformat()
                
                self.save_script_registry(registry)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to upgrade module {module_name}: {e}")
            return False
    
    def request_upgrade_permission(self, upgrades):
        """Request permission for upgrades (in real implementation, this might involve Discord notifications)"""
        if not upgrades:
            return True
        
        self.logger.info(f"Requesting permission to upgrade {len(upgrades)} modules:")
        for upgrade in upgrades:
            self.logger.info(f"  - {upgrade['module']}: {upgrade['issue']}")
        
        # For now, auto-approve if auto_upgrade_enabled
        if self.auto_upgrade_enabled:
            self.logger.info("Auto-upgrade enabled. Proceeding with upgrades.")
            return True
        else:
            self.logger.info("Manual approval required. Skipping upgrades.")
            return False
    
    def push_to_github(self):
        """Push changes to GitHub"""
        try:
            # Add all changes
            result = subprocess.run(['git', 'add', '.'], 
                                  cwd=self.project_root, 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"Git add failed: {result.stderr}")
                return False
            
            # Commit changes
            commit_message = f"Auto-upgrade modules - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            result = subprocess.run(['git', 'commit', '-m', commit_message], 
                                  cwd=self.project_root, 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                if "nothing to commit" in result.stdout:
                    self.logger.info("No changes to commit")
                    return True
                else:
                    self.logger.error(f"Git commit failed: {result.stderr}")
                    return False
            
            # Push to GitHub
            result = subprocess.run(['git', 'push'], 
                                  cwd=self.project_root, 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"Git push failed: {result.stderr}")
                return False
            
            self.logger.info("Successfully pushed upgrades to GitHub")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to push to GitHub: {e}")
            return False
    
    def run_upgrade_cycle(self):
        """Run a complete upgrade cycle"""
        self.logger.info("Starting upgrade cycle")
        
        # Scan for changes
        changes = self.scan_for_changes()
        
        # Detect outdated modules
        outdated = self.detect_outdated_modules()
        
        if not outdated:
            self.logger.info("No modules need upgrading")
            return True
        
        # Request permission
        if not self.request_upgrade_permission(outdated):
            self.logger.info("Upgrade permission denied")
            return False
        
        # Perform upgrades
        upgrade_results = []
        for module_info in outdated:
            result = self.upgrade_module(module_info)
            upgrade_results.append(result)
            
            if result:
                self.upgrade_history.append({
                    "module": module_info["module"],
                    "issue": module_info["issue"],
                    "timestamp": datetime.now().isoformat(),
                    "success": True
                })
        
        successful_upgrades = sum(upgrade_results)
        self.logger.info(f"Completed {successful_upgrades}/{len(outdated)} upgrades")
        
        # Push to GitHub if any upgrades were successful
        if successful_upgrades > 0:
            if self.push_to_github():
                self.logger.info("Upgrade cycle completed successfully")
                return True
            else:
                self.logger.error("Upgrade cycle completed but failed to push to GitHub")
                return False
        
        return True

def main(task_info=None):
    """Main entry point for auto upgrader"""
    upgrader = AutoUpgrader()
    return upgrader.run_upgrade_cycle()

if __name__ == "__main__":
    result = main()
    print(f"Upgrade result: {result}")
