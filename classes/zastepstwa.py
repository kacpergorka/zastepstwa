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
import contextlib
from datetime import datetime

# Zewnętrzne biblioteki
import aiohttp
import discord
import pytz

# Wewnętrzne importy
from assets.ascii import ascii
from commands import (
	informacje,
	skonfiguruj,
	statystyki
)
from events import (
	join,
	remove
)
from handlers.configuration import konfiguracja
from handlers.logging import logiKonsoli
from tasks.statistics import sprawdźKoniecRoku
from tasks.updates import sprawdźAktualizacje

class Zastępstwa(discord.Client):
	"""
	Domyślne ustawienia, działania i operacje bota.

	Attributes:
		intents (discord.Intents): Uprawnienia (intencje) klienta Discord.
	"""

	def __init__(
		self,
		*,
		intents: discord.Intents
	) -> None:
		"""
		Inicjalizuje instancję klienta Zastępstwa.

		Args:
			intents (discord.Intents): Uprawnienia (intencje) klienta Discord.
		"""

		super().__init__(intents=intents)
		self.tree = discord.app_commands.CommandTree(self)

	async def setup_hook(self) -> None:
		"""
		Tworzy i konfiguruje sesję HTTP wywoływaną przy starcie bota.
		"""

		try:
			wersja = konfiguracja.get("wersja", "Brak danych")
			self.połączenieHTTP = aiohttp.ClientSession(
				timeout=aiohttp.ClientTimeout(total=10),
				headers={"User-Agent": f"Zastepstwa/{wersja} (https://github.com/kacpergorka/zastepstwa)"}
			)
		except Exception as e:
			logiKonsoli.critical(
				f"Nie udało się utworzyć sesji HTTP. Więcej informacji: {e}"
			)
			raise

	async def close(self) -> None:
		"""
		Bezpiecznie wyłącza bota, anuluje wszystkie zadania i zamyka sesję HTTP.
		"""

		for atrybut in ("aktualizacje", "koniecRoku"):
			zadanie = getattr(self, atrybut, None)

			if zadanie and not zadanie.done():
				try:
					zadanie.cancel()
				except Exception as e:
					logiKonsoli.exception(
						f"Wystąpił błąd podczas zatrzymywania zadania ({atrybut}). Więcej informacji: {e}"
					)

				with contextlib.suppress(asyncio.CancelledError, Exception):
					await zadanie

		if getattr(self, "połączenieHTTP", None):
			try:
				await self.połączenieHTTP.close()
			except Exception as e:
				logiKonsoli.exception(
					f"Wystąpił błąd podczas zamykania sesji HTTP. Więcej informacji: {e}"
				)

		await super().close()

	async def on_ready(self) -> None:
		"""
		Ustawia status, synchronizuje polecenia i uruchamia zadania okresowe wywoływane po zalogowaniu bota.
		"""

		try:
			self.zaczynaCzas = datetime.now(pytz.timezone("Europe/Warsaw"))
			logiKonsoli.info(ascii)
			logiKonsoli.info(
				f"Zalogowano jako {self.user.name} (ID: {self.user.id}). Czekaj..."
			)
			await self.tree.sync()
			await self.change_presence(
				status=discord.Status.online,
				activity=discord.CustomActivity(name="kacpergorka.com/zastepstwa")
			)

			if not getattr(self, "aktualizacje", None) or self.aktualizacje.done():
				self.aktualizacje = asyncio.create_task(sprawdźAktualizacje(self))
			else:
				logiKonsoli.info(
					"Zadanie sprawdzające aktualizacje zastępstw jest już uruchomione. Próba ponownego jego uruchomienia została zatrzymana."
				)

			if not getattr(self, "koniecRoku", None) or self.koniecRoku.done():
				self.koniecRoku = asyncio.create_task(sprawdźKoniecRoku(self))
			else:
				logiKonsoli.info(
					"Zadanie sprawdzające zakończenie roku szkolnego jest już uruchomione. Próba ponownego jego uruchomienia została zatrzymana."
				)

			logiKonsoli.info(
				"Wszystkie zadania zostały poprawnie uruchomione. Enjoy!"
			)
		except Exception as e:
			logiKonsoli.exception(
				f"Wystąpił błąd podczas wywoływania funkcji on_ready. Więcej informacji: {e}"
			)

# Konfiguracja uprawnień bota
intents = discord.Intents.default()
bot = Zastępstwa(intents=intents)

# Import poleceń i eventów do synchronizacji
informacje.ustaw(bot)
skonfiguruj.ustaw(bot)
statystyki.ustaw(bot)
join.ustaw(bot)
remove.ustaw(bot)