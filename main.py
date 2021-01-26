from discord.ext.commands import Bot, DefaultHelpCommand
from json import load
import os
from pathlib import Path

def load_config(file_name):
    return load(open(file_name))


cwd = Path(__file__).parents[0]
cwd = str(cwd)

config = load_config("config.json")

bot = Bot(
    command_prefix=config["prefix"],
    case_insensitive=True,
    help_command=DefaultHelpCommand(),
    owner_ids=config["owner"],
    description="A Python music bot"
)

bot.config = config

@bot.event
async def on_ready():
    print(f"{bot.user.name}#{bot.user.discriminator} is ready!")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    await bot.process_commands(message)


if __name__ == "__main__":
  for file in os.listdir(cwd + "\cogs"):
    if not file.startswith("_"):
      bot.load_extension(f"cogs.{file[:-3]}")

  bot.run(config["token"])

