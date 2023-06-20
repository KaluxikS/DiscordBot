import discord
from discord.ext import tasks, commands
import asyncio
import datetime
from youtube_search import YoutubeSearch
import pytube
from collections import deque
import methods as m


intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.messages = True
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='$', intents=intents)

ffmpeg_path = 'sciezka do ffmpeg'

queue = deque()
isplaying = False
stop = False
current_playing = None
current_loop = m.read_current_loop()


async def play_next():
    global queue, isplaying, current_playing  # Dodajemy flagi do zakresu globalnego

    # Pobieranie kolejnego utworu z kolejki
    if queue:
        file_path, ctx = queue.popleft()
        file_name = file_path.replace('temp/', '').replace('.mp4', '')

        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        voice_client.play(discord.FFmpegPCMAudio(file_path),
                          after=lambda e: asyncio.run_coroutine_threadsafe(play_next(), bot.loop))

        isplaying = True  # Ustawienie flagi isplaying na True
        current_playing = file_name
        await ctx.send('Leci nutka!')


@bot.event
async def on_ready():
    print('Bot is ready')
    await m.send_initial_message(bot)
    send_daily_message.start()
    await m.clear_temp_folder()


@tasks.loop(hours=24)
async def send_daily_message():
    global current_loop
    guild_id = "id serwera"
    member_id = "id uzytkownika"
    channel_id = "id kanalu"
    guild = bot.get_guild(guild_id)
    channel = bot.get_channel(channel_id)
    print("wywolanie")
    if guild:
        member = await guild.fetch_member(member_id)

        if member:
            message = f"Dzień {current_loop}. 😄\nDoleś <@{member_id}> jest na serwerze! 🎉"
        else:
            message = "Dolesa nie ma na serwerze!."
    else:
        print("Nie można odnaleźć serwera o podanym ID.")

    await channel.send(message)

    # Zapisanie nowej wartości current_loop do pliku dzien.txt
    m.write_current_loop(current_loop + 1)


@send_daily_message.before_loop
async def before_send_daily_message():
    await bot.wait_until_ready()
    now = datetime.datetime.now()
    target_time = datetime.time(1, 1, 0)  # Ustawienie docelowej godziny na 01:00
    delta = datetime.timedelta(
        hours=target_time.hour - now.hour,
        minutes=target_time.minute - now.minute,
        seconds=target_time.second - now.second
    )
    if delta.total_seconds() < 0:
        delta += datetime.timedelta(
            days=1)  # Jeśli docelowa godzina już minęła, następne uruchomienie będzie następnego dnia o 01:00
    await asyncio.sleep(delta.total_seconds())


@bot.command()
async def doles(ctx, *, arg):
    await ctx.send("Doles mowi: " + arg)


@bot.command()
async def play(ctx, *query):
    global isplaying, stop  # Dodajemy flagi do zakresu globalnego

    search_query = ' '.join(query)  # Łączenie słów w zapytaniu wyszukiwania

    results = YoutubeSearch(search_query, max_results=1).to_dict()
    video_url = "https://www.youtube.com" + results[0]["url_suffix"]

    video = pytube.YouTube(video_url)
    audio_stream = video.streams.filter(only_audio=True).first()

    voice_channel = ctx.author.voice.channel

    # Sprawdzenie, czy bot już jest na kanale użytkownika
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_connected():
        # Jeśli bot jest już na kanale, przełącz się na nowy kanał
        await voice_client.move_to(voice_channel)
    else:
        # Jeśli bot nie jest jeszcze na kanale, dołącz do niego
        voice_client = await voice_channel.connect()

    audio_stream.download(output_path='temp')

    # Dodawanie utworu do kolejki
    queue.append(('temp/' + audio_stream.default_filename, ctx))

    if not isplaying:  # Sprawdzenie flagi isplaying
        # Jeśli nie jest odtwarzany żaden utwór, rozpocznij odtwarzanie
        await play_next()


@bot.command()
async def skip(ctx):
    global isplaying
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await ctx.send('Pomijam bieżący utwór.')
        isplaying = False
        await play_next()
    else:
        await ctx.send('Nie ma żadnego utworu do pominięcia.')


@bot.command()
async def stop(ctx):
    global isplaying, stop  # Dodajemy flagi do zakresu globalnego

    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client.is_playing():
        voice_client.stop()
        isplaying = False  # Ustawienie flagi isplaying na False
        stop = True  # Ustawienie flagi stop na True
        await ctx.send('Zatrzymałem odtwarzanie.')


@bot.command()
async def resume(ctx):
    global isplaying, stop  # Dodajemy flagi do zakresu globalnego

    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_paused() and stop:
        voice_client.resume()
        isplaying = True  # Ustawienie flagi isplaying na True
        stop = False  # Ustawienie flagi stop na False
        await ctx.send('Wznawiam odtwarzanie.')


@bot.command()
async def disconnect(ctx):
    global isplaying, stop  # Dodajemy flagi do zakresu globalnego

    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client.is_connected():
        await voice_client.disconnect()
        isplaying = False  # Ustawienie flagi isplaying na False
        stop = False  # Ustawienie flagi stop na False
        await ctx.send('Odłączyłem się od kanału głosowego.')


@bot.command()
async def clear(ctx):
    global queue
    queue.clear()
    await ctx.send('Kolejka utworów została wyczyszczona.')


@bot.command()
async def summon(ctx):
    voice_channel = ctx.author.voice.channel

    # Sprawdzenie, czy bot już jest na kanale użytkownika
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_connected():
        # Jeśli bot jest już na kanale, przełącz się na nowy kanał
        await voice_client.move_to(voice_channel)
    else:
        # Jeśli bot nie jest jeszcze na kanale, dołącz do niego
        voice_client = await voice_channel.connect()

    await ctx.send(f'Przywołano bota na kanał: {voice_channel}')


@bot.command(aliases=['np'])
async def now_playing(ctx):
    global current_playing
    if current_playing:
        await ctx.send(f"Aktualnie odtwarzana piosenka: {current_playing} ")
    else:
        await ctx.send("Nie jest odtwarzana żadna piosenka.")


@bot.command()
async def helpme(ctx):
    help_message = """
    **Dostępne komendy:**
    - `$play [link youtube/wyszukiwanie na youtube]`: Odtwarza utwór z YouTube na kanale głosowym, dodając go do kolejki.
    - `$skip`: Pomija bieżący odtwarzany utwór i przechodzi do następnego w kolejce.
    - `$disconnect`: Odłącza bota od aktualnego kanału głosowego.
    - `$clear`: Czyści kolejkę utworów.
    - `$summon`: Przywołuje bota na aktualny kanał głosowy.
    - `$np`: Wyswietla informacje o aktualnej nutce.
    """
    await ctx.send(help_message)


bot.run('token bota')
