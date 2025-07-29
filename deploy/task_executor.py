#!/usr/bin/env python3
"""
Task Executor - Safe execution of modules with timeouts and logging
Safely executes modules passed by task_router with proper error handling
"""

import os
import sys
import json
import time
import logging
import traceback
import subprocess
import importlib.util
from pathlib import Path
from datetime import datetime
from threading import Thread, Event
from contextlib import contextmanager

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

class ExecutionResult:
    def __init__(self, success=False, output="", error="", duration=0, task_id=None):
        self.success = success
        self.output = output
        self.error = error
        self.duration = duration
        self.task_id = task_id
        self.timestamp = datetime.now().isoformat()

class TaskExecutor:
    def __init__(self):
        self.project_root = project_root
        self.brain_scripts_dir = self.project_root / "brain_scripts"
        self.logs_dir = self.project_root / "logs"
        
        # Execution settings
        self.default_timeout = 300  # 5 minutes
        self.max_timeout = 1800     # 30 minutes
        self.execution_history = []
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Initialize logging system"""
        self.logs_dir.mkdir(exist_ok=True)
        log_file = self.logs_dir / f"task_executor_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    @contextmanager
    def execution_timeout(self, timeout_seconds):
        """Context manager for execution timeout"""
        timeout_event = Event()
        
        def timeout_handler():
            time.sleep(timeout_seconds)
            if not timeout_event.is_set():
                self.logger.warning(f"Execution timeout after {timeout_seconds} seconds")
                timeout_event.set()
        
        timeout_thread = Thread(target=timeout_handler, daemon=True)
        timeout_thread.start()
        
        try:
            yield timeout_event
        finally:
            timeout_event.set()
    
    def execute_python_module(self, script_path, task_info=None, timeout=None):
        """Execute a Python module safely"""
        timeout = timeout or self.default_timeout
        start_time = time.time()
        
        self.logger.info(f"Executing Python module: {script_path}")
        
        try:
            # Load the module dynamically
            module_name = Path(script_path).stem
            spec = importlib.util.spec_from_file_location(module_name, script_path)
            
            if spec is None:
                raise ImportError(f"Could not load spec for {script_path}")
            
            module = importlib.util.module_from_spec(spec)
            
            # Execute with timeout
            with self.execution_timeout(timeout) as timeout_event:
                if timeout_event.is_set():
                    raise TimeoutError(f"Module loading timed out after {timeout} seconds")
                
                # Load the module
                spec.loader.exec_module(module)
                
                if timeout_event.is_set():
                    raise TimeoutError(f"Module execution timed out after {timeout} seconds")
                
                # Execute main function if it exists
                if hasattr(module, 'main'):
                    if task_info:
                        # Try to pass task info if the function accepts it
                        try:
                            result = module.main(task_info)
                        except TypeError:
                            # Fallback to no arguments
                            result = module.main()
                    else:
                        result = module.main()
                    
                    output = str(result) if result is not None else "Module executed successfully"
                else:
                    output = "Module loaded successfully (no main function found)"
                
                duration = time.time() - start_time
                
                return ExecutionResult(
                    success=True,
                    output=output,
                    duration=duration,
                    task_id=task_info.get("id") if task_info else None
                )
                
        except TimeoutError as e:
            duration = time.time() - start_time
            error_msg = str(e)
            self.logger.error(f"Module execution timed out: {error_msg}")
            
            return ExecutionResult(
                success=False,
                error=error_msg,
                duration=duration,
                task_id=task_info.get("id") if task_info else None
            )
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"{type(e).__name__}: {str(e)}"
            error_trace = traceback.format_exc()
            
            self.logger.error(f"Module execution failed: {error_msg}")
            self.logger.debug(f"Full traceback: {error_trace}")
            
            return ExecutionResult(
                success=False,
                error=error_msg,
                duration=duration,
                task_id=task_info.get("id") if task_info else None
            )
    
    def execute_subprocess(self, command, task_info=None, timeout=None):
        """Execute a subprocess command safely"""
        timeout = timeout or self.default_timeout
        start_time = time.time()
        
        self.logger.info(f"Executing subprocess: {command}")
        
        try:
            # Execute the command with timeout
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.project_root
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                return ExecutionResult(
                    success=True,
                    output=result.stdout,
                    duration=duration,
                    task_id=task_info.get("id") if task_info else None
                )
            else:
                return ExecutionResult(
                    success=False,
                    output=result.stdout,
                    error=result.stderr,
                    duration=duration,
                    task_id=task_info.get("id") if task_info else None
                )
                
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            error_msg = f"Subprocess timed out after {timeout} seconds"
            self.logger.error(error_msg)
            
            return ExecutionResult(
                success=False,
                error=error_msg,
                duration=duration,
                task_id=task_info.get("id") if task_info else None
            )
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Subprocess execution failed: {str(e)}"
            self.logger.error(error_msg)
            
            return ExecutionResult(
                success=False,
                error=error_msg,
                duration=duration,
                task_id=task_info.get("id") if task_info else None
            )
    
    def execute_task(self, task_info):
        """Execute a task based on its configuration"""
        if not task_info:
            return ExecutionResult(success=False, error="No task information provided")
        
        task_name = task_info.get("name", "unknown")
        script_info = task_info.get("script_info", {})
        
        self.logger.info(f"Starting execution of task: {task_name}")
        
        # Determine execution method
        script_path = script_info.get("path")
        if not script_path:
            return ExecutionResult(
                success=False, 
                error="No script path provided",
                task_id=task_info.get("id")
            )
        
        if not os.path.exists(script_path):
            return ExecutionResult(
                success=False, 
                error=f"Script file not found: {script_path}",
                task_id=task_info.get("id")
            )
        
        # Get custom timeout from task metadata
        custom_timeout = None
        if "metadata" in task_info:
            custom_timeout = task_info["metadata"].get("timeout")
        
        timeout = min(custom_timeout or self.default_timeout, self.max_timeout)
        
        # Execute based on file type
        if script_path.endswith('.py'):
            result = self.execute_python_module(script_path, task_info, timeout)
        else:
            # Treat as executable command
            result = self.execute_subprocess(script_path, task_info, timeout)
        
        # Log execution result
        self.log_execution_result(task_info, result)
        
        # Add to execution history
        self.execution_history.append({
            "task": task_info,
            "result": result.__dict__,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 100 executions in memory
        if len(self.execution_history) > 100:
            self.execution_history = self.execution_history[-100:]
        
        return result
    
    def log_execution_result(self, task_info, result):
        """Log detailed execution results"""
        task_name = task_info.get("name", "unknown")
        
        if result.success:
            self.logger.info(f"Task '{task_name}' completed successfully in {result.duration:.2f}s")
            if result.output:
                self.logger.debug(f"Task output: {result.output[:500]}...")  # Limit output length
        else:
            self.logger.error(f"Task '{task_name}' failed after {result.duration:.2f}s")
            self.logger.error(f"Error: {result.error}")
        
        # Write detailed log to separate file
        task_log_file = self.logs_dir / f"task_{task_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        try:
            with open(task_log_file, 'w') as f:
                f.write(f"Task Execution Log\n")
                f.write(f"==================\n")
                f.write(f"Task: {task_name}\n")
                f.write(f"Task ID: {task_info.get('id', 'N/A')}\n")
                f.write(f"Timestamp: {result.timestamp}\n")
                f.write(f"Duration: {result.duration:.2f}s\n")
                f.write(f"Success: {result.success}\n")
                f.write(f"Task Info: {json.dumps(task_info, indent=2)}\n")
                f.write(f"\nOutput:\n{result.output}\n")
                if result.error:
                    f.write(f"\nError:\n{result.error}\n")
        except Exception as e:
            self.logger.error(f"Failed to write task log: {e}")
    
    def execute_batch(self, tasks):
        """Execute multiple tasks in sequence"""
        results = []
        
        self.logger.info(f"Starting batch execution of {len(tasks)} tasks")
        
        for i, task in enumerate(tasks):
            self.logger.info(f"Executing task {i+1}/{len(tasks)}: {task.get('name', 'unknown')}")
            result = self.execute_task(task)
            results.append(result)
            
            # Brief pause between tasks
            time.sleep(1)
        
        successful = sum(1 for r in results if r.success)
        self.logger.info(f"Batch execution completed: {successful}/{len(tasks)} tasks successful")
        
        return results
    
    def get_execution_stats(self):
        """Get execution statistics"""
        if not self.execution_history:
            return {"total_executions": 0}
        
        total = len(self.execution_history)
        successful = sum(1 for entry in self.execution_history if entry["result"]["success"])
        failed = total - successful
        
        durations = [entry["result"]["duration"] for entry in self.execution_history]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            "total_executions": total,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total) * 100 if total > 0 else 0,
            "average_duration": avg_duration
        }

if __name__ == "__main__":
    executor = TaskExecutor()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "test":
            # Test execution
            test_task = {
                "id": "test_001",
                "name": "test_module",
                "script_info": {
                    "path": str(executor.brain_scripts_dir / "test_module.py")
                }
            }
            
            result = executor.execute_task(test_task)
            print(f"Test execution result: {result.success}")
            print(f"Output: {result.output}")
            if result.error:
                print(f"Error: {result.error}")
        
        elif command == "stats":
            stats = executor.get_execution_stats()
            print("Execution Statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
