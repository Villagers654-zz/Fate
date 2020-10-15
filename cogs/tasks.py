import asyncio
import websockets
import random
import traceback
import os
import time
from datetime import datetime
from zipfile import ZipFile

import discord
from discord.ext import commands, tasks
import pysftp

from utils import auth


class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.enabled_tasks = [
            self.status_task,
            self.log_queue,
            self.debug_log,
            self.auto_backup,
        ]

    def running_tasks(self):
        return [
            task
            for task in asyncio.all_tasks(self.bot.loop)
            if not task.done() and not task.cancelled()
        ]

    def running_task_names(self):
        return sorted([task.get_name() for task in self.running_tasks()])

    def ensure_all(self):
        """Start any core tasks that aren't running"""
        for task in self.enabled_tasks:
            if not task.is_running():
                task.start()
                self.bot.log(f"Started task {task.coro.__name__}", color="cyan")

    @tasks.loop()
    async def status_task(self):
        await asyncio.sleep(10)
        while True:
            motds = [
                "FBI OPEN UP",
                "YEET to DELETE",
                "Pole-Man",
                "♡Juice wrld♡",
                "Mad cuz Bad",
                "Quest for Cake",
                "Gone Sexual",
                "@EPFFORCE#1337 wuz here",
            ]
            stages = ["Serendipity", "Euphoria", "Singularity", "Epiphany"]
            for i in range(len(stages)):
                try:
                    await self.bot.change_presence(
                        status=discord.Status.online,
                        activity=discord.Game(name=f"Seeking For The Clock"),
                    )
                    await asyncio.sleep(45)
                    await self.bot.change_presence(
                        status=discord.Status.online,
                        activity=discord.Game(name=f"{stages[i]} | use .help"),
                    )
                    await asyncio.sleep(15)
                    await self.bot.change_presence(
                        status=discord.Status.idle,
                        activity=discord.Game(
                            name=f"SVR: {len(self.bot.guilds)} USR: {len(self.bot.users)}"
                        ),
                    )
                    await asyncio.sleep(15)
                    await self.bot.change_presence(
                        status=discord.Status.dnd,
                        activity=discord.Game(
                            name=f"{stages[i]} | {random.choice(motds)}"
                        ),
                    )
                except (
                    discord.errors.Forbidden,
                    discord.errors.HTTPException,
                    websockets.exceptions.ConnectionClosedError,
                ):
                    self.bot.log(
                        f"Error changing my status", "DEBUG", traceback.format_exc()
                    )
                await asyncio.sleep(15)

    @tasks.loop()
    async def debug_log(self):
        channel = self.bot.get_channel(self.bot.config["debug_channel"])
        log = []
        reads = 0
        while True:
            reads += 1
            with open("discord.log", "r") as f:
                lines = f.readlines()
            new_lines = len(lines) - len(log)
            if new_lines > 0:
                added_lines = lines[-new_lines:]
                msg = "".join(added_lines)
                char = "\u0000"
                for group in [msg[i : i + 1990] for i in range(0, len(msg), 1990)]:
                    group = group.replace(char, "")
                    if group:
                        while not channel:
                            channel = self.bot.get_channel(
                                self.bot.config["debug_channel"]
                            )
                            await asyncio.sleep(5)
                        await channel.send(f"```{group}```")
                log = [*log, *added_lines]
            if reads == 1000:
                with open("discord.log", "w") as f:
                    f.write("")
                log = []
                reads = 0
            await asyncio.sleep(1)

    @tasks.loop(seconds=1)
    async def log_queue(self):
        if not self.bot.is_ready():
            await self.bot.wait_until_ready()
        channel = await self.bot.fetch_channel(self.bot.config["log_channel"])
        if not self.bot.logs:
            return
        message = "```"
        mention = ""
        if any("CRITICAL" in log for log in self.bot.logs):
            owner = self.bot.get_user(self.bot.config["bot_owner_id"])
            mention = (
                f"{owner.mention} something went terribly wrong"
                if owner
                else "Critical Error\n"
            )
        for log in list(self.bot.logs):  # type: str
            original = str(log)
            mention = ""
            if "CRITICAL" in log:
                owner = self.bot.get_user(self.bot.config["bot_owner_id"])
                mention = (
                    f"{owner.mention} something went terribly wrong"
                    if owner
                    else "Critical Error\n"
                )
            if original in self.bot.logs:
                self.bot.logs.remove(original)
            if len(log) >= 2000:
                for group in self.bot.utils.split(log, 1990):
                    await channel.send(f"{mention}```{group}```")
                continue
            if len(message) + len(log) >= 1990:
                message += "```"
                await channel.send(mention + message)
                message = "```"
            message += log + "\n"
        message += "```"
        await channel.send(mention + message)

    @tasks.loop(hours=5)
    async def auto_backup(self):
        """Backs up files every x seconds and keeps them for x days"""

        def get_all_file_paths(directory):
            file_paths = []
            for root, directories, files in os.walk(directory):
                for filename in files:
                    if "backup" not in filename and "images" not in root:
                        filepath = os.path.join(root, filename)
                        file_paths.append(filepath)
            return file_paths

        keep_for = 7  # Days to keep each backup
        await asyncio.sleep(60 * 60)
        before = time.monotonic()

        def copy_files():
            # Copy all data to the ZipFile
            file_paths = get_all_file_paths("./data")
            fp = f"backup_{datetime.now()}.zip"
            with ZipFile(fp, "w") as _zip:
                for file in file_paths:
                    _zip.write(file)

            creds = auth.Backups()
            cnopts = pysftp.CnOpts()
            cnopts.hostkeys = None
            with pysftp.Connection(
                creds.host,
                username=creds.username,
                password=creds.password,
                port=creds.port,
                cnopts=cnopts,
            ) as sftp:
                # Remove older backups
                root = "/home/luck/Backups"
                for backup in sftp.listdir(root):
                    backup_time = datetime.strptime(
                        backup.split("_")[1].strip(".zip"), "%Y-%m-%d %H:%M:%S.%f"
                    )
                    if (datetime.now() - backup_time).days > keep_for:
                        try:
                            sftp.remove(backup)
                            self.bot.log(f"Removed backup {backup}")
                        except FileNotFoundError:
                            pass

                # Transfer then remove the local backup
                sftp.put(fp, os.path.join(root, fp))
                os.remove(fp)

        await self.bot.loop.run_in_executor(None, copy_files)
        ping = round((time.monotonic() - before) * 1000)
        self.bot.log(f"Ran Automatic Backup: {ping}ms")


def setup(bot):
    bot.add_cog(Tasks(bot))


def teardown(bot):
    main = bot.cogs["Tasks"]  # type: Tasks
    for task in main.enabled_tasks:
        task.stop()
        bot.log.info(f"Cancelled {task.coro.__name__}")
