import os

import discord
from discord.ext import commands

from botutils import config


# def is_guild_owner():
# 	async def predicate(ctx):
# 		return ctx.author.id == ctx.guild.owner.id or (
# 			ctx.author.id == config.owner_id())  # for testing
#
# 	return commands.check(predicate)


class Archive(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.saving = {}

    @commands.command(name="archive")
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 25, commands.BucketType.channel)
    async def _archive(self, ctx, amount: int):
        if amount > 1000:
            if not config.owner(ctx):
                return await ctx.send("You cannot save more than 1000 messages")
        self.saving[str(ctx.channel.id)] = "saving"
        async with ctx.typing():
            log = ""
            async for msg in ctx.channel.history(limit=amount):
                log = f"{msg.created_at.strftime('%I:%M%p')} | {msg.author.display_name}: {msg.content}\n{log}"
            with open(f"./data/{ctx.channel.name}.txt", "w") as f:
                f.write(log)
            path = os.getcwd() + f"/data/{ctx.channel.name}.txt"
            await ctx.send(file=discord.File(path))
            os.remove(f"./data/{ctx.channel.name}.txt")
            del self.saving[str(ctx.channel.id)]

    # @commands.command(name='ss-server-contents')
    # @commands.cooldown(1, 60, commands.BucketType.guild)
    # @is_guild_owner()
    # @commands.bot_has_permissions(administrator=True)
    # async def ss_server_contents(self, ctx):
    # 	async with ctx.channel.typing():
    # 		path = f'./static/{ctx.guild.id}'
    # 		try:
    # 			os.remove(path)
    # 		except:
    # 			pass
    # 		os.mkdir(path)
    # 		for channel in ctx.guild.text_channels:
    # 			if channel.category:
    # 				cat_path = join(path, channel.category.name)
    # 				if not os.path.isdir(cat_path):
    # 					os.mkdir(cat_path)
    # 				chnl_path = join(path, channel.category.name, channel.name)
    # 				os.mkdir(chnl_path)
    # 			else:
    # 				chnl_path = join(path, channel.name)
    # 			cnt_path = join(chnl_path, 'content')
    # 			os.mkdir(cnt_path)


#
# 			messages = await channel.history(oldest_first=True).flatten()
# 			chat_history = ''
#
# 			for msg in messages:
# 				msg_content = f'\n{msg.created_at.strftime("%I:%M%p")} - {msg.author} | '
# 				msg_path = join(cnt_path, str(msg.id))
#
# 				if msg.attachments:
# 					os.mkdir(msg_path)
# 					for attachment in msg.attachments:
# 						await attachment.save(join(msg_path, attachment.filename))
# 						msg_content += f'[Attachment at "{join(msg_path, attachment.filename)}"]\n'
# 					for i, embed in enumerate(msg.embeds):
# 						with open(join(msg_path, f'embed-{i}'), 'w') as f:
# 							f.write(str(embed.to_dict()))
# 						msg_content += f'[Embed at "{join(msg_path, f"embed-{i}")}"]\n'
#
# 				chat_history += msg_content + msg.content
#
# 			with open(join(chnl_path, 'chat-history'), 'w') as f:
# 				f.write(chat_history)
# 			await ctx.send(f"Archived contents of {channel.mention}")
#
# 		await ctx.send('Compressing files')
# 		file_paths = []
# 		for root, directories, files in os.walk(path):
# 			for filename in files:
# 				filepath = os.path.join(root, filename)
# 				file_paths.append(filepath)
# 		with ZipFile('Archive.zip', 'w') as zip:
# 			for file in file_paths:
# 				zip.write(file)
# 		await ctx.send('Saved Server Contents')
# 		try:
# 			await ctx.send(file=discord.File('Archive.zip'))
# 		except:
# 			await ctx.send('File too big to send')
#
# @commands.command(name='export')
# @commands.is_owner()
# async def export(self, ctx, channel: discord.TextChannel = None):
# 	if not channel:
# 		channel = ctx.channel
# 	file = 'archiver/DiscordChatExporter.Cli.dll'
# 	dir = '/home/luck/Fate/static'
# 	os.system(f'dotnet {file} export -t "{outh.tokens("fatezero")}" -b -c {channel.id} -o {dir}')
# 	file = [file for file in os.listdir('static') if '.html' in file][0]
# 	await ctx.send(file=discord.File(f'./static/{file}'))
# 	os.remove(f'./static/{file}')
#
# @commands.command(name='export-guild')
# @commands.is_owner()
# async def export_guild(self, ctx, guild_id: int):
# 	file = 'archiver/DiscordChatExporter.Cli.dll'
# 	dir = '/home/luck/Fate/static/export'
# 	if not os.path.exists(dir):
# 		os.mkdir(dir)
# 	os.system(f'dotnet {file} exportguild -t "{outh.tokens("fatezero")}" -b -g {guild_id} -o {dir}')
# 	files = [file for file in os.listdir('static/export') if '.html' in file]
# 	for file in files:
# 		try:
# 			await ctx.send(file=discord.File(f'./static/export/{file}'))
# 		except:
# 			await ctx.send(f"File `{file}` is too large")
# 		os.remove(f'./static/export/{file}')
# 	await ctx.send('Done')


def setup(bot):
    bot.add_cog(Archive(bot))
