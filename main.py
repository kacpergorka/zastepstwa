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
import os
import signal
import sys

# Zewnętrzne biblioteki
import discord

# Wewnętrzne importy
from src.classes.zastepstwa import bot
from src.handlers.configuration import konfiguracja
from src.handlers.logging import logiKonsoli

def wyłączBota(*_):
	"""
	Wyłącza bota w bezpieczny sposób po przechwyceniu sygnału systemowego.

	Args:
		*_: Dowolne argumenty przekazywane automatycznie przez sygnał systemowy.
	"""

	logiKonsoli.info(
		"Przechwycono Ctrl+C. Trwa zatrzymywanie bota..."
	)
	bot.loop.call_soon_threadsafe(lambda: asyncio.create_task(bot.close()))

signal.signal(signal.SIGINT, wyłączBota)

if hasattr(signal, "SIGTERM"):
	signal.signal(signal.SIGTERM, wyłączBota)

if hasattr(signal, "SIGBREAK"):
	signal.signal(signal.SIGBREAK, wyłączBota)


def włączBota():
	"""
	Uruchamia bota z tokenem znajdującym się w zmiennej środowiskowej lub pliku konfiguracyjnym.
	"""

	try:
		token = os.getenv("ZASTEPSTWA")
		if not token:
			token = konfiguracja.get("token", "")

			if not token:
				logiKonsoli.critical(
					"Nie znaleziono tokena bota. Utwórz zmienną środowiskową z zawartością tokena o nazwie „ZASTEPSTWA” lub uzupełnij plik konfiguracyjny."
				)
				sys.exit(1)

		bot.run(token)
	except discord.LoginFailure as e:
		logiKonsoli.critical(
			f"Nieprawidłowy token bota. Więcej informacji: {e}"
		)
		raise
	except Exception as e:
		logiKonsoli.exception(
			f"Wystąpił krytyczny błąd podczas uruchamiania bota. Więcej informacji: {e}"
		)

włączBota()