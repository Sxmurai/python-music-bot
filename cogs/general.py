from discord.ext import commands
import discord

class General(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  # cog events
  async def cog_after_invoke(self, ctx):
    print(f"{ctx.author.name}#{ctx.author.discriminator} [{ctx.author.id}] ran the {ctx.command.name} command.")

  # commands
  @commands.command(aliases=["pong", "latency"], description="Displays the latency of the bot")
  async def ping(self, ctx):
    await ctx.send(
      embed=discord.Embed(
        color=discord.Color.blurple(),
        description=f"💓 Gateway: **{round(self.bot.latency * 1000)}ms**"
      )
    )
    
def setup(bot):
    bot.add_cog(General(bot))