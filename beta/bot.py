import asyncio
import json
from contextlib import suppress
from time import monotonic

from discord.ext import commands
from discord import ui
import discord


bot = commands.Bot(command_prefix="f.")
bot.remove_command("help")
style = discord.ButtonStyle
styles = {
    True: style.green,
    False: style.red
}


@bot.event
async def on_ready():
    print(bot.user)
    print(discord.__version__)


class Configure(ui.View):
    def __init__(self, options: dict, **kwargs):
        self.timeout = 5
        self.items = {}
        super().__init__(**kwargs)

        for option, toggle in options.items():
            button = discord.ui.Button(label=option, style=styles[toggle], custom_id=option)
            button.callback = self.process
            self.items[option] = button
            self.add_item(button)

    async def process(self, interaction):
        button = self.items[interaction.data["custom_id"]]
        button.style = styles[not button.style is style.green]
        await interaction.message.edit(content="Settings updated", view=self)

    @ui.button(label="Done", style=style.blurple)
    async def format_config(self, _button, interaction):
        await interaction.message.edit(content="Settings Saved")
        self.stop()


class ChoiceButtons(ui.View):
    def __init__(self):
        self.choice = None
        self.asyncio_event = asyncio.Event()
        super().__init__()

    @ui.button(label="Yes", style=style.green)
    async def yes(self, _button, interaction):
        self.choice = True
        await interaction.message.edit(view=None)
        self.asyncio_event.set()
        self.stop()

    @ui.button(label="No", style=style.red)
    async def no(self, _button, interaction):
        self.choice = False
        await interaction.message.edit(view=None)
        self.asyncio_event.set()
        self.stop()


async def get_answers_from(message: discord.Message, questions: list, delete_after: bool = False):
    choices = {}
    for i, question in enumerate(questions):
        # Update the message
        q = f"{i + 1}/{len(questions)} {question}"
        view = ChoiceButtons()
        await message.edit(content=q, view=view)
        # Wait for a button press
        try:
            await asyncio.wait_for(view.asyncio_event.wait(), timeout=25)
        except asyncio.TimeoutError:
            return await message.edit(content="Timed out waiting for response", view=None)

        # Save the users choice and continue
        choices[question] = view.choice

    with suppress(Exception):
        if delete_after:
            await message.delete()
        else:
            await message.edit(view=None)

    return choices


@bot.command(name="setup")
@commands.cooldown(1, 5, commands.BucketType.user)
async def setup(ctx):
    questions = [
        "Should I do X?",
        "Do you want me to Y?",
        "Do you want Z enabled?"
    ]
    msg = await ctx.send("Initial Msg")
    choices = await get_answers_from(msg, questions=questions)

    formatted = f"```json\n{json.dumps(choices, indent=2)}```"
    await msg.edit(content=formatted)


@bot.command(name="button")
async def button(ctx):
    view = Configure(options={
        "X": False,
        "Y": False,
        "Z": False
    }, timeout=10)
    msg = await ctx.send("Adjust your configuration", view=view)
    await view.wait()
    await ctx.send("View ended")


bot.run("NTExMTQxMzM1ODY1MjI5MzMz.W-gTdw.7XvdSnq6nwgdZQM5vzwhs3RABOc")
