import asyncio
from discord.ext import commands
import discord
from botutils import colors, get_prefix


class Audit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.perms = [p for p in dir(discord.AuditLogAction) if not p.startswith("_")]

    @commands.group(name="audit", description="Helps search through the audit")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _audit(self, ctx, *args):
        p = get_prefix(ctx)
        if not args or len(args) > 2:
            e = discord.Embed(color=colors.cyan)
            e.set_author(name="Audit Log Data", icon_url=ctx.author.avatar_url)
            e.set_thumbnail(url=ctx.guild.icon_url)
            e.add_field(
                name="◈ Commands ◈",
                value=".audit [action]\n"
                      ".audit [amount]\n"
                      ".audit [action] [amount]\n"
                      ".audit @user [amount]\n",
                inline=False,
            )
            e.add_field(
                name="◈ Actions ◈",
                value="Examples: kick, ban, message_delete\nFor a full list "
                     f"run `{p}audit types`",
                inline=False,
            )
            return await ctx.send(embed=e)

        if args[0] == "types":
            return await ctx.send(f", ".join(self.perms))

        _audit = discord.AuditLogAction
        entries = []
        counter = 0
        log_type = None
        user = None
        limit = 1

        if len(args) == 1:
            if not args[0].isdigit() and args[0] not in self.perms:
                return await ctx.send(f"That's not an event. Run `{p}audit types`")
            if args[0].isdigit():
                limit = int(args[0])
                if limit > 50:
                    limit = 50
            elif args[0] in self.perms:
                log_type = eval(f"_audit.{args[0]}")

        elif len(args) == 2:
            if "@" in args[0]:
                converter = commands.UserConverter()
                try:
                    user = await converter.convert(ctx, args[0])
                except discord.errors.NotFound:
                    return await ctx.send("User not found")
            elif args[0] in self.perms or args[0]:
                log_type = eval(f"_audit.{args[0]}")
            else:
                return await ctx.send("Invalid usage")
            if not args[1].isdigit():
                return await ctx.send("Invalid usage")
            limit = int(args[1])

        if user:
            search = ctx.guild.audit_logs(limit=128, action=log_type)
        else:
            search = ctx.guild.audit_logs(limit=limit, action=log_type)
        async for entry in search:
            if user:
                if hasattr(entry, "user") and entry.user and entry.user.id == user.id:
                    entries.append(entry)
                    counter += 1
                elif hasattr(entry, "target") and entry.target and entry.target.id == user.id:
                    entries.append(entry)
                    counter += 1
            else:
                entries.append(entry)
                counter += 1
            if counter == limit:
                break
        if not entries:
            return await ctx.send("Nothing found")

        def create_embed():
            e = discord.Embed(color=self.bot.config["theme_color"])
            e.set_author(name="AuditLog Results", icon_url=ctx.author.avatar_url)
            e.set_thumbnail(url=ctx.guild.icon_url)
            e.description = "\n".join(_page)
            e.set_footer(text=f"Page 1/{len(pages)}")
            pages.append(e)

        pages = []
        _page = []
        for i, entry in enumerate(entries):
            target = entry.target
            if isinstance(target, discord.Object):
                target = target.id
            line = f"{entry.user} {entry.action.name} to {target}"
            _page.append(line)
            if len(_page) == 9:
                create_embed()
                _page = []
        if _page:
            create_embed()

        async def add_emojis_task():
            """ So the bot can read reactions before all are added """
            for emoji in emojis:
                await msg.add_reaction(emoji)
                await asyncio.sleep(0.5)
            return

        index = 0
        emojis = ["🏡", "⏪", "⏩"]
        pages[0].set_footer(
            text=f"Page {index + 1}/{len(pages)}"
        )
        msg = await ctx.send(embed=pages[0])
        if len(pages) == 1:
            return

        self.bot.loop.create_task(add_emojis_task())
        while True:
            try:
                reaction, user = await self.bot.utils.get_reaction(ctx, timeout=25, ignore_timeout=False)
            except asyncio.TimeoutError:
                return await msg.clear_reactions()
            emoji = reaction.emoji

            if emoji == emojis[0]:  # home
                index = 0

            if emoji == emojis[1]:
                index -= 1

            if emoji == emojis[2]:
                index += 1

            if index > len(pages) - 1:
                index = len(pages) - 1

            if index < 0:
                index = 0

            pages[index].set_footer(
                text=f"Page {index + 1}/{len(pages)}"
            )
            await msg.edit(embed=pages[index])
            await msg.remove_reaction(reaction, ctx.author)


def setup(bot):
    bot.add_cog(Audit(bot))
