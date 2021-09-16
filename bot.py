import discord
from discord.ext import commands, tasks
from discord_components import Button, Select, SelectOption, ComponentsBot
import youtube_dl
import datetime
import asyncio
import requests
from urllib.parse import urlparse
import os

DISCORD_TOKEN = os.environ.get("discord")
CLIENT_ID = os.environ.get("client")
CLIENT_SECRET = os.environ.get("secret")
AUTH_URL = 'https://accounts.spotify.com/api/token'

auth_response = requests.post(AUTH_URL, {
    'grant_type': 'client_credentials',
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
})

auth_response_data = auth_response.json()

access_token = auth_response_data['access_token']

client = discord.Client()
bot = ComponentsBot(command_prefix = "@", activity=discord.Activity(type=discord.ActivityType.listening, name="@help ❤️"), help_command=None)

queue = []
current = {}
VERSION = "v0.1"
FOOTER = "https://i.imgur.com/n1guxrV.png"

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'audioformat': 'mp3',
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' 
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.thumbnail = data.get('thumbnail')
        self.duration = self.parse_duration(int(data.get('duration')))
        self.url = ""

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]

        filename = data['title'] if stream else ytdl.prepare_filename(data)
        track = data['title']
        thumbnail = data['thumbnail']
        duration = data['duration']
        
        return (filename, track, thumbnail, duration)
    
def create_embed(description, title="RiRa", footer=f"RiRa {VERSION}", thumbnail="https://i.imgur.com/n1guxrV.png"):
    embed = discord.Embed(title=title, description=description, color=discord.Color.red())
    embed.set_thumbnail(url=thumbnail)
    embed.set_footer(text=footer, icon_url=FOOTER)
    
    return embed
    
def convert(n):
    return str(datetime.timedelta(seconds = n)) 

def playlist(url):
    try:
        headers = {
            'Authorization': f"Bearer {access_token}"
        }

        track_id = urlparse(url).path[10::]

        REQUEST_URL = f"https://api.spotify.com/v1/playlists/{track_id}/tracks"
        IMAGE_URL = f"https://api.spotify.com/v1/playlists/{track_id}/images"

        data = requests.get(REQUEST_URL, headers=headers)
        data = data.json()
        items = data["items"]
        
        tracks = []
        
        for i in items:
            tracks.append(i["track"]["name"] + " - " + i["track"]["album"]["artists"][0]["name"])
            
        data = requests.get(IMAGE_URL, headers=headers)
        data = data.json()
        images = data[0]["url"]
            
        return (tracks, images)
        
    except Exception as e:
        print(e)

def album(url):
    try:
        headers = {
            'Authorization': f"Bearer {access_token}"
        }

        album_id = urlparse(url).path[7::]

        REQUEST_URL = f"https://api.spotify.com/v1/tracks/{album_id}"

        data = requests.get(REQUEST_URL, headers=headers)
        data = data.json()
        
        record = data["name"] + " - " + data["album"]["artists"][0]["name"]
            
        return record
        
    except Exception as e:
        print(e)
    
@bot.command(name='disconnect', help='To make RiRa leave the voice channel', aliases=['dc'])
async def disconnect(ctx):
    global queue 
    
    try:
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_connected():
            await voice_client.disconnect()
            queue = []
        else:
            embed = create_embed("RiRa is not connected to a voice channel.")
            await ctx.send(embed=embed)
            
    except Exception as e:
        embed = create_embed("RiRa is not connected to a voice channel.")
        await ctx.send(embed=embed)
    
@bot.command(name='start', help='To make Rira start playing the music', aliases=['s'])
async def start(ctx):
    global queue
    global current
    
    try :
        server = ctx.message.guild
        voice_channel = server.voice_client
        
        voice_client = ctx.message.guild.voice_client
        
        async def pause_callback(interaction):
            await pause(ctx, interaction)

        async def resume_callback(interaction):
            await resume(ctx, interaction)

        async def skip_callback(interaction):
            await skip(ctx, interaction)     

        while(len(queue)!=0 and not voice_client.is_playing()):
            async with ctx.typing():
                filename, track, thumbnail, duration = await YTDLSource.from_url(queue[0], loop=bot.loop)
                voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename))
                
            current["track"] = track
            current["duration"] = duration
            current["request"] = ctx.author.name
            current["thumbnail"] = thumbnail

            embed = discord.Embed(title="RiRa", description="Now Playing", color=discord.Color.red())
            embed.add_field(name="Title", value=f"{track}", inline = False)
            embed.add_field(name="Duration", value=f"{convert(duration)}")
            embed.add_field(name="Requested by", value=f"{ctx.author.name}")
            embed.set_thumbnail(url=thumbnail)
            embed.set_footer(text=f"RiRa {VERSION}", icon_url=FOOTER)

            await ctx.send(embed=embed, components=[[
                        bot.components_manager.add_callback(Button(label="Pause", custom_id="pause", style=1), pause_callback),
                        bot.components_manager.add_callback(Button(label="Resume", custom_id="play", style=3), resume_callback),
                        bot.components_manager.add_callback(Button(label="Skip", custom_id="skip", style=4), skip_callback)]])

            del(queue[0])
            
    except Exception as e:
        embed = create_embed("Queue is empty.")
        await ctx.send(embed=embed)

@bot.command(name='pause', help='Pauses the music', aliases=['ps'])
async def pause(ctx, interaction=None):
    try:
        voice_client = ctx.message.guild.voice_client
        if voice_client.pause() is None and interaction is not None:
            embed = create_embed("Paused")
            await interaction.send(embed=embed)
        elif voice_client.is_playing():
            await voice_client.pause()
    except Exception as e:
        embed = create_embed("RiRa is not connected to a voice channel.")
        await ctx.send(embed=embed)
        
@bot.command(name='resume', help='Resumes the music', aliases=['rs'])
async def resume(ctx, interaction=None):
    try:
        voice_client = ctx.message.guild.voice_client
        if voice_client.resume() is None and interaction is not None:
            embed = create_embed("Resumed")
            await interaction.send(embed=embed)
        elif voice_client.is_paused():
            await voice_client.resume()
    except Exception as e:
        embed = create_embed("RiRa is not connected to a voice channel.")
        await ctx.send(embed=embed)

@bot.command(name='skip', help='Skips the music', aliases=['fs'])
async def skip(ctx, interaction=None):
    try:
        voice_client = ctx.message.guild.voice_client
        if voice_client.stop() is None and interaction is not None:
            embed = create_embed("Skipped")
            await interaction.send(embed=embed)
            await start(ctx)

        elif voice_client.is_playing():
            await voice_client.stop()
            await start(ctx)

        else:
            await start(ctx)
    except Exception as e:
        embed = create_embed("RiRa is not connected to a voice channel.")
        await ctx.send(embed=embed)
        
@bot.command(name='play', help='To play music', aliases=['p'])
async def play(ctx, *, url: str):
    global queue

    if url is not None:
        voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)

        if not ctx.message.author.voice:
            embed = create_embed(f"{ctx.message.author.name} is not connected to a voice channel")
            await ctx.send(embed=embed)
            return
        elif voice == None:
            channel = ctx.message.author.voice.channel
            await channel.connect()

        voice_client = ctx.guild.voice_client
        
        spotify = urlparse(url)
        
        if spotify.netloc == "open.spotify.com" and "playlist" in spotify.path:
            tracks, images = playlist(url)
            count = 0
            for i in tracks:
                count += 1
                queue.append(i)
                
            embed = discord.Embed(title="RiRa", description="Playlist Added", color=discord.Color.red())
            embed.add_field(name="Number of tracks", value=f"{count}", inline = False)
            embed.add_field(name="Requested by", value=f"{ctx.author.name}")
            embed.set_thumbnail(url=images)
            embed.set_footer(text=f"RiRa {VERSION}", icon_url=FOOTER)
            
            await ctx.send(embed=embed)
            await start(ctx)
            
        elif spotify.netloc == "open.spotify.com" and "track" in spotify.path:
            record = album(url)
            filename, track, thumbnail, duration = await YTDLSource.from_url(record, loop=bot.loop, stream=True)
            queue.append(track)
                
            embed = discord.Embed(title="RiRa", description="Added to Queue", color=discord.Color.red())
            embed.add_field(name="Title", value=f"{track}", inline = False)
            embed.add_field(name="Duration", value=f"{convert(duration)}")
            embed.add_field(name="Requested by", value=f"{ctx.author.name}")
            embed.set_thumbnail(url=thumbnail)
            embed.set_footer(text=f"RiRa {VERSION}", icon_url=FOOTER)
            
            await ctx.send(embed=embed)
            await start(ctx)
            
        else:
            if voice_client.is_playing():
                filename, track, thumbnail, duration = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
                queue.append(track)
                
                embed = discord.Embed(title="RiRa", description="Added to queue", color=discord.Color.red())
                embed.add_field(name="Title", value=f"{track}", inline = False)
                embed.add_field(name="Duration", value=f"{convert(duration)}")
                embed.add_field(name="Requested by", value=f"{ctx.author.name}")
                embed.set_thumbnail(url=thumbnail)
                embed.set_footer(text=f"RiRa {VERSION}", icon_url=FOOTER)

                await ctx.send(embed=embed)
            else:
                filename, track, thumbnail, duration = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
                queue.append(track)
            
                await start(ctx)
    else:
        embed = create_embed("Provide a song to be played.")
        await ctx.send(embed=embed)     
    
@bot.command(name='remove', help='Removes music from the queue', aliases=['r', 'del'])
async def remove(ctx, number=None):
    global queue
    try:
        if number is not None:
            del(queue[int(number)-1])
            await queue_(ctx)
        else:
            embed = create_embed("Provide an index to be removed")
            await ctx.send(embed=embed)
    except Exception as e:
        embed = create_embed("Queue is either **empty** or **invalid index**")
        await ctx.send(embed=embed)
        
@bot.command(name='queue', help='View the queue', aliases=['q', 'view'])
async def queue_(ctx, page=1):
    if (len(queue)!=0):
        pages = len(queue)//20
        if(page<=pages):
            message = ""

            for i in range((page-1)*20,((page-1)*20)+20):
                message += str(i+1) + ". " + queue[i] + "\n"

            embed = create_embed(message, "Coming Next", footer=f"Page {page}/{pages}")
            await ctx.send(embed=embed)
        else:
            embed = create_embed("Invalid page number")
            await ctx.send(embed=embed)
    else:
        embed = create_embed("Queue is empty")
        await ctx.send(embed=embed)
        
@bot.command(name='clear', help='Clears the queue', aliases=['c', 'cl'])
async def clear(ctx):
    global queue
    queue = []

    embed = create_embed("Queue is now empty")
    await ctx.send(embed=embed)
        
@bot.command(name='ping', help='Returns the latency', aliases=['pi'])
async def ping(ctx):
    embed = create_embed(f"**Pong!** Latency: {round(bot.latency * 1000)} ms")
    await ctx.send(embed=embed)
    
@bot.command(name='np', help='Shows currently playing music')
async def np(ctx):
    try:
        global current

        voice_client = ctx.guild.voice_client
        if voice_client.is_playing():
            embed = discord.Embed(title="RiRa", description="Now Playing", color=discord.Color.red())
            embed.add_field(name="Title", value=f"{current['track']}", inline = False)
            embed.add_field(name="Duration", value=f"{convert(current['duration'])}")
            embed.add_field(name="Requested by", value=f"{current['request']}")
            embed.set_thumbnail(url=current["thumbnail"])
            embed.set_footer(text=f"RiRa {VERSION}", icon_url=FOOTER)
            await ctx.send(embed=embed)

        else:
            embed = create_embed("RiRa is not playing any music")
            await ctx.send(embed=embed)
            
    except Exception as e:
        embed = create_embed("RiRa is not playing any music")
        await ctx.send(embed=embed)
        
@bot.command(name='credits', help='Returns the credits', aliases=['cr'])
async def credits(ctx):
    embed = create_embed(f"Developed by **Earthing**")
    await ctx.send(embed=embed)
    await ctx.send(f"GitHub: https://github.com/apratimshukla6")
    
@bot.command(name='help', help='Returns RiRa help')
async def help(context):
    embed = discord.Embed(title="RiRa", description="List of RiRa commands", color=discord.Color.red())
    embed.add_field(name=f"**@play**", value=f'> Alias: @p\n> Task: To play music\n> Example: @p songname',inline=False)
    embed.add_field(name=f"**@np**", value=f'> Alias: @np\n> Task: Shows currently playing music\n> Example: @np',inline=False)
    embed.add_field(name=f"**@queue**", value=f'> Alias: @q, @view\n> Task: View the queue\n> Example: @q, @q 2',inline=False)
    embed.add_field(name=f"**@remove**", value=f'> Alias: @r, @del\n> Task: Removes music from the queue\n> Example: @r 1',inline=False)
    embed.add_field(name=f"**@clear**", value=f'> Alias: @c, @cl\n> Task: Clears the queue\n> Example: @c',inline=False)
    embed.add_field(name=f"**@pause**", value=f'> Alias: @ps\n> Task: Pauses the music\n> Example: @ps',inline=False)
    embed.add_field(name=f"**@resume**", value=f'> Alias: @rs\n> Task: Resumes the music\n> Example: @rs',inline=False)
    embed.add_field(name=f"**@skip**", value=f'> Alias: @fs\n> Task: Skips the music\n> Example: @fs',inline=False)
    embed.add_field(name=f"**@disconnect**", value=f'> Alias: @dc\n> Task: To make RiRa leave the voice channel\n> Example: @dc',inline=False)
    embed.add_field(name=f"**@ping**", value=f'> Alias: @pi\n> Task: Returns the latency\n> Example: @pi',inline=False)
    embed.add_field(name=f"**@credits**", value=f'> Alias: @cr\n> Task: Returns the credits\n> Example: @cr',inline=False)
    embed.set_thumbnail(url=FOOTER)
    embed.set_footer(text=f"RiRa {VERSION}", icon_url=FOOTER)
    await context.send(embed=embed)
        
# Events
@bot.event
async def on_ready():
    print(f"RiRa {VERSION}")
    
bot.run(DISCORD_TOKEN)

