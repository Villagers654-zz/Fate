"""
cogs.core.tasks
~~~~~~~~~~~~~~~~

Cog for managing the core bot tasks like it's status, and backups

:copyright: (C) 2021-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""

import asyncio
import websockets
import random
import traceback
import os
import time
from datetime import datetime
from zipfile import ZipFile
import subprocess

import discord
from discord.ext import commands, tasks
import psutil

from botutils import split, CooldownManager


class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.enabled_tasks = [
            self.cog_cleanup,
            self.log_queue,
            self.auto_backup,
            self.cleanup_pool,
            self.warn_if_storage_full
        ]
        for task in self.enabled_tasks:
            task.start()
            bot.log(f"Started {task.coro.__name__}")

    def cog_unload(self):
        for task in self.enabled_tasks:
            if task.is_running():
                task.cancel()
                self.bot.log.info(f"Cancelled {task.coro.__name__}")

    def ensure_all(self):
        """Start any core tasks that aren't running"""
        for task in self.enabled_tasks:
            if not task.is_running():
                task.start()
                self.bot.log(f"Started task {task.coro.__name__}", color="cyan")

    @tasks.loop(seconds=60)
    async def warn_if_storage_full(self):
        if psutil.disk_usage("/").percent >= 95:
            self.bot.log.critical("storage usage has passed 95%")

    @tasks.loop(minutes=1)
    async def cog_cleanup(self):
        # Clean the filtered messages index by only keeping recent deletes
        if not hasattr(self.bot, "filtered_messages"):
            self.bot.filtered_messages = {}
        objects_removed = 0
        for guild_id, msgs in list(self.bot.filtered_messages.items()):
            await asyncio.sleep(0)
            for msg_id, deleted_at in list(msgs.items()):
                await asyncio.sleep(0)
                if time.time() - 1800 > deleted_at:
                    del self.bot.filtered_messages[guild_id][msg_id]
                    objects_removed += 1
            if not self.bot.filtered_messages[guild_id]:
                del self.bot.filtered_messages[guild_id]
                objects_removed += 1

        for cog in list(self.bot.cogs.keys()):
            for attr_name in dir(cog):
                await asyncio.sleep(0)
                attr = getattr(cog, attr_name)
                if isinstance(attr, CooldownManager):
                    count = len(attr.index)
                    attr.cleanup()
                    objects_removed += count


    @tasks.loop(hours=1)
    async def cleanup_pool(self):
        if self.bot.pool:
            await self.bot.pool.clear()
            self.bot.log.debug("Cleared the pool")

    @tasks.loop(minutes=1)
    async def prefix_cleanup_task(self):
        uncached = 0
        for guild_id, data in list(self.bot.guild_prefixes.items()):
            await asyncio.sleep(0)
            if isinstance(data, float):
                last_used = data
            else:
                last_used = data[1]
            if last_used > time.time() - 60 * 60:
                del self.bot.guild_prefixes[guild_id]
                uncached += 1
        self.bot.log.debug(f"Removed {uncached} unused prefixes from guild cache")
        uncached = 0

        for user_id, data in list(self.bot.user_prefixes.items()):
            await asyncio.sleep(0)
            if isinstance(data, float):
                last_used = data
            else:
                last_used = data["last_used"]
            if last_used > time.time() - 60 * 60:
                del self.bot.user_prefixes[user_id]
                uncached += 1
        self.bot.log.debug(f"Removed {uncached} unused prefixes from guild cache")

    @tasks.loop()
    async def status_task(self):
        await asyncio.sleep(9)
        while True:
            await asyncio.sleep(1)
            motds = [
                "FBI OPEN UP",
                "YEET to DELETE",
                "Pole-Man",
                "♡Juice wrld♡",
                "Mad cuz Bad",
                "Quest for Cake",
                "Gone Sexual"
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
                    users = 0
                    for guild in list(self.bot.guilds):
                        await asyncio.sleep(0)
                        users += guild.member_count
                    await self.bot.change_presence(
                        status=discord.Status.idle,
                        activity=discord.Game(
                            name=f"SVR: {len(self.bot.guilds)} USR: {users}"
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
        await asyncio.sleep(1)
        channel = self.bot.get_channel(self.bot.config["debug_channel"])
        log = []
        reads = 0
        while True:
            await asyncio.sleep(1)
            reads += 1
            async with self.bot.utils.open("discord.log", "r") as f:
                lines = await f.readlines()
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
                async with self.bot.utils.open("discord.log", "w") as f:
                    await f.write("")
                log = []
                reads = 0

    @tasks.loop(seconds=1)
    async def log_queue(self):
        await asyncio.sleep(1)
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
            await asyncio.sleep(0)
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
                for group in split(log, 1990):
                    await channel.send(f"{mention}```{group}```")
                continue
            if len(message) + len(log) >= 1990:
                message += "```"
                await channel.send(mention + message)
                message = "```"
            message += log + "\n"
        message += "```"
        await channel.send(mention + message)

    @tasks.loop(seconds=25)
    async def auto_backup(self):
        """Backs up files every x seconds and keeps them for x days"""
        await asyncio.sleep(1)
        def get_all_file_paths(directory):
            file_paths = []
            for root, directories, files in os.walk(directory):
                for filename in files:
                    if "backup" not in filename and "images" not in root:
                        filepath = os.path.join(root, filename)
                        file_paths.append(filepath)
            return file_paths

        def copy_files():
            # Copy all data to the ZipFile
            root = self.bot.config["backups_location"]
            path = os.path.join(root, "local")
            file_paths = get_all_file_paths("./data")
            fp = os.path.join(path, f"backup_{datetime.now()}.zip")

            with ZipFile(fp, "w") as _zip:
                for file in file_paths:
                    _zip.write(file)

            for subdir in ["local", "mysql"]:
                for backup in os.listdir(os.path.join(root, subdir)):
                    if ".zip" in backup or ".sql" in backup:
                        backup_time = datetime.strptime(
                            backup.split("_")[1].strip(".zip").strip(".sql"), "%Y-%m-%d %H:%M:%S.%f"
                        )
                    else:
                        backup_time = datetime.strptime(
                            backup, "%Y-%m-%d %H:%M:%S.%f"
                        )
                    if (datetime.now() - backup_time).days > keep_for:
                        if ".zip" in backup or ".sql" in backup:
                            os.remove(os.path.join(root, subdir, backup))
                        else:
                            os.rmdir(os.path.join(root, subdir, backup))
                        self.bot.log.info(f"Removed backup {backup}")

        sleep_for = self.bot.config["backup_every_?_hours"] * 60 * 60
        try:
            await asyncio.sleep(sleep_for)
            keep_for = self.bot.config["keep_backups_for_?_days"]
            creds = self.bot.auth["MySQL"]

            # Backup MySQL DB
            before = time.monotonic()
            db_path = os.path.join(self.bot.config["backups_location"], "mysql")
            fp = os.path.join(db_path, f"backup_{datetime.now()}.sql")
            process = subprocess.Popen(
                f"mysqldump -u root -p{creds['password']} fate > '{fp}'",
                shell=True
            )
            while True:
                await asyncio.sleep(1.21)
                if not process.poll():
                    break
            ping = round((time.monotonic() - before) * 1000)
            self.bot.log.info(f"Backed up SQL Database: {ping}ms")

            # Backup MongoDB
            before = time.monotonic()
            db_path = os.path.join(self.bot.config["backups_location"], "mongo")
            fp = os.path.join(db_path, f"{datetime.now()}")
            process = subprocess.Popen(
                f"mongodump --db fate --out '{fp}'", shell=True
            )
            while True:
                await asyncio.sleep(1.21)
                if not process.poll():
                    break
            ping = round((time.monotonic() - before) * 1000)
            self.bot.log.info(f"Backed up Mongo Database: {ping}ms")

            # Backup Local Files
            before = time.monotonic()
            await self.bot.loop.run_in_executor(None, copy_files)
            ping = round((time.monotonic() - before) * 1000)
            self.bot.log(f"Ran Automatic Backup: {ping}ms")
        except asyncio.CancelledError as error:
            raise error
        except:
            self.bot.log.critical(f"Backup task errored:\n{traceback.format_exc()}")


def setup(bot):
    bot.add_cog(Tasks(bot), override=True)
