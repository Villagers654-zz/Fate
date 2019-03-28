from discord.ext import commands
from os.path import isfile
import discord
import asyncio
import json

class SelfRoles:
	def __init__(self, bot):
		self.bot = bot
		self.message = {}
		self.roles = {}
		if isfile("./data/userdata/selfroles.json"):
			with open("./data/userdata/selfroles.json", "r") as infile:
				dat = json.load(infile)
				if "message" in dat and "roles" in dat:
					self.message = dat["message"]
					self.roles = dat["roles"]

	def save_data(self):
		with open("./data/userdata/selfroles.json", "w") as outfile:
			json.dump({"message": self.message, "roles": self.roles}, outfile, ensure_ascii=False)

	@commands.command(name="selfroles", aliases=["sr"])
	@commands.has_permissions(administrator=True)
	@commands.bot_has_permissions(manage_roles=True)
	async def _selfroles(self, ctx, config=None):
		reactions = ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣', '8⃣', '9⃣']
		if config == "disable":
			del self.message[str(ctx.guild.id)]
			del self.roles[str(ctx.guild.id)]
			await ctx.send("Disabled self roles")
		else:
			# iteration 1
			e = discord.Embed(color=0x80b0ff)
			e.set_author(name=ctx.author.name, icon_url=ctx.guild.icon_url)
			e.description = "Please send the first role name\nType cancel to cancel"
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
					await ctx.send("you cannot confirm yet", delete_after=5)
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
												e.add_field(name="◈ Self-Roles ◈", value=f"1 : {role_one}")
												message = await channel.send(embed=e)
												self.message[str(ctx.guild.id)] = str(message.id)
												await embed.delete()
												await message.add_reaction(reactions[0])
												check = 1
												break
										if check == 0:
											for channel in ctx.guild.channels:
												if msg.content.lower() in channel.name.lower():
													e = discord.Embed(color=0x80b0ff)
													e.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
													e.add_field(name="◈ Self-Roles ◈",  value=f"1 : {role_one}")
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
												save = f"{role_one},{role_two}"
												self.roles[str(ctx.guild.id)] = save
												break
										if role_two is None:
											for role in ctx.guild.roles:
												if msg.content.lower() in role.name.lower():
													role_two = role.name
													save = f"{role_one},{role_two}"
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
																e.add_field(name="◈ Self-Roles ◈", value=f"1 : {role_one}\n2 : {role_two}")
																message = await channel.send(embed=e)
																self.message[str(ctx.guild.id)] = str(message.id)
																await embed.delete()
																await message.add_reaction(reactions[0])
																await message.add_reaction(reactions[1])
																check = 1
																break
														if check == 0:
															for channel in ctx.guild.channels:
																if msg.content.lower() in channel.name.lower():
																	e = discord.Embed(color=0x80b0ff)
																	e.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
																	e.add_field(name="◈ Self-Roles ◈", value=f"1 : {role_one}\n2 : {role_two}")
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
																save = f"{role_one},{role_two},{role_three}"
																self.roles[str(ctx.guild.id)] = save
																break
														if role_three is None:
															for role in ctx.guild.roles:
																if msg.content.lower() in role.name.lower():
																	role_three = role.name
																	save = f"{role_one},{role_two},{role_three}"
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
																				e.add_field(name="◈ Self-Roles ◈", value=f"1 : {role_one}\n2 : {role_two}\n3 : {role_three}")
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
																				if msg.content.lower() in channel.name.lower():
																					e = discord.Embed(color=0x80b0ff)
																					e.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
																					e.add_field(name="◈ Self-Roles ◈", value=f"1 : {role_one}\n2 : {role_two}\n3 : {role_three}")
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
																				save = f"{role_one},{role_two},{role_three},{role_four}"
																				self.roles[str(ctx.guild.id)] = save
																				break
																		if role_four is None:
																			for role in ctx.guild.roles:
																				if msg.content.lower() in role.name.lower():
																					role_four = role.name
																					save = f"{role_one},{role_two},{role_three},{role_four}"
																					self.roles[str(ctx.guild.id)] = save
																					break
																		if role_four is None:
																			await ctx.send("Role not found. please restart")
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
																								e.add_field(name="◈ Self-Roles ◈",
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
																								if msg.content.lower() in channel.name.lower():
																									e = discord.Embed(color=0x80b0ff)
																									e.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
																									e.add_field(name="◈ Self-Roles ◈",
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
																					# iteration five
																					if msg.content.lower() == "cancel":
																						await embed.delete()
																					else:
																						role_five = None
																						msg.content = msg.content.replace("@", "")
																						for role in ctx.guild.roles:
																							if msg.content.lower() == role.name:
																								role_five = role.name
																								save = f"{role_one},{role_two},{role_three},{role_four},{role_five}"
																								self.roles[str(ctx.guild.id)] = save
																								break
																						if role_five is None:
																							for role in ctx.guild.roles:
																								if msg.content.lower() in role.name.lower():
																									role_five = role.name
																									save = f"{role_one},{role_two},{role_three},{role_four},{role_five}"
																									self.roles[str(ctx.guild.id)] = save
																									break
																						if role_five is None:
																							await ctx.send("Role not found. please restart")
																							await embed.delete()
																						else:
																							e = discord.Embed(color=0x80b0ff)
																							e.set_author(name=ctx.author.name, icon_url=ctx.guild.icon_url)
																							e.add_field(name="◈ Roles ◈", value=f"1 : {role_one}\n2 : {role_two}\n3 : {role_three}\n4 : {role_four}\n5 : {role_five}")
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
																												e.add_field(name="◈ Self-Roles ◈", value=f"1 : {role_one}\n2 : {role_two}\n3 : {role_three}\n4 : {role_four}\n5 : {role_five}")
																												message = await channel.send(embed=e)
																												self.message[str(ctx.guild.id)] = str(message.id)
																												await embed.delete()
																												await message.add_reaction(reactions[0])
																												await message.add_reaction(reactions[1])
																												await message.add_reaction(reactions[2])
																												await message.add_reaction(reactions[3])
																												await message.add_reaction(reactions[4])
																												check = 1
																												break
																										if check == 0:
																											for channel in ctx.guild.channels:
																												if msg.content.lower() in channel.name.lower():
																													e = discord.Embed(color=0x80b0ff)
																													e.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
																													e.add_field(name="◈ Self-Roles ◈", value=f"1 : {role_one}\n2 : {role_two}\n3 : {role_three}\n4 : {role_four}\n5 : {role_five}")
																													message = await channel.send(embed=e)
																													self.message[str(ctx.guild.id)] = str(message.id)
																													await embed.delete()
																													await message.add_reaction(reactions[0])
																													await message.add_reaction(reactions[1])
																													await message.add_reaction(reactions[2])
																													await message.add_reaction(reactions[3])
																													await message.add_reaction(reactions[4])
																													check = 1
																													break
																										if check == 0:
																											await ctx.send("Channel not found, please restart", delete_after=10)
																											await embed.delete()
																								else:
																									#iteration six
																									if msg.content.lower() == "cancel":
																										await embed.delete()
																									else:
																										role_six = None
																										msg.content = msg.content.replace("@", "")
																										for role in ctx.guild.roles:
																											if msg.content.lower() == role.name:
																												role_six = role.name
																												save = f"{role_one},{role_two},{role_three},{role_four},{role_five},{role_six}"
																												self.roles[str(ctx.guild.id)] = save
																												break
																										if role_six is None:
																											for role in ctx.guild.roles:
																												if msg.content.lower() in role.name.lower():
																													role_six = role.name
																													save = f"{role_one},{role_two},{role_three},{role_four},{role_five},{role_six}"
																													self.roles[str(ctx.guild.id)] = save
																													break
																										if role_six is None:
																											await ctx.send("Role not found. please restart")
																											await embed.delete()
																										else:
																											e = discord.Embed(color=0x80b0ff)
																											e.set_author(name=ctx.author.name, icon_url=ctx.guild.icon_url)
																											e.add_field(name="◈ Roles ◈", value=f"1 : {role_one}\n2 : {role_two}\n3 : {role_three}\n4 : {role_four}\n5 : {role_five}")
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
																																e.add_field(name="◈ Self-Roles ◈", value=f"1 : {role_one}\n2 : {role_two}\n3 : {role_three}\n4 : {role_four}\n5 : {role_five}\n6 : {role_six}")
																																message = await channel.send(embed=e)
																																self.message[str(ctx.guild.id)] = str(message.id)
																																await embed.delete()
																																await message.add_reaction(reactions[0])
																																await message.add_reaction(reactions[1])
																																await message.add_reaction(reactions[2])
																																await message.add_reaction(reactions[3])
																																await message.add_reaction(reactions[4])
																																await message.add_reaction(reactions[5])
																																check = 1
																																break
																														if check == 0:
																															for channel in ctx.guild.channels:
																																if msg.content.lower() in channel.name.lower():
																																	e = discord.Embed(color=0x80b0ff)
																																	e.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
																																	e.add_field(name="◈ Self-Roles ◈", value=f"1 : {role_one}\n2 : {role_two}\n3 : {role_three}\n4 : {role_four}\n5 : {role_five}\n6 : {role_six}")
																																	message = await channel.send(embed=e)
																																	self.message[str(ctx.guild.id)] = str(message.id)
																																	await embed.delete()
																																	await message.add_reaction(reactions[0])
																																	await message.add_reaction(reactions[1])
																																	await message.add_reaction(reactions[2])
																																	await message.add_reaction(reactions[3])
																																	await message.add_reaction(reactions[4])
																																	await message.add_reaction(reactions[5])
																																	check = 1
																																	break
																														if check == 0:
																															await ctx.send("Channel not found, please restart", delete_after=10)
																															await embed.delete()
		self.save_data()

	async def on_raw_reaction_add(self, payload):
		server = self.bot.get_guild(payload.guild_id)
		user = server.get_member(payload.user_id)
		if not user.bot:
			guild_id = str(payload.guild_id)
			reaction_id = str(payload.message_id)
			reactions = ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣', '8⃣', '9⃣']
			if guild_id in self.message:
				roles = self.roles[guild_id].split(",")
				if reaction_id == self.message[guild_id]:
					if str(payload.emoji) == reactions[0]:
						for role in server.roles:
							if role.name == roles[0]:
								await user.add_roles(role)
								break
					if str(payload.emoji) == reactions[1]:
						for role in server.roles:
							if role.name == roles[1]:
								await user.add_roles(role)
								break
					if str(payload.emoji) == reactions[2]:
						for role in server.roles:
							if role.name == roles[2]:
								await user.add_roles(role)
								break
					if str(payload.emoji) == reactions[3]:
						for role in server.roles:
							if role.name == roles[3]:
								await user.add_roles(role)
								break
					if str(payload.emoji) == reactions[4]:
						for role in server.roles:
							if role.name == roles[4]:
								await user.add_roles(role)
								break
					if str(payload.emoji) == reactions[5]:
						for role in server.roles:
							if role.name == roles[5]:
								await user.add_roles(role)
								break

	async def on_raw_reaction_remove(self, payload):
		server = self.bot.get_guild(payload.guild_id)
		user = server.get_member(payload.user_id)
		if not user.bot:
			guild_id = str(payload.guild_id)
			reaction_id = str(payload.message_id)
			reactions = ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣', '8⃣', '9⃣']
			if guild_id in self.message:
				roles = self.roles[guild_id].split(",")
				if self.message[guild_id] == reaction_id:
					if reaction_id == self.message[guild_id]:
						if str(payload.emoji) == reactions[0]:
							for role in server.roles:
								if role.name == roles[0]:
									await user.remove_roles(role)
									break
						if str(payload.emoji) == reactions[1]:
							for role in server.roles:
								if role.name == roles[1]:
									await user.remove_roles(role)
									break
						if str(payload.emoji) == reactions[2]:
							for role in server.roles:
								if role.name == roles[2]:
									await user.remove_roles(role)
									break
						if str(payload.emoji) == reactions[3]:
							for role in server.roles:
								if role.name == roles[3]:
									await user.remove_roles(role)
									break
						if str(payload.emoji) == reactions[4]:
							for role in server.roles:
								if role.name == roles[4]:
									await user.remove_roles(role)
									break
						if str(payload.emoji) == reactions[5]:
							for role in server.roles:
								if role.name == roles[5]:
									await user.remove_roles(role)
									break

	async def on_message_delete(self, m: discord.Message):
		guild_id = str(m.guild.id)
		if guild_id in self.message:
			if self.message[guild_id] == str(m.id):
				del self.message[guild_id]
				del self.roles[guild_id]
				self.save_data()

	async def on_guild_remove(self, guild):
		guild_id = str(guild.id)
		if guild_id in self.message:
			del self.message[guild_id]
			del self.roles[guild_id]
			self.save_data()

def setup(bot):
	bot.add_cog(SelfRoles(bot))
