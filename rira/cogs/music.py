from discord.ext import commands
import discord
import asyncio
import youtube_dl
import logging
import math
from urllib import request
from urllib.parse import urlparse
import requests
from ..video import Video

FFMPEG_BEFORE_OPTS = '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'

async def audio_playing(ctx):
    client = ctx.guild.voice_client
    if client and client.channel and client.source:
        return True
    else:
        raise commands.CommandError("Not currently playing any audio.")

async def in_voice_channel(ctx):
    voice = ctx.author.voice
    bot_voice = ctx.guild.voice_client
    if voice and bot_voice and voice.channel and bot_voice.channel and voice.channel == bot_voice.channel:
        return True
    else:
        raise commands.CommandError("You need to be in the channel to do that.")

async def is_audio_requester(ctx):
    music = ctx.bot.get_cog("Music")
    state = music.get_state(ctx.guild)
    permissions = ctx.channel.permissions_for(ctx.author)
    if permissions.administrator or state.is_requester(ctx.author):
        return True
    else:
        raise commands.CommandError("You need to be the song requester to do that.")

class Music(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config[__name__.split(".")[-1]]
        self.states = {}
        self.access_token = None

    def get_state(self, guild):
        if guild.id in self.states:
            return self.states[guild.id]
        else:
            self.states[guild.id] = GuildState()
            return self.states[guild.id]
        
    def playlist(self, url):
        self.access_token = requests.post("https://accounts.spotify.com/api/token", {
            'grant_type': 'client_credentials',
            'client_id': self.config["client"],
            'client_secret': self.config["secret"],
        }).json()["access_token"]
        headers = {'Authorization': f"Bearer {self.access_token}"}
        track_id = urlparse(url).path[10::]
        REQUEST_URL = f"https://api.spotify.com/v1/playlists/{track_id}/tracks"
        data = requests.get(REQUEST_URL, headers=headers)
        data = data.json()
        items = data["items"]
        url = []
        for i in items:
            url.append(i["track"]["name"] + " - " + i["track"]["album"]["artists"][0]["name"])

        return (url)

    def album(self, url):
        self.access_token = requests.post("https://accounts.spotify.com/api/token", {
            'grant_type': 'client_credentials',
            'client_id': self.config["client"],
            'client_secret': self.config["secret"],
        }).json()["access_token"]
        headers = {'Authorization': f"Bearer {self.access_token}"}
        album_id = urlparse(url).path[7::]
        REQUEST_URL = f"https://api.spotify.com/v1/tracks/{album_id}"
        data = requests.get(REQUEST_URL, headers=headers)
        data = data.json()
        url = data["name"] + " - " + data["album"]["artists"][0]["name"]

        return url
    
    def create_embed(self, description, title="RiRa", footer=f"RiRa v0.1", thumbnail="https://i.imgur.com/n1guxrV.png"):
        embed = discord.Embed(title=title, description=description, color=discord.Color.red())
        embed.set_thumbnail(url=thumbnail)
        embed.set_footer(text=footer, icon_url=thumbnail)

        return embed

    @commands.command(aliases=["dc", "leave"])
    @commands.guild_only()
    async def disconnect(self, ctx):
        client = ctx.guild.voice_client
        state = self.get_state(ctx.guild)
        if client and client.channel:
            await client.disconnect()
            state.playlist = []
            state.now_playing = None
        else:
            raise commands.CommandError("Not in a voice channel.")

    @commands.command(aliases=["resume", "ps", "rs"])
    @commands.guild_only()
    @commands.check(audio_playing)
    @commands.check(in_voice_channel)
    @commands.check(is_audio_requester)
    @commands.has_any_role("DJ")
    async def pause(self, ctx):
        client = ctx.guild.voice_client
        self._pause_audio(client)

    def _pause_audio(self, client):
        if client.is_paused():
            client.resume()
        else:
            client.pause()

    @commands.command(aliases=["vol", "v"])
    @commands.guild_only()
    @commands.check(audio_playing)
    @commands.check(in_voice_channel)
    @commands.check(is_audio_requester)
    @commands.has_any_role("DJ")
    async def volume(self, ctx, volume: int):
        state = self.get_state(ctx.guild)
        if volume < 0:
            volume = 0

        max_vol = self.config["max_volume"]
        if max_vol > -1: 
            if volume > max_vol:
                volume = max_vol

        client = ctx.guild.voice_client
        state.volume = float(volume) / 100.0
        client.source.volume = state.volume  

    @commands.command(aliases=["fs"])
    @commands.guild_only()
    @commands.check(audio_playing)
    @commands.check(in_voice_channel)
    async def skip(self, ctx):
        state = self.get_state(ctx.guild)
        client = ctx.guild.voice_client
        if ctx.channel.permissions_for(ctx.author).administrator or state.is_requester(ctx.author):
            client.stop()
        elif self.config["vote_skip"]:
            channel = client.channel
            self._vote_skip(channel, ctx.author)
            users_in_channel = len([member for member in channel.members if not member.bot])
            required_votes = 3
            await ctx.send(f"{ctx.author.mention} voted to skip ({len(state.skip_votes)}/{required_votes} votes)")
        else:
            raise commands.CommandError("Vote skipping is disabled.")

    def _vote_skip(self, channel, member):
        logging.info(f"{member.name} votes to skip")
        state = self.get_state(channel.guild)
        state.skip_votes.add(member)

        if ((len(state.skip_votes))==3):
            logging.info(f"Enough votes, skipping.")
            channel.guild.voice_client.stop()

    def _play_song(self, client, state, song):
        state.now_playing = song
        state.skip_votes = set()
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(song.stream_url, before_options=FFMPEG_BEFORE_OPTS), volume=state.volume)

        def after_playing(err):
            if len(state.playlist) > 0:
                next_song = state.playlist.pop(0)
                self._play_song(client, state, next_song)
            else:
                asyncio.run_coroutine_threadsafe(client.disconnect(), self.bot.loop)

        client.play(source, after=after_playing)

    @commands.command(aliases=["np", "current"])
    @commands.guild_only()
    @commands.check(audio_playing)
    async def nowplaying(self, ctx):
        state = self.get_state(ctx.guild)
        message = await ctx.send("", embed=state.now_playing.get_embed())

    @commands.command(aliases=["q", "view"])
    @commands.guild_only()
    @commands.check(audio_playing)
    async def queue(self, ctx):
        state = self.get_state(ctx.guild)
        await ctx.send(embed=self.create_embed(self._queue_text(state.playlist)))

    def _queue_text(self, queue):
        if len(queue) > 0:
            message = [f"> {len(queue)} songs in queue"]
            message += [
                f"  {index+1}. **{song.title}** (requested by **{song.requested_by.name}**)"
                for (index, song) in enumerate(queue)
            ]
            return "\n".join(message)
        else:
            return "The play queue is empty."

    @commands.command(aliases=["c", "cq"])
    @commands.guild_only()
    @commands.check(audio_playing)
    @commands.has_permissions(administrator=True)
    async def clear(self, ctx):
        state = self.get_state(ctx.guild)
        state.playlist = []
        await ctx.send(embed=self.create_embed("Cleared queue."))

    @commands.command(aliases=["r", "del"])
    @commands.guild_only()
    @commands.check(audio_playing)
    @commands.has_any_role("DJ")
    async def remove(self, ctx, song: int):
        state = self.get_state(ctx.guild)
        if 1 <= song <= len(state.playlist):
            song = state.playlist.pop(song - 1)  

            await ctx.send(embed=self.create_embed(self._queue_text(state.playlist)))
        else:
            raise commands.CommandError("You must use a valid index.")

    @commands.command(aliases=["p"])
    @commands.guild_only()
    async def play(self, ctx, *, url):
        client = ctx.guild.voice_client
        state = self.get_state(ctx.guild)

        if client and client.channel:
            try:
                voice_client = ctx.guild.voice_client
                spotify = urlparse(url)
                
                if spotify.netloc == "open.spotify.com" and "track" in spotify.path:
                    url = self.album(url)
                # Spotify playlist feature coming soon
                elif spotify.netloc == "open.spotify.com" and "playlist" in spotify.path:
                    url = self.playlist(url)[0]
                    
                video = Video(url, ctx.author)
                    
            except youtube_dl.DownloadError as e:
                logging.warn(f"Downloading error: {e}")
                await ctx.send("There was an error downloading your video, sorry.")
                return
            state.playlist.append(video)
            inform = await ctx.send(embed=self.create_embed("Added to queue."))
            message = await ctx.send(embed=video.get_embed())
            
        else:
            if ctx.author.voice is not None and ctx.author.voice.channel is not None:
                channel = ctx.author.voice.channel
                try:
                    spotify = urlparse(url)
                
                    if spotify.netloc == "open.spotify.com" and "track" in spotify.path:
                        url = self.album(url)
                    # Spotify playlist feature coming soon
                    elif spotify.netloc == "open.spotify.com" and "playlist" in spotify.path:
                        url = self.playlist(url)[0]
                        
                    video = Video(url, ctx.author)
                except youtube_dl.DownloadError as e:
                    await ctx.send("There was an error downloading your video, sorry.")
                    return
                client = await channel.connect()
                self._play_song(client, state, video)
                message = await ctx.send("", embed=video.get_embed())
                logging.info(f"Now playing '{video.title}'")
            else:
                raise commands.CommandError("You need to be in a voice channel to do that.")
                
    @commands.command(aliases=["pi"])
    @commands.guild_only()
    async def ping(self, ctx):
        await ctx.send(embed=self.create_embed(f"**Pong!** Latency: {round(self.bot.latency * 1000)} ms"))
                
    @commands.command(aliases=["cr"])
    @commands.guild_only()
    async def credits(self, ctx):
        await ctx.send(embed=self.create_embed(f"Developed by **Earthing**"))
        await ctx.send(f"GitHub: https://github.com/apratimshukla6")
                
    @commands.command(aliases=["h"])
    @commands.guild_only()
    async def help(self, ctx):
        embed = discord.Embed(title="RiRa", description="List of RiRa commands", color=discord.Color.red())
        embed.add_field(name=f"**!play**", value=f'> Alias: !p\n> Task: To play music\n> Example: !p songname',inline=False)
        embed.add_field(name=f"**!nowplaying**", value=f'> Alias: !np, !current\n> Task: Shows currently playing music\n> Example: !np',inline=False)
        embed.add_field(name=f"**!queue**", value=f'> Alias: !q, !view\n> Task: View the queue\n> Example: !q',inline=False)
        embed.add_field(name=f"**!remove**", value=f'> Alias: !r, !del\n> Task: Removes music from the queue\n> Example: !r 1',inline=False)
        embed.add_field(name=f"**!clear**", value=f'> Alias: !c, !cq\n> Task: Clears the queue\n> Example: !c',inline=False)
        embed.add_field(name=f"**!pause**", value=f'> Alias: !ps\n> Task: Pauses the music\n> Example: !ps',inline=False)
        embed.add_field(name=f"**!resume**", value=f'> Alias: !rs\n> Task: Resumes the music\n> Example: !rs',inline=False)
        embed.add_field(name=f"**!skip**", value=f'> Alias: !fs\n> Task: Skips the music\n> Example: !fs',inline=False)
        embed.add_field(name=f"**!disconnect**", value=f'> Alias: !dc, !leave\n> Task: To make RiRa leave the voice channel\n> Example: !dc',inline=False)
        embed.add_field(name=f"**!volume**", value=f'> Alias: !v, !vol\n> Task: To change the volume\n> Example: !v 250',inline=False)
        embed.add_field(name=f"**!ping**", value=f'> Alias: !pi\n> Task: Returns the latency\n> Example: !pi',inline=False)
        embed.add_field(name=f"**!credits**", value=f'> Alias: !cr\n> Task: Returns the credits\n> Example: !cr',inline=False)
        embed.set_thumbnail(url="https://i.imgur.com/n1guxrV.png")
        embed.set_footer(text=f"RiRa v0.1", icon_url="https://i.imgur.com/n1guxrV.png")
        await ctx.send(embed=embed)

class GuildState:
    def __init__(self):
        self.volume = 1.0
        self.playlist = []
        self.skip_votes = set()
        self.now_playing = None

    def is_requester(self, user):
        return self.now_playing.requested_by == user
