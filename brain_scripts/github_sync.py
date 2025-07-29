#!/usr/bin/env python3
"""
GitHub Sync - Automatically pushes committed upgrades to GitHub
Includes error logging, branch status checking, and force push override
"""

import os
import sys
import json
import logging
import subprocess
import time
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

class GitHubSync:
    def __init__(self):
        self.project_root = project_root
        self.logs_dir = self.project_root / "logs"
        self.configs_dir = self.project_root / "logs" / "configs"
        
        # Sync settings
        self.sync_interval = 3600  # 1 hour default
        self.auto_sync_enabled = True
        self.force_push_enabled = False
        self.max_retry_attempts = 3
        
        # Git settings
        self.default_branch = "master"
        self.remote_name = "origin"
        
        # Sync history
        self.sync_history = []
        self.last_sync_time = None
        self.last_sync_successful = False
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Initialize logging system"""
        self.logs_dir.mkdir(exist_ok=True)
        log_file = self.logs_dir / f"github_sync_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_sync_config(self):
        """Load sync configuration"""
        sync_config_path = self.configs_dir / "github_sync_config.json"
        
        if sync_config_path.exists():
            try:
                with open(sync_config_path, 'r') as f:
                    config = json.load(f)
                
                self.sync_interval = config.get("sync_interval", 3600)
                self.auto_sync_enabled = config.get("auto_sync_enabled", True)
                self.force_push_enabled = config.get("force_push_enabled", False)
                self.max_retry_attempts = config.get("max_retry_attempts", 3)
                self.default_branch = config.get("default_branch", "master")
                self.remote_name = config.get("remote_name", "origin")
                
                self.logger.info("Loaded GitHub sync configuration")
                return config
                
            except Exception as e:
                self.logger.error(f"Failed to load sync config: {e}")
                return self.create_default_sync_config()
        else:
            return self.create_default_sync_config()
    
    def create_default_sync_config(self):
        """Create default sync configuration"""
        default_config = {
            "sync_interval": self.sync_interval,
            "auto_sync_enabled": self.auto_sync_enabled,
            "force_push_enabled": self.force_push_enabled,
            "max_retry_attempts": self.max_retry_attempts,
            "default_branch": self.default_branch,
            "remote_name": self.remote_name,
            "created": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
        
        self.save_sync_config(default_config)
        return default_config
    
    def save_sync_config(self, config):
        """Save sync configuration"""
        sync_config_path = self.configs_dir / "github_sync_config.json"
        
        try:
            self.configs_dir.mkdir(parents=True, exist_ok=True)
            with open(sync_config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.logger.info("Sync configuration saved")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save sync config: {e}")
            return False
    
    def run_git_command(self, command, timeout=30):
        """Run a git command and return the result"""
        try:
            self.logger.debug(f"Running git command: {' '.join(command)}")
            
            result = subprocess.run(
                command,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "returncode": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"Git command timed out: {' '.join(command)}")
            return {
                "success": False,
                "stdout": "",
                "stderr": "Command timed out",
                "returncode": -1
            }
        except Exception as e:
            self.logger.error(f"Failed to run git command: {e}")
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }
    
    def check_git_status(self):
        """Check current git repository status"""
        status_result = self.run_git_command(["git", "status", "--porcelain"])
        
        if not status_result["success"]:
            self.logger.error(f"Failed to check git status: {status_result['stderr']}")
            return None
        
        # Parse status output
        status_lines = status_result["stdout"].split('\n') if status_result["stdout"] else []
        
        status_info = {
            "has_changes": len(status_lines) > 0 and status_lines[0],
            "staged_files": [],
            "unstaged_files": [],
            "untracked_files": []
        }
        
        for line in status_lines:
            if len(line) >= 3:
                staged_status = line[0]
                unstaged_status = line[1]
                filename = line[3:]
                
                if staged_status != ' ':
                    status_info["staged_files"].append(filename)
                if unstaged_status != ' ':
                    status_info["unstaged_files"].append(filename)
                if staged_status == '?' and unstaged_status == '?':
                    status_info["untracked_files"].append(filename)
        
        return status_info
    
    def check_branch_status(self):
        """Check current branch and remote status"""
        # Get current branch
        branch_result = self.run_git_command(["git", "branch", "--show-current"])
        
        if not branch_result["success"]:
            self.logger.error(f"Failed to get current branch: {branch_result['stderr']}")
            return None
        
        current_branch = branch_result["stdout"]
        
        # Check if remote branch exists
        remote_branch_result = self.run_git_command([
            "git", "ls-remote", "--heads", self.remote_name, current_branch
        ])
        
        remote_exists = remote_branch_result["success"] and remote_branch_result["stdout"]
        
        # Check for ahead/behind status
        ahead_behind = {"ahead": 0, "behind": 0}
        
        if remote_exists:
            status_result = self.run_git_command([
                "git", "rev-list", "--left-right", "--count", 
                f"{self.remote_name}/{current_branch}...HEAD"
            ])
            
            if status_result["success"] and status_result["stdout"]:
                try:
                    behind, ahead = map(int, status_result["stdout"].split())
                    ahead_behind = {"ahead": ahead, "behind": behind}
                except ValueError:
                    pass
        
        return {
            "current_branch": current_branch,
            "remote_exists": remote_exists,
            "ahead": ahead_behind["ahead"],
            "behind": ahead_behind["behind"]
        }
    
    def check_remote_connectivity(self):
        """Check if remote repository is accessible"""
        remote_result = self.run_git_command(["git", "remote", "-v"])
        
        if not remote_result["success"]:
            self.logger.error("Failed to check git remotes")
            return False
        
        if self.remote_name not in remote_result["stdout"]:
            self.logger.error(f"Remote '{self.remote_name}' not found")
            return False
        
        # Test connectivity with fetch --dry-run
        fetch_result = self.run_git_command([
            "git", "fetch", "--dry-run", self.remote_name
        ], timeout=10)
        
        if fetch_result["success"] or "up to date" in fetch_result["stderr"].lower():
            return True
        else:
            self.logger.warning(f"Remote connectivity check failed: {fetch_result['stderr']}")
            return False
    
    def add_all_changes(self):
        """Add all changes to staging area"""
        add_result = self.run_git_command(["git", "add", "."])
        
        if add_result["success"]:
            self.logger.info("Added all changes to staging area")
            return True
        else:
            self.logger.error(f"Failed to add changes: {add_result['stderr']}")
            return False
    
    def commit_changes(self, message=None):
        """Commit staged changes"""
        if not message:
            message = f"Auto-sync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        commit_result = self.run_git_command(["git", "commit", "-m", message])
        
        if commit_result["success"]:
            self.logger.info(f"Committed changes with message: {message}")
            return True
        elif "nothing to commit" in commit_result["stdout"]:
            self.logger.info("No changes to commit")
            return True
        else:
            self.logger.error(f"Failed to commit changes: {commit_result['stderr']}")
            return False
    
    def push_to_remote(self, force=False):
        """Push changes to remote repository"""
        branch_status = self.check_branch_status()
        
        if not branch_status:
            return False
        
        current_branch = branch_status["current_branch"]
        
        # Prepare push command
        push_command = ["git", "push", self.remote_name, current_branch]
        
        # Add force flag if needed and enabled
        if force and self.force_push_enabled:
            push_command.append("--force")
            self.logger.warning("Force pushing changes")
        
        # Set upstream if remote branch doesn't exist
        if not branch_status["remote_exists"]:
            push_command.extend(["-u", self.remote_name, current_branch])
            self.logger.info(f"Setting upstream for branch: {current_branch}")
        
        push_result = self.run_git_command(push_command, timeout=60)
        
        if push_result["success"]:
            self.logger.info(f"Successfully pushed to {self.remote_name}/{current_branch}")
            return True
        else:
            self.logger.error(f"Failed to push: {push_result['stderr']}")
            
            # Check if force push might be needed
            if "rejected" in push_result["stderr"] and not force:
                self.logger.warning("Push rejected - may need force push")
                
                if self.force_push_enabled:
                    self.logger.info("Attempting force push...")
                    return self.push_to_remote(force=True)
            
            return False
    
    def sync_to_github(self, auto_commit=True):
        """Perform complete sync to GitHub"""
        sync_start_time = datetime.now()
        sync_record = {
            "start_time": sync_start_time.isoformat(),
            "success": False,
            "error": None,
            "changes_synced": False,
            "commit_created": False,
            "push_successful": False
        }
        
        try:
            self.logger.info("Starting GitHub sync")
            
            # Check remote connectivity
            if not self.check_remote_connectivity():
                raise Exception("Remote repository not accessible")
            
            # Check git status
            status = self.check_git_status()
            
            if not status:
                raise Exception("Failed to check git status")
            
            if not status["has_changes"]:
                self.logger.info("No changes to sync")
                sync_record["success"] = True
                return sync_record
            
            self.logger.info(f"Found changes: {len(status['staged_files'])} staged, {len(status['unstaged_files'])} unstaged")
            
            # Add changes if auto_commit is enabled
            if auto_commit:
                if status["unstaged_files"] or status["untracked_files"]:
                    if not self.add_all_changes():
                        raise Exception("Failed to add changes")
                
                # Commit changes
                if not self.commit_changes():
                    raise Exception("Failed to commit changes")
                
                sync_record["commit_created"] = True
            
            # Push to remote
            if not self.push_to_remote():
                raise Exception("Failed to push to remote")
            
            sync_record["push_successful"] = True
            sync_record["changes_synced"] = True
            sync_record["success"] = True
            
            self.last_sync_successful = True
            self.logger.info("GitHub sync completed successfully")
            
        except Exception as e:
            error_msg = str(e)
            sync_record["error"] = error_msg
            self.logger.error(f"GitHub sync failed: {error_msg}")
            self.last_sync_successful = False
        
        finally:
            # Record sync attempt
            sync_record["end_time"] = datetime.now().isoformat()
            sync_record["duration"] = (datetime.now() - sync_start_time).total_seconds()
            
            self.sync_history.append(sync_record)
            self.last_sync_time = sync_start_time
            
            # Keep only last 50 sync records
            if len(self.sync_history) > 50:
                self.sync_history = self.sync_history[-50:]
        
        return sync_record
    
    def should_sync(self):
        """Check if it's time to sync"""
        if not self.auto_sync_enabled:
            return False
        
        if self.last_sync_time is None:
            return True
        
        time_since_last = datetime.now() - self.last_sync_time
        return time_since_last.total_seconds() >= self.sync_interval
    
    def run_sync_cycle(self):
        """Run automatic sync cycle"""
        self.logger.info("Starting sync cycle")
        
        # Load configuration
        self.load_sync_config()
        
        # Check if sync is needed
        if not self.should_sync():
            time_until_next = self.sync_interval - (datetime.now() - self.last_sync_time).total_seconds()
            self.logger.info(f"Sync not needed. Next sync in {time_until_next:.0f} seconds")
            return {"success": True, "synced": False, "next_sync_in": time_until_next}
        
        # Perform sync with retry logic
        sync_result = None
        
        for attempt in range(self.max_retry_attempts):
            try:
                self.logger.info(f"Sync attempt {attempt + 1}/{self.max_retry_attempts}")
                sync_result = self.sync_to_github()
                
                if sync_result["success"]:
                    break
                else:
                    if attempt < self.max_retry_attempts - 1:
                        wait_time = (attempt + 1) * 30  # Progressive backoff
                        self.logger.info(f"Sync failed, retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    
            except Exception as e:
                self.logger.error(f"Sync attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retry_attempts - 1:
                    wait_time = (attempt + 1) * 30
                    time.sleep(wait_time)
        
        if sync_result and sync_result["success"]:
            self.logger.info("Sync cycle completed successfully")
        else:
            self.logger.error("Sync cycle failed after all retry attempts")
        
        return sync_result or {"success": False, "error": "All sync attempts failed"}
    
    def get_sync_status(self):
        """Get current sync status and statistics"""
        recent_syncs = self.sync_history[-10:] if self.sync_history else []
        successful_syncs = sum(1 for sync in recent_syncs if sync["success"])
        
        return {
            "auto_sync_enabled": self.auto_sync_enabled,
            "sync_interval": self.sync_interval,
            "last_sync_time": self.last_sync_time.isoformat() if self.last_sync_time else None,
            "last_sync_successful": self.last_sync_successful,
            "total_syncs": len(self.sync_history),
            "recent_success_rate": (successful_syncs / len(recent_syncs)) * 100 if recent_syncs else 0,
            "next_sync_due": self.should_sync(),
            "git_status": self.check_git_status(),
            "branch_status": self.check_branch_status()
        }
    
    def manual_sync(self):
        """Perform manual sync (ignores schedule)"""
        self.logger.info("Performing manual sync")
        return self.sync_to_github()

def main(task_info=None):
    """Main entry point for GitHub sync"""
    syncer = GitHubSync()
    
    # Check if this is a manual sync request
    if task_info and task_info.get("metadata", {}).get("manual_sync"):
        return syncer.manual_sync()
    else:
        return syncer.run_sync_cycle()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        syncer = GitHubSync()
        
        if command == "status":
            status = syncer.get_sync_status()
            print(json.dumps(status, indent=2))
        elif command == "sync":
            result = syncer.manual_sync()
            print(f"Sync result: {result}")
        elif command == "config":
            config = syncer.load_sync_config()
            print(json.dumps(config, indent=2))
        else:
            print("Usage:")
            print("  python github_sync.py status  - Show sync status")
            print("  python github_sync.py sync    - Manual sync")
            print("  python github_sync.py config  - Show configuration")
    else:
        result = main()
        print(f"GitHub sync result: {result}")
