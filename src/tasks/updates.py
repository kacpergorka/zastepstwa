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

# Zewnętrzne biblioteki
import discord

# Wewnętrzne importy
from src.handlers.configuration import (
	blokadaKonfiguracji,
	konfiguracja
)
from src.handlers.data import zarządzajPlikiemDanych
from src.handlers.logging import logiKonsoli
from src.handlers.notifications import wyślijAktualizacje
from src.handlers.parser import wyodrębnijDane
from src.handlers.scraper import pobierzZawartośćStrony
from src.helpers.helpers import (
	blokadaNaSerwer,
	obliczSumęKontrolną,
	pobierzListęKlas
)

async def sprawdźAktualizacje(bot: discord.Client) -> None:
	"""
	Monitoruje i sprawdza aktualizacje zastępstw dla wszystkich serwerów i szkół zdefiniowanych w pliku konfiguracyjnym.

	Args:
		bot (discord.Client): Instancja klienta Discord.
	"""

	await bot.wait_until_ready()
	while not bot.is_closed():
		async with blokadaKonfiguracji:
			szkoły = dict(konfiguracja.get("szkoły", {}).copy())
			serwery = dict(konfiguracja.get("serwery", {}).copy())

		if not szkoły:
			logiKonsoli.warning(
				"Brak zdefiniowanych szkół w pliku konfiguracyjnym. Uzupełnij brakujące dane i spróbuj ponownie."
			)
		else:
			for identyfikatorSzkoły, daneSzkoły in szkoły.items():
				url = (daneSzkoły or {}).get("url", "")

				if not url:
					logiKonsoli.warning(
						f"Nie ustawiono URL dla szkoły o ID {identyfikatorSzkoły} w pliku konfiguracyjnym. Uzupełnij brakujące dane i spróbuj ponownie."
					)
					continue

				zawartośćStrony = await pobierzZawartośćStrony(bot, url, kodowanie=(daneSzkoły or {}).get("kodowanie", "iso-8859-2"))
				serweryDoSprawdzenia = [int(identyfikatorSerwera) for identyfikatorSerwera, konfiguracjaSerwera in serwery.items() if (konfiguracjaSerwera or {}).get("szkoła", "") == identyfikatorSzkoły]

				if not zawartośćStrony or not serweryDoSprawdzenia:
					continue

				zadania = [sprawdźSerwer(int(identyfikatorSerwera), zawartośćStrony, bot) for identyfikatorSerwera in serweryDoSprawdzenia]
				await asyncio.gather(*zadania, return_exceptions=True)
		await asyncio.sleep(300)


async def sprawdźSerwer(
	identyfikatorSerwera: int,
	zawartośćStrony: str,
	bot: discord.Client
) -> None:
	"""
	Sprawdza aktualizacje per serwer, używając semafora ograniczającego jednoczesne sprawdzanie serwerów do trzech wątków.

	Args:
		identyfikatorSerwera (int): ID serwera Discord.
		zawartośćStrony (str): Zawartość strony z zastępstwami.
		bot (discord.Client): Instancja klienta Discord.
	"""

	async with blokadaNaSerwer:
		await sprawdźSerwery(identyfikatorSerwera, zawartośćStrony, bot)


async def sprawdźSerwery(
	identyfikatorSerwera: int,
	zawartośćStrony: str,
	bot: discord.Client
) -> None:
	"""
	Pobiera konfigurację serwera, sprawdza aktualizacje danych, wysyła aktualizacje i aktualizuje statystyki.

	Args:
		identyfikatorSerwera (int): ID serwera Discord.
		zawartośćStrony (str): Zawartość strony z zastępstwami.
		bot (discord.Client): Instancja klienta Discord.
	"""

	async with blokadaKonfiguracji:
		konfiguracjaSerwera = konfiguracja.get("serwery", {}).get(str(identyfikatorSerwera), {}).copy()

	identyfikatorKanału = konfiguracjaSerwera.get("identyfikator-kanalu", "")
	kanał = bot.get_channel(int(identyfikatorKanału))

	if not identyfikatorKanału or not kanał:
		return

	try:
		poprzednieDane = await zarządzajPlikiemDanych(identyfikatorSerwera)

		if not isinstance(poprzednieDane, dict):
			poprzednieDane = {}

		sumaKontrolnaPoprzednichInformacjiDodatkowych = poprzednieDane.get("suma-kontrolna-informacji-dodatkowych", "")
		sumaKontrolnaPoprzednichWpisówZastępstw = poprzednieDane.get("suma-kontrolna-wpisow-zastepstw", "")

		wybraneKlasy = konfiguracjaSerwera.get("wybrane-klasy", [])
		wybraniNauczyciele = konfiguracjaSerwera.get("wybrani-nauczyciele", [])

		listaKlas = pobierzListęKlas(konfiguracjaSerwera.get("szkoła", ""))
		informacjeDodatkowe, aktualneWpisyZastępstw = wyodrębnijDane(zawartośćStrony, wybraneKlasy, wybraniNauczyciele, listaKlas)
		sumaKontrolnaAktualnychInformacjiDodatkowych = obliczSumęKontrolną(informacjeDodatkowe)
		sumaKontrolnaAktualnychWpisówZastępstw = obliczSumęKontrolną(aktualneWpisyZastępstw)

		if sumaKontrolnaAktualnychInformacjiDodatkowych != sumaKontrolnaPoprzednichInformacjiDodatkowych or sumaKontrolnaAktualnychWpisówZastępstw != sumaKontrolnaPoprzednichWpisówZastępstw:
			if sumaKontrolnaAktualnychWpisówZastępstw == sumaKontrolnaPoprzednichWpisówZastępstw:
				logiKonsoli.debug(
					f"Treść informacji dodatkowych uległa zmianie dla serwera o ID {identyfikatorSerwera}. Zostaną wysłane zaktualizowane informacje."
				)
			else:
				logiKonsoli.debug(
					f"Treść zastępstw uległa zmianie dla serwera o ID {identyfikatorSerwera}. Zostaną wysłane zaktualizowane zastępstwa."
				)

			try:
				if sumaKontrolnaAktualnychInformacjiDodatkowych != sumaKontrolnaPoprzednichInformacjiDodatkowych and sumaKontrolnaAktualnychWpisówZastępstw == sumaKontrolnaPoprzednichWpisówZastępstw:
					await wyślijAktualizacje(kanał, identyfikatorSerwera, informacjeDodatkowe, None)

				elif sumaKontrolnaAktualnychInformacjiDodatkowych == sumaKontrolnaPoprzednichInformacjiDodatkowych and sumaKontrolnaAktualnychWpisówZastępstw != sumaKontrolnaPoprzednichWpisówZastępstw:
					await wyślijAktualizacje(kanał, identyfikatorSerwera, informacjeDodatkowe, aktualneWpisyZastępstw)

				else:
					await wyślijAktualizacje(kanał, identyfikatorSerwera, informacjeDodatkowe, aktualneWpisyZastępstw)

				poprzedniLicznik = int(poprzednieDane.get("licznik-zastepstw", 0))

				if sumaKontrolnaAktualnychWpisówZastępstw != sumaKontrolnaPoprzednichWpisówZastępstw:
					przyrost = sum(len(wpisy) for _, wpisy in aktualneWpisyZastępstw) if aktualneWpisyZastępstw else 0
					nowyLicznik = poprzedniLicznik + przyrost
					statystykiNauczycieli = poprzednieDane.get("statystyki-nauczycieli", {})

					if not isinstance(statystykiNauczycieli, dict):
						statystykiNauczycieli = {}

					for tytuł, wpisy in (aktualneWpisyZastępstw or []):
						nazwa = (tytuł or "").strip()

						if "Zastępstwa z nieprzypisanymi klasami!" in nazwa:
							for wpis in wpisy:
								if "**Nauczyciel:**" in wpis:
									nauczyciel = wpis.split("**Nauczyciel:**", 1)[1].strip()
									nauczyciel = nauczyciel.split("\n", 1)[0].strip().split("/", 1)[0].split(" - ", 1)[0].strip()
									statystykiNauczycieli[nauczyciel] = int(statystykiNauczycieli.get(nauczyciel, 0)) + 1

							continue

						klucz = nazwa.split("/", 1)[0].split(" - ", 1)[0].strip()
						statystykiNauczycieli[klucz] = int(statystykiNauczycieli.get(klucz, 0)) + len(wpisy)
				else:
					nowyLicznik = poprzedniLicznik
					statystykiNauczycieli = poprzednieDane.get("statystyki-nauczycieli", {})

					if not isinstance(statystykiNauczycieli, dict):
						statystykiNauczycieli = {}

				noweDane = {
					"suma-kontrolna-informacji-dodatkowych": sumaKontrolnaAktualnychInformacjiDodatkowych,
					"suma-kontrolna-wpisow-zastepstw": sumaKontrolnaAktualnychWpisówZastępstw,
					"licznik-zastepstw": nowyLicznik,
					"statystyki-nauczycieli": statystykiNauczycieli,
					"ostatni-raport": poprzednieDane.get("ostatni-raport", "")
				}

				await zarządzajPlikiemDanych(identyfikatorSerwera, noweDane)
			except discord.DiscordException as e:
				logiKonsoli.exception(
					f"Nie udało się wysłać wszystkich wiadomości do serwera o ID {identyfikatorSerwera}, suma kontrolna nie zostanie zaktualizowana. Więcej informacji: {e}"
				)
	except Exception as e:
		logiKonsoli.exception(
			f"Wystąpił błąd podczas przetwarzania aktualizacji dla serwera o ID {identyfikatorSerwera}. Więcej informacji: {e}"
		)