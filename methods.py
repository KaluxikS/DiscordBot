import shutil
from pathlib import Path


# Czyszczenie pliku temp
async def clear_temp_folder():
    folder_path = 'temp'
    shutil.rmtree(folder_path)
    print(f"Cleared '{folder_path}' folder.")


# Odczytanie wartości current_loop z pliku dzien.txt
def read_current_loop():
    file_path = Path("dzien.txt")
    if file_path.exists():
        with open(file_path, "r") as file:
            current_loop = int(file.read())
            print("zczytano plik")
    else:
        print("Blad zczytywania pliku!")
    return current_loop


# Zapisanie wartości current_loop do pliku dzien.txt
def write_current_loop(current_loop):
    with open("dzien.txt", "w") as file:
        file.write(str(current_loop))


async def send_initial_message(bot):
    channel_id = 1117138964218912841  # ID kanału, na którym bot ma wysłać początkową wiadomość
    channel = bot.get_channel(channel_id)
    message = "Bot został włączony i jest gotowy do działania!"
    await channel.send(message)