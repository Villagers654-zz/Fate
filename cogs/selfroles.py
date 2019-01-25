from discord.ext import commands
from os.path import isfile
import discord
import asyncio
import json

class SelfRoles:
	def __init__(self, bot):
		self.bot = bot
		self.toggle = {}
		self.message = {}
		self.roles = {}
		if isfile("./data/userdata/selfroles.json"):
			with open("./data/userdata/selfroles.json", "r") as infile:
				dat = json.load(infile)
				if "toggle" in dat and "message" in dat and "roles" in dat:
					self.toggle = dat["toggle"]
					self.message = dat["message"]
					self.roles = dat["roles"]

	@commands.command(name="selfroles", aliases=["sr"])
	@commands.has_permissions(administrator=True)
	async def _selfroles(self, ctx, config=None):
		reactions = ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣', '8⃣', '9⃣']
		if config is None:
			# iteration 1
			e = discord.Embed(color=0x80b0ff)
			e.set_author(name=ctx.author.name, icon_url=ctx.guild.icon_url)
			e.description = "Please send the first role name\n Type confirm when all are added\nType cancel to cancel"
			e.add_field(name="◈ Roles ◈", value="reaction : role")
			embed = await ctx.send(embed=e)
			await asyncio.sleep(0.5)
			await ctx.message.delete()
			def pred(m):
				return m.channel.id == ctx.channel.id and m.author.id == ctx.author.id
			try:
				msg = await self.bot.wait_for('message', check=pred, timeout=60)
			except asyncio.TimeoutError:
				await ctx.send("Timeout error")
			else:
				await msg.delete()
				if msg.content.lower() == "confirm":
					await ctx.send("you cannot confirm yet")
					await embed.delete()
				else:
					if msg.content.lower() == "cancel":
						await embed.delete()
					else:
						role_one = None
						msg.content = msg.content.replace("@", "")
						for role in ctx.guild.roles:
							if msg.content.lower() == role.name:
								role_one = role.name
								save = f"{role_one}"
								self.roles[str(ctx.guild.id)] = save
								break
						if role_one is None:
							for role in ctx.guild.roles:
								if msg.content.lower() in role.name.lower():
									role_one = role.name
									save = f"{role_one}"
									self.roles[str(ctx.guild.id)] = save
									break
						if role_one is None:
							await ctx.send("Role not found. please restart")
							await embed.delete()
						else:
							e = discord.Embed(color=0x80b0ff)
							e.set_author(name=ctx.author.name, icon_url=ctx.guild.icon_url)
							e.add_field(name="◈ Roles ◈", value=f"1 : {role_one}")
							e.description = "Please send the second role name\n Type confirm when all are added\nType cancel to cancel"
							await embed.edit(embed=e)
							try:
								msg = await self.bot.wait_for('message', check=pred, timeout=60)
							except asyncio.TimeoutError:
								await ctx.send("Timeout error")
							else:
								await msg.delete()
								if msg.content.lower() == "confirm":
									e.description = "Please type a channel name\nType cancel to cancel"
									await embed.edit(embed=e)
									try:
										msg = await self.bot.wait_for('message', check=pred, timeout=60)
									except asyncio.TimeoutError:
										await ctx.send("Timeout error")
									else:
										await msg.delete()
										check = 0
										for channel in ctx.guild.channels:
											if msg.content.lower() == channel.name.lower():
												e = discord.Embed(color=0x80b0ff)
												e.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
												e.add_field(name="◈ Roles ◈", value=f"1 : {role_one}")
												message = await channel.send(embed=e)
												self.message[str(ctx.guild.id)] = str(message.id)
												await embed.delete()
												await message.add_reaction(reactions[0])
												check = 1
												break
										if check == 0:
											for channel in ctx.guild.channels:
												if msg.content.lower() == channel.name.lower():
													e = discord.Embed(color=0x80b0ff)
													e.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
													e.add_field(name="◈ Roles ◈",  value=f"1 : {role_one}")
													message = await channel.send(embed=e)
													self.message[str(ctx.guild.id)] = str(message.id)
													await embed.delete()
													await message.add_reaction(reactions[0])
													check = 1
													break
										if check == 0:
											await ctx.send("Channel not found, please restart", delete_after=10)
											await embed.delete()
								else:
									# iteration two
									if msg.content.lower() == "cancel":
										await embed.delete()
									else:
										role_two = None
										msg.content = msg.content.replace("@", "")
										for role in ctx.guild.roles:
											if msg.content.lower() == role.name:
												role_two = role.name
												save = f"{self.roles[str(ctx.guild.id)]},{role_two}"
												self.roles[str(ctx.guild.id)] = save
												break
										if role_two is None:
											for role in ctx.guild.roles:
												if msg.content.lower() in role.name.lower():
													role_two = role.name
													save = f"{self.roles[str(ctx.guild.id)]},{role_two}"
													self.roles[str(ctx.guild.id)] = save
													break
										if role_two is None:
											await ctx.send("Role not found. please restart")
											await embed.delete()
										else:
											e = discord.Embed(color=0x80b0ff)
											e.set_author(name=ctx.author.name, icon_url=ctx.guild.icon_url)
											e.add_field(name="◈ Roles ◈", value=f"1 : {role_one}\n2 : {role_two}")
											e.description = "Please send the third role name\n Type confirm when all are added\nType cancel to cancel"
											await embed.edit(embed=e)
											try:
												msg = await self.bot.wait_for('message', check=pred, timeout=60)
											except asyncio.TimeoutError:
												await ctx.send("Timeout error")
											else:
												await msg.delete()
												if msg.content.lower() == "confirm":
													e.description = "Please type a channel name\nType cancel to cancel"
													await embed.edit(embed=e)
													try:
														msg = await self.bot.wait_for('message', check=pred, timeout=60)
													except asyncio.TimeoutError:
														await ctx.send("Timeout error")
													else:
														await msg.delete()
														check = 0
														for channel in ctx.guild.channels:
															if msg.content.lower() == channel.name.lower():
																e = discord.Embed(color=0x80b0ff)
																e.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
																e.add_field(name="◈ Roles ◈", value=f"1 : {role_one}\n2 : {role_two}")
																message = await channel.send(embed=e)
																self.message[str(ctx.guild.id)] = str(message.id)
																await embed.delete()
																await message.add_reaction(reactions[0])
																await message.add_reaction(reactions[1])
																check = 1
																break
														if check == 0:
															for channel in ctx.guild.channels:
																if msg.content.lower() == channel.name.lower():
																	e = discord.Embed(color=0x80b0ff)
																	e.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
																	e.add_field(name="◈ Roles ◈", value=f"1 : {role_one}\n2 : {role_two}")
																	message = await channel.send(embed=e)
																	self.message[str(ctx.guild.id)] = str(message.id)
																	await embed.delete()
																	await message.add_reaction(reactions[0])
																	await message.add_reaction(reactions[1])
																	check = 1
																	break
														if check == 0:
															await ctx.send("Channel not found, please restart", delete_after=10)
															await embed.delete()
												else:
													# iteration three
													if msg.content.lower() == "cancel":
														await embed.delete()
													else:
														role_three = None
														msg.content = msg.content.replace("@", "")
														for role in ctx.guild.roles:
															if msg.content.lower() == role.name:
																role_three = role.name
																save = f"{self.roles[str(ctx.guild.id)]},{role_two},{role_three}"
																self.roles[str(ctx.guild.id)] = save
																break
														if role_three is None:
															for role in ctx.guild.roles:
																if msg.content.lower() in role.name.lower():
																	role_three = role.name
																	save = f"{self.roles[str(ctx.guild.id)]},{role_two},{role_three}"
																	self.roles[str(ctx.guild.id)] = save
																	break
														if role_three is None:
															await ctx.send("Role not found. please restart")
															await embed.delete()
														else:
															e = discord.Embed(color=0x80b0ff)
															e.set_author(name=ctx.author.name, icon_url=ctx.guild.icon_url)
															e.add_field(name="◈ Roles ◈", value=f"1 : {role_one}\n2 : {role_two}\n3 : {role_three}")
															e.description = "Please send the third role name\n Type confirm when all are added\nType cancel to cancel"
															await embed.edit(embed=e)
															try:
																msg = await self.bot.wait_for('message', check=pred, timeout=60)
															except asyncio.TimeoutError:
																await ctx.send("Timeout error")
															else:
																await msg.delete()
																if msg.content.lower() == "confirm":
																	e.description = "Please type a channel name\nType cancel to cancel"
																	await embed.edit(embed=e)
																	try:
																		msg = await self.bot.wait_for('message', check=pred, timeout=60)
																	except asyncio.TimeoutError:
																		await ctx.send("Timeout error")
																	else:
																		await msg.delete()
																		check = 0
																		for channel in ctx.guild.channels:
																			if msg.content.lower() == channel.name.lower():
																				e = discord.Embed(color=0x80b0ff)
																				e.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
																				e.add_field(name="◈ Roles ◈", value=f"1 : {role_one}\n2 : {role_two}\n3 : {role_three}")
																				message = await channel.send(embed=e)
																				self.message[str(ctx.guild.id)] = str(message.id)
																				await embed.delete()
																				await message.add_reaction(reactions[0])
																				await message.add_reaction(reactions[1])
																				await message.add_reaction(reactions[2])
																				check = 1
																				break
																		if check == 0:
																			for channel in ctx.guild.channels:
																				if msg.content.lower() == channel.name.lower():
																					e = discord.Embed(color=0x80b0ff)
																					e.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
																					e.add_field(name="◈ Roles ◈", value=f"1 : {role_one}\n2 : {role_two}\n3 : {role_three}")
																					message = await channel.send(embed=e)
																					self.message[str(ctx.guild.id)] = str(message.id)
																					await embed.delete()
																					await message.add_reaction(reactions[0])
																					await message.add_reaction(reactions[1])
																					await message.add_reaction(reactions[2])
																					check = 1
																					break
																		if check == 0:
																			await ctx.send("Channel not found, please restart", delete_after=10)
																			await embed.delete()
																else:
																	# iteration four
																	if msg.content.lower() == "cancel":
																		await embed.delete()
																	else:
																		role_four = None
																		msg.content = msg.content.replace("@", "")
																		for role in ctx.guild.roles:
																			if msg.content.lower() == role.name:
																				role_four = role.name
																				save = f"{self.roles[str(ctx.guild.id)]},{role_two},{role_three},{role_four}"
																				self.roles[str(ctx.guild.id)] = save
																				break
																		if role_four is None:
																			for role in ctx.guild.roles:
																				if msg.content.lower() in role.name.lower():
																					role_four = role.name
																					save = f"{self.roles[str(ctx.guild.id)]},{role_two},{role_three},{role_four}"
																					self.roles[str(ctx.guild.id)] = save
																					break
																		if role_four is None:
																			await ctx.send(
																				"Role not found. please restart")
																			await embed.delete()
																		else:
																			e = discord.Embed(color=0x80b0ff)
																			e.set_author(name=ctx.author.name, icon_url=ctx.guild.icon_url)
																			e.add_field(name="◈ Roles ◈", value=f"1 : {role_one}\n2 : {role_two}\n3 : {role_three}\n4 : {role_four}")
																			e.description = "Please send the third role name\n Type confirm when all are added\nType cancel to cancel"
																			await embed.edit(embed=e)
																			try:
																				msg = await self.bot.wait_for('message', check=pred, timeout=60)
																			except asyncio.TimeoutError:
																				await ctx.send("Timeout error")
																			else:
																				await msg.delete()
																				if msg.content.lower() == "confirm":
																					e.description = "Please type a channel name\nType cancel to cancel"
																					await embed.edit(embed=e)
																					try:
																						msg = await self.bot.wait_for('message', check=pred, timeout=60)
																					except asyncio.TimeoutError:
																						await ctx.send("Timeout error")
																					else:
																						await msg.delete()
																						check = 0
																						for channel in ctx.guild.channels:
																							if msg.content.lower() == channel.name.lower():
																								e = discord.Embed(color=0x80b0ff)
																								e.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
																								e.add_field(name="◈ Roles ◈",
																									value=f"1 : {role_one}\n2 : {role_two}\n3 : {role_three}\n4 : {role_four}")
																								message = await channel.send(embed=e)
																								self.message[str(ctx.guild.id)] = str(message.id)
																								await embed.delete()
																								await message.add_reaction(reactions[0])
																								await message.add_reaction(reactions[1])
																								await message.add_reaction(reactions[2])
																								await message.add_reaction(reactions[3])
																								check = 1
																								break
																						if check == 0:
																							for channel in ctx.guild.channels:
																								if msg.content.lower() == channel.name.lower():
																									e = discord.Embed(color=0x80b0ff)
																									e.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
																									e.add_field(name="◈ Roles ◈",
																										value=f"1 : {role_one}\n2 : {role_two}\n3 : {role_three}\n4 : {role_four}")
																									message = await channel.send(embed=e)
																									self.message[str(ctx.guild.id)] = str(message.id)
																									await embed.delete()
																									await message.add_reaction(reactions[0])
																									await message.add_reaction(reactions[1])
																									await message.add_reaction(reactions[2])
																									await message.add_reaction(reactions[3])
																									check = 1
																									break
																						if check == 0:
																							await ctx.send("Channel not found, please restart", delete_after=10)
																							await embed.delete()
		else:
			if config == "disable":
				self.message[str(ctx.guild.id)] = "deleted"
				await ctx.send("Successfully disabled self roles")
		with open("./data/userdata/selfroles.json", "w") as outfile:
			json.dump({"toggle": self.toggle, "message": self.message, "roles": self.roles}, outfile, ensure_ascii=False)

	async def on_reaction_add(self, reaction, user):
		if isinstance(reaction.message.guild, discord.Guild):
			guild_id = str(reaction.message.guild.id)
			reaction_id = str(reaction.message.id)
			roles = self.roles[guild_id].split(",")
			reactions = ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣', '8⃣', '9⃣']
			if guild_id in self.message:
				if self.message[guild_id] == "deleted":
					pass
				else:
					if reaction_id == self.message[guild_id]:
						if reaction.emoji == reactions[0]:
							for role in reaction.message.guild.roles:
								if role.name == roles[0]:
									role = role
									await user.add_roles(role)
									break
						if reaction.emoji == reactions[1]:
							for role in reaction.message.guild.roles:
								if role.name == roles[1]:
									role = role
									await user.add_roles(role)
									break
						if reaction.emoji == reactions[2]:
							for role in reaction.message.guild.roles:
								if role.name == roles[2]:
									role = role
									await user.add_roles(role)
									break
						if reaction.emoji == reactions[3]:
							for role in reaction.message.guild.roles:
								if role.name == roles[3]:
									role = role
									await user.add_roles(role)
									break

	async def on_reaction_remove(self, reaction, user):
		if isinstance(reaction.message.guild, discord.Guild):
			guild_id = str(reaction.message.guild.id)
			reaction_id = str(reaction.message.id)
			roles = self.roles[guild_id].split(",")
			reactions = ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣', '8⃣', '9⃣']
			if guild_id in self.message:
				if self.message[guild_id] == "deleted":
					pass
				else:
					if reaction_id == self.message[guild_id]:
						if reaction.emoji == reactions[0]:
							for role in reaction.message.guild.roles:
								if role.name == roles[0]:
									role = role
									await user.remove_roles(role)
									break
						if reaction.emoji == reactions[1]:
							for role in reaction.message.guild.roles:
								if role.name == roles[1]:
									role = role
									await user.remove_roles(role)
									break
						if reaction.emoji == reactions[2]:
							for role in reaction.message.guild.roles:
								if role.name == roles[2]:
									role = role
									await user.remove_roles(role)
									break
						if reaction.emoji == reactions[3]:
							for role in reaction.message.guild.roles:
								if role.name == roles[3]:
									role = role
									await user.remove_roles(role)
									break

def setup(bot):
	bot.add_cog(SelfRoles(bot))
