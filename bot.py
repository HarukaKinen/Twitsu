from asyncio import tasks
from discord.ext import commands
import calendar
import asyncio
import discord
import time
import os

from discord_token import TOKEN

bot = commands.Bot(command_prefix="!", help_command = None)
timestamp = calendar.timegm(time.gmtime())

def check_if_it_is_me(ctx):
    return ctx.message.author.id == 276627005280092162

@bot.event
async def on_ready():
    # count current asyncio loop
    task = len([task for task in asyncio.Task.all_tasks() if not task.done()])
    await bot.change_presence(status = discord.Status.dnd, activity = discord.Game(name = f"Now processing {task} tasks."))

@bot.command()
@commands.check(check_if_it_is_me)
async def load(ctx, extension):
    bot.load_extension(f"Cogs.{extension}")
    await ctx.send(f"已加载 {extension}")

@bot.command()
@commands.check(check_if_it_is_me)
async def unload(ctx, extension):
    bot.unload_extension(f"Cogs.{extension}")
    await ctx.send(f"已卸载 {extension}")

@bot.command()
@commands.check(check_if_it_is_me)
async def reload(ctx, extension):
    bot.reload_extension(f"Cogs.{extension}")
    await ctx.send(f"已重载 {extension}")

for filename in os.listdir("./Cogs"):
    if filename.endswith(".py") and filename != "settings.py" and not (filename.startswith("__")):
        bot.load_extension(f"Cogs.{filename[:-3]}")

if __name__ == "__main__":
    bot.run(TOKEN)
