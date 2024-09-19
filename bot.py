import discord
from discord.ext import commands
from flask import Flask, jsonify, request
import asyncio
import os
import requests  # Library to make API calls
import threading

# Bot Discord setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Flask setup for API
app = Flask(__name__)

# Variables for playback
current_track = None
loop = False

# GitHub API endpoint for music files
GITHUB_API_URL = "https://api.github.com/repos/Discode-Studio/AudioSource/contents/music"

# Supported file types
SUPPORTED_FILE_TYPES = ['.mp3', '.ogg', '.wav']

# Function to get music files from GitHub repository
def fetch_tracks_from_github():
    response = requests.get(GITHUB_API_URL)
    if response.status_code == 200:
        data = response.json()
        tracks = []
        for item in data:
            if any(item['name'].endswith(ext) for ext in SUPPORTED_FILE_TYPES):
                tracks.append(item['download_url'])  # Get the direct download URL for the file
        return tracks
    else:
        return []

# Function to update available tracks
available_tracks = fetch_tracks_from_github()

# API route to get list of tracks
@app.route('/tracks', methods=['GET'])
def get_tracks():
    global available_tracks
    # Fetch updated list from GitHub each time (or could cache for performance)
    available_tracks = fetch_tracks_from_github()
    return jsonify({'tracks': available_tracks, 'current_track': current_track, 'loop': loop})

# API route to play a track
@app.route('/play', methods=['POST'])
def play_track():
    global current_track
    track = request.json.get('track')
    if track in available_tracks:
        current_track = track
        # Trigger the bot to play the track
        asyncio.run_coroutine_threadsafe(play_audio(track), bot.loop)
        return jsonify({'message': f'Playing {track}'})
    return jsonify({'error': 'Track not found'}), 404

# API route to stop playing
@app.route('/stop', methods=['POST'])
def stop_track():
    asyncio.run_coroutine_threadsafe(stop_audio(), bot.loop)
    return jsonify({'message': 'Playback stopped'})

# API route to toggle loop
@app.route('/loop', methods=['POST'])
def toggle_loop():
    global loop
    loop = not loop
    return jsonify({'message': 'Looping is now {}'.format('on' if loop else 'off')})

# Bot commands to play and stop audio
async def play_audio(track_url):
    voice_channel = discord.utils.get(bot.guilds[0].voice_channels, name="On demand music")
    if not voice_channel:
        voice_channel = await bot.guilds[0].create_voice_channel("On demand music")
    vc = await voice_channel.connect()

    # Logic to play the audio from URL (example)
    source = discord.FFmpegPCMAudio(track_url)
    vc.play(source)

async def stop_audio():
    for vc in bot.voice_clients:
        if vc.is_playing():
            vc.stop()

# Running Flask and Bot together
def run_api():
    app.run(host='0.0.0.0', port=5000)

if __name__ == "__main__":
    # Running the Flask API in a separate thread so the bot can run simultaneously
    api_thread = threading.Thread(target=run_api)
    api_thread.start()

    # Running the bot
    bot.run(os.getenv('DISCORD_BOT_TOKEN'))
