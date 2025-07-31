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
            "queue": self.handle_queue_command,
            "stocks": self.handle_stocks_command,
            "analyze_stocks": self.handle_analyze_stocks_command,
            "execute_stock_trades": self.handle_execute_stock_trades_command,
            "track_stocks": self.handle_track_stocks_command,
            "summary": self.handle_summary_command,
            "summary_ai": self.handle_summary_ai_command,
            "top_earners": self.handle_top_earners_command,
            "auto_on": self.handle_auto_on_command,
            "auto_off": self.handle_auto_off_command,
            "wallet": self.handle_wallet_command,
            "make_channel": self.handle_make_channel_command,
            "rename_channel": self.handle_rename_channel_command,
            "move_logs_channel": self.handle_move_logs_channel_command,
            "autofix": self.handle_autofix_command,
            # AI Self-Building Commands - CRITICAL FOR GITHUB SYNC
            "autoevolve": self.handle_autoevolve_command,
            "build_self": self.handle_build_self_command,
            # Bot Spawning Commands - CRITICAL FOR BOT MANAGEMENT
            "spawn_bot": self.handle_spawn_bot_command,
            "inject_keys": self.handle_inject_keys_command,
            "upgrade_bot": self.handle_upgrade_bot_command,
            "list_my_bots": self.handle_list_my_bots_command,
            "terminate_bot": self.handle_terminate_bot_command,
            "assign_bot": self.handle_assign_bot_command
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

💹 **Stock Trading:**
  `/stocks` - Collect latest stock market data
  `/analyze_stocks` - Run pattern detection and volatility screening
  `/execute_stock_trades` - Execute stock trading strategies
  `/track_stocks` - Track portfolio performance
  `/wallet [action]` - Check wallet balances and trading status

🧠 **AI Intelligence:**
  `/summary` - Generate trading summary from logs
  `/summary_ai` - Show top AI predictions by confidence
  `/top_earners` - Rank top 5 performing assets

⚙️ **Automation:**
  `/auto_on` - Enable autonomous trading mode
  `/auto_off` - Disable autonomous trading mode

🤖 **Bot Spawning:**
  `/spawn_bot name:<n> brain:<1-100>` - Create downloadable AI bot
  `/inject_keys botname:<n> api=<key>` - Add API keys to bot
  `/upgrade_bot botname:<n>` - Manual GitHub sync
  `/list_my_bots` - List your autonomous bots
  `/terminate_bot botname:<n>` - Delete bot permanently

🧠 **AI Evolution - CRITICAL:**
  `/autoevolve` - Trigger autonomous module generation & GitHub sync
  `/build_self [hint]` - Force AI to build missing capabilities

⚙️ **System Control:**
  `/mode <mode>` - Change operational mode
  `/flush <type>` - Clear memory/cache/logs
  `/execute <task>` - Manually run a specific task
  `/autofix` - Run automatic error fixing

📊 **Status & Info:**
  `/status` - Show system status
  `/queue` - Show task queue
  `/help` - Show this help message

🎯 **Goal Types:** learn, optimize, maintain, evolve
⚙️ **Modes:** active, passive, learning, maintenance, evolution
🧹 **Flush Types:** memory, cache, logs, temp, all
"""
        return help_message

    async def handle_autoevolve_command(self, args, user_id=None):
        """Handle /autoevolve command - triggers AI self-building cycle with GitHub sync"""
        try:
            self.logger.info(f"Auto-evolve command from user {user_id}")
            
            task_id = self.task_router.add_task(
                "ai_self_builder",
                task_type="evolution",
                priority=2,
                trigger_source="discord",
                metadata={"user_id": user_id, "command": "autoevolve"}
            )
            
            if task_id:
                return f"""🧠 **AI Evolution Initiated**

🔍 Scanning for missing modules and commands...
✨ Generating new capabilities autonomously...
🔄 GitHub sync enabled for bot distribution...
📝 Task ID: {task_id}
✅ Russo Jr is evolving - new modules will be auto-generated!"""
            else:
                return "❌ Failed to initiate auto-evolution. Please try again."
                
        except Exception as e:
            self.logger.error(f"Error in autoevolve command: {str(e)}")
            return f"❌ Error processing auto-evolution: {str(e)}"

    async def handle_build_self_command(self, args, user_id=None):
        """Handle /build_self command - alias for autoevolve with detailed output"""
        try:
            self.logger.info(f"Build-self command from user {user_id}")
            
            # Get module name if specified
            module_hint = args[0] if args else None
            
            task_id = self.task_router.add_task(
                "ai_self_builder",
                task_type="evolution",
                priority=1,
                trigger_source="discord",
                metadata={
                    "user_id": user_id, 
                    "command": "build_self",
                    "module_hint": module_hint
                }
            )
            
            if task_id:
                return f"""🔧 **AI Self-Building Initiated**

🎯 Target: {module_hint or 'Auto-detect missing capabilities'}
🧠 Analyzing current architecture...
⚡ High priority task queued
📝 Task ID: {task_id}
🚀 Building missing functionality autonomously!"""
            else:
                return "❌ Failed to initiate self-building. Please try again."
                
        except Exception as e:
            self.logger.error(f"Error in build_self command: {str(e)}")
            return f"❌ Error processing self-building: {str(e)}"

    async def handle_spawn_bot_command(self, args, user_id=None):
        """Handle /spawn_bot command - spawns new autonomous bot clone"""
        try:
            # Parse bot spawn parameters
            if not args:
                return """❌ **Usage**: `/spawn_bot name:<botname> brain:<1-100> [currencies:<BTC,ETH,USD>]`

**Examples:**
• `/spawn_bot name:MyTrader brain:75 currencies:BTC,ETH`
• `/spawn_bot name:ConservativeBot brain:25 currencies:USD`

**Brain Levels:**
• 1-25%: Conservative trading, basic modules
• 26-50%: Balanced approach, moderate modules  
• 51-75%: Aggressive trading, advanced modules
• 76-100%: Ultra-aggressive, all modules unlocked"""
            
            # Basic implementation - you'll need to expand this
            task_id = self.task_router.add_task(
                "bot_spawner",
                task_type="bot_spawn",
                priority=1,
                trigger_source="discord",
                metadata={"user_id": user_id, "command": "spawn_bot", "args": args}
            )
            
            if task_id:
                return f"""🤖 **Bot Spawning Initiated**

🧠 Creating autonomous trading bot...
📦 Preparing downloadable package...
🔄 GitHub integration enabled...
📝 Task ID: {task_id}
✅ Your bot will be ready shortly!"""
            else:
                return "❌ Failed to spawn bot. Please try again."
                
        except Exception as e:
            self.logger.error(f"Error in spawn_bot command: {str(e)}")
            return f"❌ Error spawning bot: {str(e)}"

    # Add placeholder handlers for missing commands
    async def handle_stocks_command(self, args, user_id=None):
        """Handle /stocks command - triggers stock data collection"""
        task_id = self.task_router.add_task("stock_data_collector", task_type="stock", priority=2, trigger_source="discord", metadata={"user_id": user_id, "command": "stocks"})
        return f"📈 **Stock Data Collection Initiated**\n🔄 Fetching latest market data...\n📝 Task ID: {task_id}" if task_id else "❌ Failed to queue stock data collection"

    async def handle_analyze_stocks_command(self, args, user_id=None):
        """Handle /analyze_stocks command"""
        task_id = self.task_router.add_task("stock_pattern_detector", task_type="stock", priority=2, trigger_source="discord", metadata={"user_id": user_id, "command": "analyze_stocks"})
        return f"🔍 **Stock Analysis Initiated**\n📊 Running pattern detection...\n📝 Task ID: {task_id}" if task_id else "❌ Failed to queue stock analysis"

    async def handle_execute_stock_trades_command(self, args, user_id=None):
        """Handle /execute_stock_trades command"""
        task_id = self.task_router.add_task("stock_trade_executor", task_type="stock", priority=1, trigger_source="discord", metadata={"user_id": user_id, "command": "execute_stock_trades"})
        return f"💰 **Stock Trade Execution Initiated**\n🎯 Analyzing positions...\n📝 Task ID: {task_id}" if task_id else "❌ Failed to queue trade execution"

    async def handle_track_stocks_command(self, args, user_id=None):
        """Handle /track_stocks command"""
        task_id = self.task_router.add_task("stock_portfolio_tracker", task_type="stock", priority=2, trigger_source="discord", metadata={"user_id": user_id, "command": "track_stocks"})
        return f"📋 **Portfolio Tracking Initiated**\n💼 Analyzing performance...\n📝 Task ID: {task_id}" if task_id else "❌ Failed to queue portfolio tracking"

    async def handle_summary_command(self, args, user_id=None):
        """Handle /summary command"""
        task_id = self.task_router.add_task("summary_reporter", task_type="utility", priority=2, trigger_source="discord", metadata={"user_id": user_id, "command": "summary"})
        return f"📊 **Trading Summary Generation**\n💰 Calculating P&L metrics...\n📝 Task ID: {task_id}" if task_id else "❌ Failed to queue summary generation"

    async def handle_summary_ai_command(self, args, user_id=None):
        """Handle /summary_ai command"""
        task_id = self.task_router.add_task("ai_summary_reporter", task_type="ai", priority=2, trigger_source="discord", metadata={"user_id": user_id, "command": "summary_ai"})
        return f"🧠 **AI Predictions Summary**\n🎯 Analyzing top confidence predictions...\n📝 Task ID: {task_id}" if task_id else "❌ Failed to queue AI summary"

    async def handle_top_earners_command(self, args, user_id=None):
        """Handle /top_earners command"""
        task_id = self.task_router.add_task("leaderboard_generator", task_type="utility", priority=2, trigger_source="discord", metadata={"user_id": user_id, "command": "top_earners"})
        return f"🏆 **Top Earners Analysis**\n🥇 Ranking top performers...\n📝 Task ID: {task_id}" if task_id else "❌ Failed to queue top earners analysis"

    async def handle_auto_on_command(self, args, user_id=None):
        """Handle /auto_on command"""
        task_id = self.task_router.add_task("auto_mode_controller", task_type="utility", priority=1, trigger_source="discord", metadata={"user_id": user_id, "command": "auto_on", "mode": "enable"})
        return f"🟢 **Auto Trading Mode ENABLED**\n⚡ Autonomous algorithms activated\n📝 Task ID: {task_id}" if task_id else "❌ Failed to enable auto trading"

    async def handle_auto_off_command(self, args, user_id=None):
        """Handle /auto_off command"""
        task_id = self.task_router.add_task("auto_mode_controller", task_type="utility", priority=1, trigger_source="discord", metadata={"user_id": user_id, "command": "auto_off", "mode": "disable"})
        return f"🔴 **Auto Trading Mode DISABLED**\n✋ Manual control restored\n📝 Task ID: {task_id}" if task_id else "❌ Failed to disable auto trading"

    async def handle_wallet_command(self, args, user_id=None):
        """Handle /wallet command"""
        action = args[0].lower() if args else "balance"
        return f"💰 **Wallet {action.title()} Report**\n🏦 Checking exchange balances...\n💡 Use `/wallet help` for options"

    async def handle_make_channel_command(self, args, user_id=None):
        """Handle /make_channel command"""
        channel_name = "_".join(args).lower() if args else None
        if not channel_name:
            return "❌ **Usage**: `/make_channel [channel_name]`"
        task_id = self.task_router.add_task("discord_channel_manager", task_type="utility", priority=2, trigger_source="discord", metadata={"user_id": user_id, "command": "make_channel", "channel_name": channel_name})
        return f"🔧 **Channel Creation**\n📝 Creating: #{channel_name}\nTask ID: {task_id}" if task_id else "❌ Failed to queue channel creation"

    async def handle_rename_channel_command(self, args, user_id=None):
        """Handle /rename_channel command"""
        if len(args) < 2:
            return "❌ **Usage**: `/rename_channel [old_name] [new_name]`"
        return f"🔧 **Channel Rename**\n📝 Renaming: #{args[0]} → #{args[1]}"

    async def handle_move_logs_channel_command(self, args, user_id=None):
        """Handle /move_logs_channel command"""
        channel_name = "_".join(args).lower() if args else None
        if not channel_name:
            return "❌ **Usage**: `/move_logs_channel [channel_name]`"
        return f"🔧 **Log Channel Updated**\n📝 Default logs: #{channel_name}"

    async def handle_autofix_command(self, args, user_id=None):
        """Handle /autofix command"""
        task_id = self.task_router.add_task("auto_fixer_v1", task_type="maintenance", priority=1, trigger_source="discord", metadata={"user_id": user_id, "command": "autofix"})
        return f"🔧 **Auto-Fix Initiated**\n🛠️ Running error fixing cycle...\n📝 Task ID: {task_id}" if task_id else "❌ Failed to initiate auto-fix"

    async def handle_inject_keys_command(self, args, user_id=None):
        """Handle /inject_keys command"""
        return "🔑 **API Key Injection**\n💡 Usage: `/inject_keys botname:<name> kraken=<key> alpaca=<key>`"

    async def handle_upgrade_bot_command(self, args, user_id=None):
        """Handle /upgrade_bot command"""
        botname = args[0] if args else None
        if not botname:
            return "❌ **Usage**: `/upgrade_bot botname:<name>`"
        return f"🔄 **Bot Upgrade**\n🤖 Upgrading: {botname}\n📦 Syncing with GitHub..."

    async def handle_list_my_bots_command(self, args, user_id=None):
        """Handle /list_my_bots command"""
        return f"🤖 **Your Autonomous Bots**\n\n📋 No bots found for user {user_id}\n💡 Use `/spawn_bot` to create your first bot!"

    async def handle_terminate_bot_command(self, args, user_id=None):
        """Handle /terminate_bot command"""
        botname = args[0] if args else None
        if not botname:
            return "❌ **Usage**: `/terminate_bot botname:<name>`"
        return f"⚠️ **Bot Termination**\n🤖 Terminating: {botname}\n🗑️ This action is permanent!"

    async def handle_assign_bot_command(self, args, user_id=None):
        """Handle /assign_bot command"""
        return "🤖 **Bot Assignment**\n💡 Usage: `/assign_bot @user name:<botname> brain:<%>`"
    
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
