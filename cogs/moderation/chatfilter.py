import re
from time import time
import asyncio
from contextlib import suppress
from unicodedata import normalize
from string import printable

from discord.ext import commands
from botutils import colors
import discord


aliases = {
    "a": ["@"],
    "i": ['1', 'l', r'\|', "!", "/", "j", r"\*", ";"],
    "o": ["0", "@"]
}


class ChatFilter(commands.Cog):
    def __init__(self, bot):
        if not hasattr(bot, "filtered_messages"):
            bot.filtered_messages = {}
        self.bot = bot
        self.config = bot.utils.cache("chatfilter")
        self.chatfilter_usage = self._chatfilter
        self.webhooks = {}

    def is_enabled(self, guild_id):
        return guild_id in self.config

    async def filter(self, content: str, filtered_words: list):
        def run_regex():
            regexes = {}
            flags = []
            for word in filtered_words:
                word = word.lower()
                if not all(c.lower() != c.upper() or c != "." for c in word):
                    if word in content:
                        flags.append(word)
                    continue
                for section in content.split():
                    if word in section:
                        if len(section) - len(word) > 2 and len(word) > 3:
                            flags.append(word)
                            continue
                    if word == section[1:]:
                        flags.append(word)
                        continue

                regexes[word] = []
                fmt = word.lower()

                # Add a max range of 2K chars for repeated letters like "fuuuuuck"
                matched = []
                for i, letter in enumerate(fmt):
                    if letter in matched:
                        continue
                    if letter not in aliases:
                        rgx = letter + "+[\s]*"
                        fmt = fmt.replace(letter, rgx)
                        matched.append(letter)

                # Add regexes for alias characters
                for letter, _aliases in aliases.items():
                    _aliases = [f"{alias}[\s]*" for alias in _aliases]
                    regex = f"({letter + '|' + '|'.join(_aliases)})+"
                    fmt = fmt.replace(letter, regex)
                fmt = fmt.replace("++", "+")  # Remove repeated ranges
                regexes[word].append(fmt)

                # Account for a singular changed character if it's a long word
                if len(word) > 4 and len(content) > 4:
                    for i in range(len(word)):
                        if i == 0:
                            continue
                        _word = list(word)
                        _word[i] = "."
                        regexes[word].append("".join(_word))

            for word, queries in regexes.items():
                query = "|".join(f"(?:{q})" for q in queries if len(q) > 1)
                try:
                    result = re.search(query, content)
                    if result:
                        trigger = result.group()
                        if any(trigger in w and trigger != w for w in content.split()):
                            continue
                        flags.append(trigger)
                except re.error:
                    pass
            return flags

        illegal = ("\\", "*", "`", "_", "||")
        content = str(content).lower()
        for char in illegal:
            content = content.replace(char, "")
        content = normalize('NFKD', content).encode('ascii', 'ignore').decode()
        content = "".join(c for c in content if c in printable)

        flags = await self.bot.loop.run_in_executor(None, run_regex)
        if not flags:
            return flags

        for flag in flags:
            filtered_word = f"{flag[0]}{f'{illegal[0]}*' * (len(flag) - 1)}"
            content = content.replace(flag.rstrip(" "), filtered_word)

        return content

    @commands.group(name="chatfilter")
    @commands.bot_has_permissions(embed_links=True)
    async def _chatfilter(self, ctx):
        if not ctx.invoked_subcommand:
            guild_id = ctx.guild.id
            toggle = "disabled"
            if ctx.guild.id in self.config and self.config[guild_id]["toggle"]:
                toggle = "enabled"
            e = discord.Embed(color=colors.pink)
            e.set_author(name="| Chat Filter", icon_url=ctx.author.avatar.url)
            e.set_thumbnail(url=ctx.guild.icon.url)
            e.description = "Deletes messages containing blocked words/phrases"
            e.add_field(
                name="◈ Usage",
                value=".chatfilter enable\n"
                ".chatfilter disable\n"
                ".chatfilter ignore #channel\n"
                ".chatfilter unignore #channel\n"
                ".chatfilter add {word/phrase}\n"
                ".chatfilter remove {word/phrase}\n"
                ".chatfilter toggle-bots\n"
                "`whether to filter bot messages`",
                inline=False,
            )
            if guild_id in self.config and self.config[guild_id]["blacklist"]:
                text = str(self.config[guild_id]["blacklist"])
                for text_group in [
                    text[i : i + 1000] for i in range(0, len(text), 1000)
                ]:
                    e.add_field(name="◈ Blacklisted Words/Phrases", value=text_group, inline=False)
            if guild_id in self.config and self.config[guild_id]["ignored"]:
                channels = []
                for channel_id in list(self.config[guild_id]["ignored"]):
                    channel = self.bot.get_channel(channel_id)
                    if not channel:
                        self.config[guild_id]["ignored"].remove(channel_id)
                        await self.config.flush()
                        continue
                    channels.append(channel.mention)
                if channels:
                    e.add_field(name="◈ Ignored Channels", value="\n".join(channels))
            e.set_footer(text=f"Current Status: {toggle}")
            await ctx.send(embed=e)

    @_chatfilter.command(name="enable")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def _enable(self, ctx):
        if ctx.guild.id in self.config and self.config[ctx.guild.id]["toggle"]:
            return await ctx.send("Chatfilter is already enabled")
        if ctx.guild.id in self.config:
            self.config[ctx.guild.id]["toggle"] = True
        else:
            self.config[ctx.guild.id] = {
                "toggle": True,
                "blacklist": [],
                "ignored": []
            }
        await ctx.send("Enabled chatfilter")
        await self.config.flush()

    @_chatfilter.command(name="disable")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def _disable(self, ctx):
        if ctx.guild.id not in self.config:
            return await ctx.send("Chatfilter is not enabled")
        self.config[ctx.guild.id]["toggle"] = False
        await ctx.send("Disabled chatfilter")
        await self.config.flush()

    @_chatfilter.command(name="ignore")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def _ignore(self, ctx, *channels: discord.TextChannel):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            return await ctx.send("Chatfilter isn't enabled")
        passed = []
        for channel in channels:
            if channel.id in self.config[guild_id]["ignored"]:
                await ctx.send(f"{channel.mention} is already ignored")
                continue
            self.config[guild_id]["ignored"].append(channel.id)
            passed.append(channel.mention)
        if passed:
            await ctx.send(f"I'll now ignore {', '.join(passed)}")
            await self.config.flush()

    @_chatfilter.command(name="unignore")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def _unignore(self, ctx, *channels: discord.TextChannel):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            return await ctx.send("This server has no ignored channels")
        passed = []
        for channel in channels:
            if channel.id not in self.config[guild_id]["ignored"]:
                await ctx.send(f"{channel.mention} isn't ignored")
                continue
            self.config[guild_id]["ignored"].remove(channel.id)
            passed.append(channel.mention)
        if passed:
            await ctx.send(f"I'll no longer ignore {', '.join(passed)}")
            await self.config.flush()

    @_chatfilter.command(name="add")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def _add(self, ctx, *, phrase):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            return await ctx.send("Chatfilter isn't enabled")
        if phrase in self.config[guild_id]["blacklist"]:
            return await ctx.send("That word/phrase is already blacklisted")
        self.config[guild_id]["blacklist"].append(phrase)
        await ctx.send(f"Added `{phrase}`")
        await self.config.flush()

    @_chatfilter.command(name="remove")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def _remove(self, ctx, *, phrase):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            return await ctx.send("Chatfilter isn't enabled")
        if phrase not in self.config[guild_id]["blacklist"] and not phrase.endswith("*"):
            return await ctx.send("Phrase/word not found")
        removed = []
        if phrase.endswith("*"):
            phrase = phrase.rstrip("*")
            for word in list(self.config[guild_id]["blacklist"]):
                _word = normalize('NFKD', word).encode('ascii', 'ignore').decode().lower()
                if _word.startswith(phrase):
                    self.config[guild_id]["blacklist"].remove(word)
                    removed.append(word)
            if not removed:
                return await ctx.send("No phrase/words found matching that")
            await ctx.send(f"Removed {', '.join(f'`{w}`' for w in removed)}")
            return await self.config.flush()
        self.config[guild_id]["blacklist"].remove(phrase)
        await ctx.send(f"Removed `{phrase}`")
        await self.config.flush()

    @_chatfilter.command(name="toggle-bots")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def toggle_bots(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            return await ctx.send("Chatfilter isn't enabled")
        if "bots" not in self.config[guild_id]:
            self.config[guild_id]["bots"] = True
            await self.config.flush()
        else:
            await self.config.remove_sub(guild_id, "bots")
        toggle = "Enabled" if "bots" in self.config[guild_id] else "Disabled"
        await ctx.send(f"{toggle} filtering bot messages")

    async def get_webhook(self, channel):
        if channel.id not in self.webhooks:
            webhook = await channel.create_webhook(name="Chatfilter")
            if channel.id not in self.webhooks:
                self.webhooks[channel.id] = webhook, False
            else:
                await webhook.delete()
                return self.webhooks[channel.id][0]
        return self.webhooks[channel.id][0]

    async def delete_webhook(self, channel):
        if self.webhooks[channel.id][1]:
            return
        self.webhooks[channel.id][1] = True
        webhook = self.webhooks[channel.id][0]
        await asyncio.sleep(25)
        if webhook:
            if channel.id in self.webhooks:
                del self.webhooks[channel.id]
            with suppress(Exception):
                await webhook.delete()

    @commands.Cog.listener()
    async def on_message(self, m: discord.Message):
        if hasattr(m.guild, "id") and m.guild.id in self.config:
            guild_id = m.guild.id
            if not self.config[guild_id]["toggle"]:
                return
            if not m.author.bot or "bots" in self.config[guild_id]:
                if m.channel.id in self.config[guild_id]["ignored"]:
                    return
                result = await self.filter(m.content, self.config[guild_id]["blacklist"])
                if result:
                    with suppress(Exception):
                        await m.delete()
                        if m.guild.id not in self.bot.filtered_messages:
                            self.bot.filtered_messages[m.guild.id] = {}
                        self.bot.filtered_messages[m.guild.id][m.id] = time()

                        if m.channel.permissions_for(m.guild.me).manage_webhooks:
                            w = await self.get_webhook(m.channel)
                            await w.send(
                                content=result,
                                avatar_url=m.author.avatar.url,
                                username=m.author.display_name
                            )
                            await self.delete_webhook(m.channel)
                return

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if hasattr(after.guild, "id") and after.guild.id in self.config:
            if not self.config[after.guild.id]["toggle"]:
                return
            guild_id = after.guild.id
            if not after.author.bot or "bots" in self.config[guild_id]:
                if after.channel.id in self.config[guild_id]["ignored"]:
                    return
                guild_id = before.guild.id
                if guild_id in self.config and self.config[guild_id]["blacklist"]:
                    for phrase in self.config[guild_id]["blacklist"]:
                        await asyncio.sleep(0)
                        if "\\" not in phrase:
                            after.content = after.content.replace("\\", "")
                        if after.author.bot or not self.bot.attrs.is_moderator(after.author):
                            for chunk in after.content.split():
                                await asyncio.sleep(0)
                                if phrase in chunk.lower():
                                    await asyncio.sleep(0.5)
                                    with suppress(discord.errors.NotFound):
                                        await after.delete()
                                    if after.guild.id not in self.bot.filtered_messages:
                                        self.bot.filtered_messages[after.guild.id] = {}
                                    self.bot.filtered_messages[after.guild.id][after.id] = time()
                                    return


def setup(bot):
    bot.add_cog(ChatFilter(bot), override=True)
