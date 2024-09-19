import discord
from discord.ext import commands
import os
import asyncio
import aiohttp
from discord import FFmpegPCMAudio
from io import BytesIO

# Configuration du bot Discord
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Variables globales
github_repo_url = 'https://api.github.com/repos/Discode-Studio/AudioSource/contents/music'  # Remplace par l'URL API de ton repo GitHub
supported_formats = ['mp3', 'wav', 'ogg']  # Formats pris en charge

# Fonction pour obtenir la liste des fichiers audio du repository GitHub
async def get_audio_files():
    async with aiohttp.ClientSession() as session:
        async with session.get(github_repo_url) as response:
            if response.status == 200:
                files = await response.json()
                audio_files = [file['download_url'] for file in files if file['name'].split('.')[-1] in supported_formats]
                return audio_files
            else:
                print(f"Erreur lors de l'accès au repo: {response.status}")
                return []

# Fonction pour jouer un fichier audio
async def play_audio(vc, url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    audio_data = BytesIO(await response.read())
                    vc.play(FFmpegPCMAudio(audio_data, pipe=True))
                    while vc.is_playing():
                        await asyncio.sleep(1)
                else:
                    print(f"Erreur lors du téléchargement de l'audio: {response.status}")
    except Exception as e:
        print(f"Erreur pendant la lecture de l'audio: {e}")

# Event on_ready pour afficher que le bot est prêt et rejoindre le canal vocal automatiquement
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

    # Parcourir tous les serveurs auxquels le bot est connecté
    for guild in bot.guilds:
        # Vérifier si un salon vocal "On demand music" existe
        voice_channel = discord.utils.get(guild.voice_channels, name="On demand music")
        
        if voice_channel:
            vc = await voice_channel.connect()
        else:
            # Créer le canal vocal s'il n'existe pas
            voice_channel = await guild.create_voice_channel("On demand music")
            vc = await voice_channel.connect()

        # Boucle principale pour jouer les fichiers audio du repo
        while True:
            audio_files = await get_audio_files()
            
            if audio_files:
                for audio_url in audio_files:
                    if not vc.is_playing():
                        await play_audio(vc, audio_url)
            else:
                print("Aucun fichier audio disponible.")
            
            await asyncio.sleep(10)  # Attendre 10 secondes avant de recommencer le cycle

# Le token est récupéré depuis une variable d'environnement
bot.run(os.getenv('DISCORD_BOT_TOKEN'))
