#
#
#    ▄▄▄▄▄▄▄▄     ▄▄       ▄▄▄▄    ▄▄▄▄▄▄▄▄  ▄▄▄▄▄▄▄▄  ▄▄▄▄▄▄      ▄▄▄▄    ▄▄▄▄▄▄▄▄ ▄▄      ▄▄    ▄▄
#    ▀▀▀▀▀███    ████    ▄█▀▀▀▀█   ▀▀▀██▀▀▀  ██▀▀▀▀▀▀  ██▀▀▀▀█▄  ▄█▀▀▀▀█   ▀▀▀██▀▀▀ ██      ██   ████
#        ██▀     ████    ██▄          ██     ██        ██    ██  ██▄          ██    ▀█▄ ██ ▄█▀   ████
#      ▄██▀     ██  ██    ▀████▄      ██     ███████   ██████▀    ▀████▄      ██     ██ ██ ██   ██  ██
#     ▄██       ██████        ▀██     ██     ██        ██             ▀██     ██     ███▀▀███   ██████
#    ███▄▄▄▄▄  ▄██  ██▄  █▄▄▄▄▄█▀     ██     ██▄▄▄▄▄▄  ██        █▄▄▄▄▄█▀     ██     ███  ███  ▄██  ██▄
#    ▀▀▀▀▀▀▀▀  ▀▀    ▀▀   ▀▀▀▀▀       ▀▀     ▀▀▀▀▀█▀▀  ▀▀         ▀▀▀▀▀       ▀▀     ▀▀▀  ▀▀▀  ▀▀    ▀▀
#                                                █▄▄
#

# Standardowe biblioteki
import asyncio
import copy
import discord

# Wewnętrzne importy
from src.handlers.configuration import (
	blokadaKonfiguracji,
	konfiguracja,
	zapiszKonfiguracje
)
from src.handlers.data import folderDanych
from src.handlers.logging import logiKonsoli

def ustaw(bot: discord.Client) -> None:
	"""
	Rejestruje event `on_guild_remove` w drzewie bota.

	Args:
		bot (discord.Client): Instancja klienta Discord, do której dodawany jest event.
	"""

	@bot.event
	async def on_guild_remove(guild: discord.Guild) -> None:
		"""
		Event wywoływany po usunięciu bota z serwera Discord.

		Args:
			guild (discord.Guild): Serwer Discord, z którego bot został usunięty.
		"""

		await usuńSerwerZKonfiguracji(guild.id)

	async def usuńSerwerZKonfiguracji(identyfikatorSerwera: int) -> None:
		"""
		Usuwa konfigurację serwera Discord z pliku konfiguracyjnego oraz jego pliki zasobów.

		Args:
			identyfikatorSerwera (int): ID serwera Discord, który ma zostać usunięty z konfiguracji.
		"""

		async with blokadaKonfiguracji:
			serwery = konfiguracja.setdefault("serwery", {})

			if str(identyfikatorSerwera) in serwery:
				del serwery[str(identyfikatorSerwera)]
				logiKonsoli.info(
					f"Usunięto serwer o ID {identyfikatorSerwera} z pliku konfiguracyjnego."
				)
			else:
				logiKonsoli.warning(
					f"Nie znaleziono konfiguracji serwera o ID {identyfikatorSerwera}. Dane nie zostały usunięte."
				)

			snapshot = copy.deepcopy(konfiguracja)
			await zapiszKonfiguracje(snapshot)

		for rozszerzenie in (".json", ".json.old", ".json.tmp", ".json.bad"):
			ścieżkaZasobów = folderDanych / f"{identyfikatorSerwera}{rozszerzenie}"

			if ścieżkaZasobów.exists():
				try:
					await asyncio.to_thread(ścieżkaZasobów.unlink)
					logiKonsoli.info(
						f"Usunięto plik zasobów ({ścieżkaZasobów})."
					)
				except Exception as e:
					logiKonsoli.exception(
						f"Wystąpił błąd podczas usuwania pliku zasobów ({ścieżkaZasobów}). Więcej informacji: {e}"
					)