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

# Zewnętrzne biblioteki
from bs4 import BeautifulSoup

# Wewnętrzne importy
from handlers.logging import logiKonsoli

# Pobiera zawartość strony internetowej
async def pobierzZawartośćStrony(bot, url, kodowanie=None):
	logiKonsoli.debug(f"Pobieranie zawartości strony ({url}).")
	try:
		async with bot.połączenieHTTP.get(url) as odpowiedź:
			odpowiedź.raise_for_status()
			tekst = await odpowiedź.text(encoding=kodowanie, errors="ignore")
			pętla = asyncio.get_event_loop()
			return await pętla.run_in_executor(None, lambda: BeautifulSoup(tekst, "html.parser"))
	except asyncio.TimeoutError:
		logiKonsoli.warning(f"Przekroczono czas oczekiwania na połączenie ({url}).")
	except aiohttp.ClientError as e:
		logiKonsoli.exception(f"Wystąpił błąd klienta HTTP podczas pobierania strony. Więcej informacji: {e}")
	except Exception as e:
		logiKonsoli.exception(f"Wystąpił błąd podczas pobierania strony. Więcej informacji: {e}")
	return None