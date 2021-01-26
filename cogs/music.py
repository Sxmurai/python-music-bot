from discord.ext import commands
import lavalink
import discord
import re

# URL regex
url_regex = re.compile(r'https?://(?:www\.)?.+')

class Music(commands.Cog):
  def __init__(self, bot):
    # set the bot property
    self.bot = bot

    # get the lavalink specific config
    lavalink_config = bot.config["lavalink"]

    # connect to lavalink
    if not hasattr(bot, "music"):
      # make a new instance
      bot.music = lavalink.Client(755613660822372393)

      # add the node
      bot.music.add_node(
        lavalink_config["host"],
        lavalink_config["port"],
        lavalink_config["password"],
        lavalink_config["region"],
        lavalink_config["name"],
      )
      
      # add voice handler event shit
      bot.add_listener(bot.music.voice_update_handler, "on_socket_response")

    lavalink.add_event_hook(self.lavalink_events)

  # lavalink events
  async def lavalink_events(self, event):
    if isinstance(event, lavalink.QueueEndEvent):
      player = event.player

      channel = self.bot.get_channel(player._user_data["channel"])

      if channel is None:
        return

      await channel.send(
        embed=discord.Embed(
          color=discord.Color.blurple(),
          description="Queue has finished, I'll be leaving now."
        )
      )

      # disconnect
      await self.connect(int(player.guild_id), None)

    elif isinstance(event, lavalink.TrackStartEvent):
      player = event.player

      channel = self.bot.get_channel(player._user_data["channel"])

      if channel is None:
        return

      track = event.track

      await channel.send(
        embed=discord.Embed(
          color=discord.Color.blurple(),
          title="Now Playing",
          url=track.uri,
          description=f"[{track.title}]({track.uri})"
        ).set_thumbnail(url=f'https://i.ytimg.com/vi/{track.identifier}/hqdefault.jpg')
      )
    
    elif isinstance(event, lavalink.NodeConnectedEvent):
      node = event.node
      print(f"Node {node.name} was connected.")

  # cog events
  async def cog_after_invoke(self, ctx):
    print(f"{ctx.author.name}#{ctx.author.discriminator} [{ctx.author.id}] ran the {ctx.command.name} command.")

  async def cog_before_invoke(self, ctx):
    guild = ctx.guild is not None

    if guild:
      await self.ensure_voice(ctx)

    return guild

  async def cog_command_error(self, ctx, error):
    if isinstance(error, commands.CommandInvokeError):
      await ctx.send(
        embed=discord.Embed(
          color=discord.Color.red(),
          description=error.original
        )
      )
    else:
      await ctx.send(
        embed=discord.Embed(
          color=discord.Color.red(),
          description=str(error)
        )
      )

  # functions
  async def ensure_voice(self, ctx):
    player = self.bot.music.player_manager.create(ctx.guild.id, endpoint=str(ctx.guild.region))

    # if the command isnt named "play", skip past it
    should_connect = ctx.command.name in ("play")

    if not ctx.author.voice or not ctx.author.voice.channel:
      raise commands.CommandInvokeError("Please join a voice channel")

    if not player.is_connected:
      if not should_connect:
        raise commands.CommandInvokeError("Not connected.")

      permissions = ctx.author.voice.channel.permissions_for(ctx.me)

      if not permissions.connect or not permissions.speak:
        raise commands.CommandInvokeError("I need both the Connect and Speak permissions to do that.")

      player.store("channel", ctx.channel.id)
      await self.connect(ctx.guild.id, str(ctx.author.voice.channel.id))
    else:
      if int(player.channel_id) != ctx.author.voice.channel.id:
        raise commands.CommandInvokeError("Please join my voice channel.")

  async def connect(self, guild_id: int, voice_channel_id):
    ws = self.bot._connection._get_websocket(guild_id)
    await ws.voice_state(str(guild_id), voice_channel_id)

  # commands
  @commands.command(aliases=["p", "pp"], description="Plays music in your voice channel.")
  @commands.guild_only()
  async def play(self, ctx, *, query: str):
    if query is None:
      return await ctx.send("Please provide a search query")

    # if the user provides a link like <http://link.com> it'll remove the <> to then give us the url we need
    query = query.strip("<>")

    # get the player from the players registry
    player = self.bot.music.player_manager.get(ctx.guild.id)

    # if query is not a URL
    if not url_regex.match(query):
      # search with YouTube, as YouTube playlist links cannot be used with ytsearch:
      query = f"ytsearch:{query}" 

    # load results with identifier provided
    results = await player.node.get_tracks(query)

    # if theres no results, or if theres no tracks
    if not results or not results["tracks"]:
      # tell the user nothing was found for their search
      return await ctx.send("No tracks found for search query. Try again?")

    embed = discord.Embed(color=discord.Color.blurple(), title="Enqueued")

    # if a playlist was resolved,
    if results["loadType"] == "PLAYLIST_LOADED":
      # the tracks
      tracks = results["tracks"]

      # loop through each track in the result, and load them all
      for track in results["tracks"]:
        # add the track to the queue
        player.add(requester = ctx.author.id, track = track)

      embed.description = f'Enqueued Playlist with **{len(tracks)}** songs'
      embed.set_thumbnail(url=f'https://i.ytimg.com/vi/{tracks[0]["identifier"]}/hqdefault.jpg')

      # tell them they queued up a playlist
      await ctx.send(embed=embed)
    
    # if a playlist wasnt loaded, enqueue the first track
    else:
      # define a var
      track = results["tracks"][0]

      # add the track to queue
      player.add(requester=ctx.author.id, track=track)

      embed.url = track["info"]["uri"]
      embed.description = f'Enqueued Track: [{track["info"]["title"]}]({track["info"]["uri"]})'
      embed.set_thumbnail(url=f'https://i.ytimg.com/vi/{track["info"]["identifier"]}/hqdefault.jpg')

      # tell them they queued up a track
      await ctx.send(embed=embed)

    # if we are not playing anything, play the track
    if not player.is_playing:
      await player.play()

def setup(bot):
    bot.add_cog(Music(bot))