#!/usr/bin/env python3
"""
Auto Fixer v1 - Monitors logs and runtime exceptions to automatically fix modules
Attempts to rebuild failed modules based on context from script_registry.json
"""

import os
import sys
import json
import logging
import traceback
import re
from pathlib import Path
from datetime import datetime, timedelta
import importlib.util

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

class AutoFixerV1:
    def __init__(self):
        self.project_root = project_root
        self.brain_scripts_dir = self.project_root / "brain_scripts"
        self.configs_dir = self.project_root / "logs" / "configs"
        self.logs_dir = self.project_root / "logs"
        
        # Error tracking
        self.error_patterns = {}
        self.fix_history = []
        self.monitored_errors = []
        
        # Setup logging
        self.setup_logging()
        
        # Common error patterns and their fixes
        self.error_fixes = {
            "ModuleNotFoundError": self.fix_missing_module,
            "AttributeError": self.fix_missing_attribute,
            "NameError": self.fix_undefined_variable,
            "ImportError": self.fix_import_error,
            "SyntaxError": self.fix_syntax_error,
            "IndentationError": self.fix_indentation_error,
            "TypeError": self.fix_type_error,
            "FileNotFoundError": self.fix_missing_file
        }
        
    def setup_logging(self):
        """Initialize logging system"""
        self.logs_dir.mkdir(exist_ok=True)
        log_file = self.logs_dir / f"auto_fixer_{datetime.now().strftime('%Y%m%d')}.log"
        
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
    
    def monitor_log_files(self):
        """Monitor log files for error patterns"""
        errors_found = []
        
        # Check all log files in the logs directory
        if self.logs_dir.exists():
            for log_file in self.logs_dir.glob("*.log"):
                if log_file.name == "errors.txt" or "error" in log_file.name.lower():
                    errors = self.parse_error_log(log_file)
                    errors_found.extend(errors)
        
        # Also check for errors.txt specifically
        error_file = self.logs_dir / "errors.txt"
        if error_file.exists():
            errors = self.parse_error_log(error_file)
            errors_found.extend(errors)
        
        return errors_found
    
    def parse_error_log(self, log_file):
        """Parse error log file for actionable errors"""
        errors = []
        
        try:
            with open(log_file, 'r') as f:
                content = f.read()
            
            # Look for common error patterns
            error_patterns = [
                r'(ModuleNotFoundError|ImportError): (.+)',
                r'(AttributeError): (.+)',
                r'(NameError): (.+)',
                r'(SyntaxError): (.+)',
                r'(IndentationError): (.+)',
                r'(TypeError): (.+)',
                r'(FileNotFoundError): (.+)',
                r'ERROR - (.+): (.+)',
                r'CRITICAL - (.+): (.+)'
            ]
            
            for pattern in error_patterns:
                matches = re.finditer(pattern, content, re.MULTILINE)
                for match in matches:
                    error_type = match.group(1) if len(match.groups()) >= 2 else "Unknown"
                    error_message = match.group(2) if len(match.groups()) >= 2 else match.group(1)
                    
                    errors.append({
                        "type": error_type,
                        "message": error_message,
                        "source_file": str(log_file),
                        "timestamp": datetime.now().isoformat()
                    })
            
        except Exception as e:
            self.logger.error(f"Failed to parse log file {log_file}: {e}")
        
        return errors
    
    def extract_module_from_error(self, error):
        """Extract module name from error message"""
        message = error.get("message", "")
        
        # Common patterns to extract module names
        patterns = [
            r"No module named '([^']+)'",
            r"module '([^']+)' has no attribute",
            r"in ([a-zA-Z_][a-zA-Z0-9_]*\.py)",
            r"([a-zA-Z_][a-zA-Z0-9_]*) is not defined",
            r"File \"[^\"]*([a-zA-Z_][a-zA-Z0-9_]*\.py)\""
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                module_name = match.group(1)
                if module_name.endswith('.py'):
                    module_name = module_name[:-3]
                return module_name
        
        return None
    
    def fix_missing_module(self, error, module_name):
        """Fix missing module error"""
        self.logger.info(f"Attempting to fix missing module: {module_name}")
        
        # Check if it's a brain_scripts module
        module_path = self.brain_scripts_dir / f"{module_name}.py"
        
        if not module_path.exists():
            # Try to create the module from registry
            registry = self.load_script_registry()
            
            if module_name in registry:
                module_info = registry[module_name]
                template = self.generate_basic_module_template(module_name, module_info)
                
                try:
                    with open(module_path, 'w') as f:
                        f.write(template)
                    
                    self.logger.info(f"Created missing module: {module_name}")
                    return True
                except Exception as e:
                    self.logger.error(f"Failed to create module {module_name}: {e}")
                    return False
            else:
                self.logger.warning(f"Module {module_name} not found in registry")
                return False
        
        return True
    
    def fix_missing_attribute(self, error, module_name):
        """Fix missing attribute error"""
        self.logger.info(f"Attempting to fix missing attribute in: {module_name}")
        
        message = error.get("message", "")
        
        # Extract the missing attribute name
        attr_match = re.search(r"has no attribute '([^']+)'", message)
        if not attr_match:
            return False
        
        missing_attr = attr_match.group(1)
        module_path = self.brain_scripts_dir / f"{module_name}.py"
        
        if not module_path.exists():
            return False
        
        try:
            with open(module_path, 'r') as f:
                content = f.read()
            
            # Add the missing attribute/method
            if missing_attr == "main" and "def main(" not in content:
                main_function = '''

def main(task_info=None):
    """Main entry point for the module"""
    print(f"Executing {module_name}")
    return {"success": True, "message": "Module executed successfully"}
'''
                content += main_function
                
                with open(module_path, 'w') as f:
                    f.write(content)
                
                self.logger.info(f"Added missing main function to {module_name}")
                return True
            
            elif missing_attr and f"def {missing_attr}" not in content:
                # Add a basic method template
                method_template = f'''
    
    def {missing_attr}(self, *args, **kwargs):
        """Auto-generated method: {missing_attr}"""
        self.logger.info(f"Executing {{missing_attr}}")
        return True
'''
                # Try to add to class if one exists
                if "class " in content:
                    # Insert before the last line or before main function
                    lines = content.split('\n')
                    insert_index = len(lines)
                    
                    for i, line in enumerate(lines):
                        if line.strip().startswith("def main(") or line.strip() == 'if __name__ == "__main__":':
                            insert_index = i
                            break
                    
                    lines.insert(insert_index, method_template)
                    content = '\n'.join(lines)
                else:
                    content += method_template
                
                with open(module_path, 'w') as f:
                    f.write(content)
                
                self.logger.info(f"Added missing method {missing_attr} to {module_name}")
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to fix missing attribute in {module_name}: {e}")
            return False
        
        return False
    
    def fix_undefined_variable(self, error, module_name):
        """Fix undefined variable error"""
        self.logger.info(f"Attempting to fix undefined variable in: {module_name}")
        
        message = error.get("message", "")
        var_match = re.search(r"name '([^']+)' is not defined", message)
        
        if not var_match:
            return False
        
        undefined_var = var_match.group(1)
        module_path = self.brain_scripts_dir / f"{module_name}.py"
        
        if not module_path.exists():
            return False
        
        try:
            with open(module_path, 'r') as f:
                content = f.read()
            
            # Add common imports if they're missing
            common_imports = {
                "logging": "import logging",
                "datetime": "from datetime import datetime",
                "Path": "from pathlib import Path",
                "json": "import json",
                "os": "import os",
                "sys": "import sys"
            }
            
            if undefined_var in common_imports:
                import_line = common_imports[undefined_var]
                if import_line not in content:
                    # Add import at the top after docstring
                    lines = content.split('\n')
                    insert_index = 0
                    
                    # Find where to insert (after docstring)
                    in_docstring = False
                    for i, line in enumerate(lines):
                        if '"""' in line or "'''" in line:
                            in_docstring = not in_docstring
                        elif not in_docstring and line.strip() and not line.startswith('#'):
                            insert_index = i
                            break
                    
                    lines.insert(insert_index, import_line)
                    content = '\n'.join(lines)
                    
                    with open(module_path, 'w') as f:
                        f.write(content)
                    
                    self.logger.info(f"Added missing import for {undefined_var} in {module_name}")
                    return True
            
        except Exception as e:
            self.logger.error(f"Failed to fix undefined variable in {module_name}: {e}")
            return False
        
        return False
    
    def fix_import_error(self, error, module_name):
        """Fix import error"""
        return self.fix_missing_module(error, module_name)
    
    def fix_syntax_error(self, error, module_name):
        """Fix syntax error (basic fixes only)"""
        self.logger.info(f"Attempting to fix syntax error in: {module_name}")
        
        module_path = self.brain_scripts_dir / f"{module_name}.py"
        if not module_path.exists():
            return False
        
        try:
            with open(module_path, 'r') as f:
                content = f.read()
            
            # Common syntax fixes
            fixes_applied = False
            
            # Fix missing colons
            if re.search(r'(if|elif|else|for|while|def|class)\s+[^:]+$', content, re.MULTILINE):
                content = re.sub(r'(if|elif|else|for|while|def|class)(\s+[^:\n]+)$', r'\1\2:', content, flags=re.MULTILINE)
                fixes_applied = True
            
            # Fix missing quotes
            content = re.sub(r'(\w+)\s*=\s*([^"\'\n,]+)(\s*[,\n])', r'\1 = "\2"\3', content)
            
            if fixes_applied:
                with open(module_path, 'w') as f:
                    f.write(content)
                
                self.logger.info(f"Applied basic syntax fixes to {module_name}")
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to fix syntax error in {module_name}: {e}")
        
        return False
    
    def fix_indentation_error(self, error, module_name):
        """Fix indentation error"""
        self.logger.info(f"Attempting to fix indentation in: {module_name}")
        
        module_path = self.brain_scripts_dir / f"{module_name}.py"
        if not module_path.exists():
            return False
        
        try:
            with open(module_path, 'r') as f:
                lines = f.readlines()
            
            # Basic indentation fix - ensure consistent 4-space indentation
            fixed_lines = []
            for line in lines:
                if line.strip():  # Only process non-empty lines
                    # Count leading spaces
                    leading_spaces = len(line) - len(line.lstrip())
                    # Convert to 4-space indentation
                    indent_level = leading_spaces // 4
                    fixed_line = '    ' * indent_level + line.lstrip()
                    fixed_lines.append(fixed_line)
                else:
                    fixed_lines.append(line)
            
            with open(module_path, 'w') as f:
                f.writelines(fixed_lines)
            
            self.logger.info(f"Fixed indentation in {module_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to fix indentation in {module_name}: {e}")
        
        return False
    
    def fix_type_error(self, error, module_name):
        """Fix type error"""
        self.logger.info(f"Attempting to fix type error in: {module_name}")
        # For now, just log the error for manual review
        self.logger.warning(f"Type error in {module_name} requires manual review: {error.get('message', '')}")
        return False
    
    def fix_missing_file(self, error, module_name):
        """Fix missing file error"""
        return self.fix_missing_module(error, module_name)
    
    def generate_basic_module_template(self, module_name, module_info):
        """Generate a basic working module template"""
        description = module_info.get("description", f"Auto-generated {module_name} module")
        module_type = module_info.get("type", "utility")
        
        template = f'''#!/usr/bin/env python3
"""
{module_name.replace('_', ' ').title()} - {description}
Auto-generated by AutoFixerV1 on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
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
        """Main execution logic"""
        self.logger.info("Executing {module_name}")
        
        try:
            # Basic functionality for {module_type} type module
            result = self.perform_task()
            self.logger.info("Task completed successfully")
            return {{"success": True, "result": result}}
            
        except Exception as e:
            self.logger.error(f"Task execution failed: {{e}}")
            return {{"success": False, "error": str(e)}}
    
    def perform_task(self):
        """Perform the main task of this module"""
        # TODO: Implement specific functionality
        return f"{module_name} executed successfully"

def main(task_info=None):
    """Main entry point for the module"""
    module = {module_name.replace('_', '').title()}()
    return module.execute()

if __name__ == "__main__":
    result = main()
    print(f"Result: {{result}}")
'''
        return template
    
    def attempt_fix(self, error):
        """Attempt to fix a specific error"""
        error_type = error.get("type", "Unknown")
        module_name = self.extract_module_from_error(error)
        
        if not module_name:
            self.logger.warning(f"Could not extract module name from error: {error.get('message', '')}")
            return False
        
        self.logger.info(f"Attempting to fix {error_type} in module: {module_name}")
        
        # Get the appropriate fix function
        fix_function = self.error_fixes.get(error_type)
        
        if fix_function:
            try:
                result = fix_function(error, module_name)
                
                if result:
                    self.fix_history.append({
                        "error_type": error_type,
                        "module": module_name,
                        "message": error.get("message", ""),
                        "timestamp": datetime.now().isoformat(),
                        "success": True
                    })
                    self.logger.info(f"Successfully fixed {error_type} in {module_name}")
                else:
                    self.logger.warning(f"Failed to fix {error_type} in {module_name}")
                
                return result
                
            except Exception as e:
                self.logger.error(f"Error while attempting fix: {e}")
                return False
        else:
            self.logger.warning(f"No fix available for error type: {error_type}")
            return False
    
    def run_fixing_cycle(self):
        """Run a complete error fixing cycle"""
        self.logger.info("Starting error fixing cycle")
        
        # Monitor log files for errors
        errors = self.monitor_log_files()
        
        if not errors:
            self.logger.info("No errors found in logs")
            return True
        
        self.logger.info(f"Found {len(errors)} errors to process")
        
        # Attempt to fix each error
        fixes_attempted = 0
        fixes_successful = 0
        
        for error in errors:
            fixes_attempted += 1
            if self.attempt_fix(error):
                fixes_successful += 1
        
        self.logger.info(f"Fixed {fixes_successful}/{fixes_attempted} errors")
        return fixes_successful > 0

def main(task_info=None):
    """Main entry point for auto fixer"""
    fixer = AutoFixerV1()
    return fixer.run_fixing_cycle()

if __name__ == "__main__":
    result = main()
    print(f"Fix result: {result}")
