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
import aiohttp
import asyncio
from typing import Optional

# Zewnętrzne biblioteki
from bs4 import BeautifulSoup
import discord

# Wewnętrzne importy
from src.handlers.logging import logiKonsoli

async def pobierzZawartośćStrony(
	bot: discord.Client,
	url: str,
	kodowanie: str
) -> Optional[BeautifulSoup]:
	"""
	Pobiera zawartość strony internetowej.

	Args:
		bot (discord.Client): Instancja klienta Discord, z której wykorzystywane jest aktywne połączenie HTTP.
		url (str): Adres strony internetowej do pobrania.
		kodowanie (str): Kodowanie użyte do odczytu treści strony internetowej.

	Returns:
		Optional[BeautifulSoup]: Obiekt BeautifulSoup ze strukturą HTML lub None w przypadku błędu.
	"""

	try:
		async with bot.połączenieHTTP.get(url) as odpowiedź:
			odpowiedź.raise_for_status()

			tekst = await odpowiedź.text(encoding=kodowanie, errors="ignore")
			pętla = asyncio.get_running_loop()

			return await pętla.run_in_executor(None, lambda: BeautifulSoup(tekst, "html.parser"))
	except asyncio.TimeoutError:
		logiKonsoli.warning(
			f"Przekroczono czas oczekiwania na połączenie ({url})."
		)
	except aiohttp.ClientError as e:
		logiKonsoli.exception(
			f"Wystąpił błąd klienta HTTP podczas pobierania strony. Więcej informacji: {e}"
		)
	except Exception as e:
		logiKonsoli.exception(
			f"Wystąpił błąd podczas pobierania strony. Więcej informacji: {e}"
		)
	return None