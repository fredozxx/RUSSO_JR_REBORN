#!/usr/bin/env python3
"""
Discord Listener - Listens for Discord commands and routes them to task_router
Handles Discord bot commands like /teach, /flush, /goal, /mode
"""

import os
import sys
import json
import logging
import asyncio
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import our modules
try:
    from deploy.task_router import TaskRouter
    from deploy.task_executor import TaskExecutor
except ImportError as e:
    print(f"Warning: Could not import modules: {e}")
    print("Make sure task_router.py and task_executor.py are in the deploy/ folder")

class DiscordListener:
    def __init__(self):
        self.project_root = project_root
        self.logs_dir = self.project_root / "logs"
        
        # Initialize components
        self.task_router = None
        self.task_executor = None
        self.setup_components()
        
        # Setup logging
        self.setup_logging()
        
        # Command handlers
        self.command_handlers = {
            "teach": self.handle_teach_command,
            "flush": self.handle_flush_command,
            "goal": self.handle_goal_command,
            "mode": self.handle_mode_command,
            "status": self.handle_status_command,
            "analyze": self.handle_analyze_command,
            "execute": self.handle_execute_command,
            "help": self.handle_help_command,
            "queue": self.handle_queue_command
        }
        
        # Bot state
        self.is_running = False
        self.current_mode = "learning"
        self.active_goal = None
        
    def setup_components(self):
        """Initialize task router and executor"""
        try:
            self.task_router = TaskRouter()
            self.task_executor = TaskExecutor()
            self.logger.info("Components initialized successfully") if hasattr(self, 'logger') else None
        except Exception as e:
            print(f"Failed to initialize components: {e}")
    
    def setup_logging(self):
        """Initialize logging system"""
        self.logs_dir.mkdir(exist_ok=True)
        log_file = self.logs_dir / f"discord_listener_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    async def handle_teach_command(self, args, user_id=None):
        """Handle /teach command - teaches new concepts to the bot"""
        if not args:
            return "❌ Please provide something to teach me. Usage: `/teach <concept or information>`"
        
        concept = " ".join(args)
        self.logger.info(f"Teach command from user {user_id}: {concept}")
        
        # Route to learning module
        task_id = self.task_router.route_discord_command("teach", args, user_id)
        
        if task_id:
            return f"🧠 Learning new concept: '{concept}'\n📝 Task ID: {task_id}\n⏳ Processing..."
        else:
            return "❌ Failed to process teaching request. Please try again."
    
    async def handle_flush_command(self, args, user_id=None):
        """Handle /flush command - clears memory/cache"""
        flush_type = args[0] if args else "memory"
        
        valid_types = ["memory", "cache", "logs", "temp", "all"]
        if flush_type not in valid_types:
            return f"❌ Invalid flush type. Valid options: {', '.join(valid_types)}"
        
        self.logger.info(f"Flush command from user {user_id}: {flush_type}")
        
        # Route to memory flush module
        task_id = self.task_router.route_discord_command("flush", [flush_type], user_id)
        
        if task_id:
            return f"🧹 Flushing {flush_type}...\n📝 Task ID: {task_id}\n⏳ Processing..."
        else:
            return "❌ Failed to process flush request. Please try again."
    
    async def handle_goal_command(self, args, user_id=None):
        """Handle /goal command - sets AI goals"""
        if not args:
            current_goal = self.active_goal or "No active goal"
            return f"🎯 Current goal: {current_goal}\n💡 Usage: `/goal <learn|optimize|maintain|evolve> [context]`"
        
        goal_type = args[0].lower()
        context = " ".join(args[1:]) if len(args) > 1 else None
        
        valid_goals = ["learn", "optimize", "maintain", "evolve"]
        if goal_type not in valid_goals:
            return f"❌ Invalid goal type. Valid options: {', '.join(valid_goals)}"
        
        self.logger.info(f"Goal command from user {user_id}: {goal_type} - {context}")
        
        # Update active goal
        self.active_goal = f"{goal_type}: {context}" if context else goal_type
        
        # Route goal-based tasks
        self.task_router.route_by_goal(goal_type, context)
        
        # Also route the goal setter command
        task_id = self.task_router.route_discord_command("goal", args, user_id)
        
        return f"🎯 Goal set: {goal_type}\n📝 Context: {context or 'None'}\n🚀 Routing related tasks..."
    
    async def handle_mode_command(self, args, user_id=None):
        """Handle /mode command - switches operational modes"""
        if not args:
            return f"⚙️ Current mode: {self.current_mode}\n💡 Usage: `/mode <active|passive|learning|maintenance|evolution>`"
        
        new_mode = args[0].lower()
        valid_modes = ["active", "passive", "learning", "maintenance", "evolution"]
        
        if new_mode not in valid_modes:
            return f"❌ Invalid mode. Valid options: {', '.join(valid_modes)}"
        
        self.logger.info(f"Mode command from user {user_id}: {new_mode}")
        
        old_mode = self.current_mode
        self.current_mode = new_mode
        
        # Route to mode switcher
        task_id = self.task_router.route_discord_command("mode", args, user_id)
        
        return f"⚙️ Mode changed: {old_mode} → {new_mode}\n📝 Task ID: {task_id}\n✅ Mode switch initiated"
    
    async def handle_status_command(self, args, user_id=None):
        """Handle /status command - shows system status"""
        self.logger.info(f"Status command from user {user_id}")
        
        # Get queue status
        queue_status = self.task_router.get_queue_status()
        
        # Get execution stats
        exec_stats = self.task_executor.get_execution_stats()
        
        # Route to status report module
        task_id = self.task_router.route_discord_command("status", args, user_id)
        
        status_message = f"""📊 **Russo Jr Status Report**
        
🤖 **Bot Status**: {'🟢 Running' if self.is_running else '🔴 Stopped'}
⚙️ **Current Mode**: {self.current_mode}
🎯 **Active Goal**: {self.active_goal or 'None'}

📋 **Task Queue**: {queue_status['total_tasks']} tasks
🎯 **Recent Executions**: {exec_stats.get('total_executions', 0)}
✅ **Success Rate**: {exec_stats.get('success_rate', 0):.1f}%

📝 **Detailed Report**: Task ID {task_id}
"""
        
        return status_message
    
    async def handle_analyze_command(self, args, user_id=None):
        """Handle /analyze command - analyzes data or system"""
        analysis_type = args[0] if args else "general"
        target = " ".join(args[1:]) if len(args) > 1 else None
        
        self.logger.info(f"Analyze command from user {user_id}: {analysis_type} - {target}")
        
        # Route to data analyzer
        task_id = self.task_router.route_discord_command("analyze", args, user_id)
        
        return f"📊 Starting analysis: {analysis_type}\n🎯 Target: {target or 'System-wide'}\n📝 Task ID: {task_id}"
    
    async def handle_execute_command(self, args, user_id=None):
        """Handle /execute command - manually execute specific tasks"""
        if not args:
            return "❌ Please specify a task to execute. Usage: `/execute <task_name>`"
        
        task_name = args[0]
        
        self.logger.info(f"Execute command from user {user_id}: {task_name}")
        
        # Add task directly to router
        task_id = self.task_router.add_task(
            task_name=task_name,
            trigger_source="discord_manual",
            metadata={"user_id": user_id, "manual_execution": True}
        )
        
        # Try to dispatch immediately
        dispatched = self.task_router.route_and_dispatch(1)
        
        if dispatched:
            return f"🚀 Executing task: {task_name}\n📝 Task ID: {task_id}\n⏳ Running now..."
        else:
            return f"📋 Task queued: {task_name}\n📝 Task ID: {task_id}\n⏳ Will execute when resources available"
    
    async def handle_queue_command(self, args, user_id=None):
        """Handle /queue command - shows task queue status"""
        queue_status = self.task_router.get_queue_status()
        
        if queue_status['total_tasks'] == 0:
            return "📋 Task queue is empty"
        
        message = f"📋 **Task Queue Status**\n\n"
        message += f"📊 **Total Tasks**: {queue_status['total_tasks']}\n\n"
        
        if queue_status['by_priority']:
            message += "🎯 **By Priority**:\n"
            for priority, count in queue_status['by_priority'].items():
                message += f"   Priority {priority}: {count} tasks\n"
            message += "\n"
        
        if queue_status['by_type']:
            message += "📂 **By Type**:\n"
            for task_type, count in queue_status['by_type'].items():
                message += f"   {task_type}: {count} tasks\n"
        
        return message
    
    async def handle_help_command(self, args, user_id=None):
        """Handle /help command - shows available commands"""
        help_message = """🤖 **Russo Jr Commands**

📚 **Learning & AI:**
  `/teach <concept>` - Teach me new information
  `/goal <type> [context]` - Set AI goals (learn/optimize/maintain/evolve)
  `/analyze [type] [target]` - Analyze data or system

⚙️ **System Control:**
  `/mode <mode>` - Change operational mode
  `/flush <type>` - Clear memory/cache/logs
  `/execute <task>` - Manually run a specific task

📊 **Status & Info:**
  `/status` - Show system status
  `/queue` - Show task queue
  `/help` - Show this help message

🎯 **Goal Types:** learn, optimize, maintain, evolve
⚙️ **Modes:** active, passive, learning, maintenance, evolution
🧹 **Flush Types:** memory, cache, logs, temp, all
"""
        return help_message
    
    async def process_discord_message(self, content, user_id=None, channel_id=None):
        """Process a Discord message and route commands"""
        content = content.strip()
        
        # Check if it's a command (starts with /)
        if not content.startswith('/'):
            return None
        
        # Parse command and arguments
        parts = content[1:].split()
        if not parts:
            return None
        
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        # Log the command
        self.logger.info(f"Processing command: {command} from user: {user_id}")
        
        # Handle the command
        if command in self.command_handlers:
            try:
                response = await self.command_handlers[command](args, user_id)
                return response
            except Exception as e:
                self.logger.error(f"Error handling command {command}: {e}")
                return f"❌ Error processing command: {str(e)}"
        else:
            return f"❌ Unknown command: {command}\nUse `/help` to see available commands."
    
    def start_listening(self):
        """Start the Discord listener (placeholder for actual Discord bot integration)"""
        self.is_running = True
        self.logger.info("Discord listener started")
        
        # This is where you would initialize the actual Discord bot
        # For now, this is just a framework that can be integrated with discord.py
        
        print("🤖 Russo Jr Discord Listener is ready!")
        print("📝 Integrate this with discord.py to handle actual Discord messages")
        print("💡 Use process_discord_message() method to handle incoming messages")
    
    def stop_listening(self):
        """Stop the Discord listener"""
        self.is_running = False
        self.logger.info("Discord listener stopped")

# Example integration function for discord.py
async def integrate_with_discord_bot():
    """
    Example of how to integrate this with an actual Discord bot using discord.py
    
    This is just a template - you'll need to install discord.py and set up a bot token
    """
    
    # Uncomment and modify this code when you're ready to integrate with Discord:
    
    # import discord
    # from discord.ext import commands
    # 
    # # Initialize the Discord listener
    # listener = DiscordListener()
    # listener.start_listening()
    # 
    # # Create Discord bot
    # intents = discord.Intents.default()
    # intents.message_content = True
    # bot = commands.Bot(command_prefix='/', intents=intents)
    # 
    # @bot.event
    # async def on_ready():
    #     print(f'{bot.user} has connected to Discord!')
    # 
    # @bot.event
    # async def on_message(message):
    #     if message.author == bot.user:
    #         return
    #     
    #     # Process the message through our listener
    #     response = await listener.process_discord_message(
    #         message.content, 
    #         str(message.author.id), 
    #         str(message.channel.id)
    #     )
    #     
    #     if response:
    #         await message.channel.send(response)
    # 
    # # Run the bot
    # await bot.start('YOUR_BOT_TOKEN_HERE')
    
    pass

if __name__ == "__main__":
    listener = DiscordListener()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "test":
            # Test the command processing
            async def test_commands():
                test_messages = [
                    "/help",
                    "/status", 
                    "/teach This is a test concept",
                    "/goal learn data analysis",
                    "/mode learning",
                    "/queue"
                ]
                
                for msg in test_messages:
                    print(f"\n{'='*50}")
                    print(f"Testing: {msg}")
                    print(f"{'='*50}")
                    response = await listener.process_discord_message(msg, "test_user")
                    print(response)
            
            # Run the test
            asyncio.run(test_commands())
        
        elif command == "start":
            listener.start_listening()
            print("Discord listener is running. Press Ctrl+C to stop.")
            try:
                while True:
                    pass
            except KeyboardInterrupt:
                listener.stop_listening()
                print("\nDiscord listener stopped.")
    else:
        print("Usage:")
        print("  python discord_listener.py test   - Test command processing")
        print("  python discord_listener.py start  - Start the listener")
        print("\nTo integrate with actual Discord bot, see the integrate_with_discord_bot() function")
