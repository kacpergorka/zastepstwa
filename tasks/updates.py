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
from datetime import datetime

# Zewnętrzne biblioteki
import discord
import pytz

# Wewnętrzne importy
from handlers.configuration import (
	blokadaKonfiguracji,
	konfiguracja
)
from handlers.data import zarządzajPlikiemDanych
from handlers.logging import logiKonsoli
from handlers.notifications import wyślijAktualizacje
from handlers.parser import wyodrębnijDane
from handlers.scraper import pobierzZawartośćStrony
from helpers.helpers import (
	obliczSumęKontrolną,
	pobierzListęKlas,
	policzZastępstwa
)

# Sprawdza aktualizacje zastępstw
async def sprawdźAktualizacje(bot):
	await bot.wait_until_ready()
	while not bot.is_closed():
		async with blokadaKonfiguracji:
			szkoły = dict((konfiguracja.get("szkoły") or {}).copy())
			serwery = dict((konfiguracja.get("serwery") or {}).copy())
		if not szkoły:
			logiKonsoli.warning("Brak zdefiniowanych szkół w pliku konfiguracyjnym. Uzupełnij brakujące dane i spróbuj ponownie.")
		else:
			for identyfikatorSzkoły, daneSzkoły in szkoły.items():
				url = (daneSzkoły or {}).get("url")
				if not url:
					logiKonsoli.warning(f"Nie ustawiono URL dla szkoły o ID {identyfikatorSzkoły} w pliku konfiguracyjnym. Uzupełnij brakujące dane i spróbuj ponownie.")
					continue

				zawartośćStrony = await pobierzZawartośćStrony(bot, url, kodowanie=(daneSzkoły or {}).get("kodowanie"))
				if zawartośćStrony is None:
					logiKonsoli.debug(f"Nie udało się pobrać zawartości strony zastępstw szkoły o ID {identyfikatorSzkoły}. Aktualizacja została pominięta.")
					continue

				serweryDoSprawdzenia = [int(identyfikatorSerwera) for identyfikatorSerwera, konfiguracjaSerwera in serwery.items() if (konfiguracjaSerwera or {}).get("szkoła") == identyfikatorSzkoły]
				if not serweryDoSprawdzenia:
					continue
				zadania = [sprawdźSerwer(int(identyfikatorSerwera), zawartośćStrony) for identyfikatorSerwera in serweryDoSprawdzenia]
				await asyncio.gather(*zadania, return_exceptions=True)
		await asyncio.sleep(300)

# Sprawdza aktualizacje per serwer
blokadaNaSerwer = asyncio.Semaphore(3)
async def sprawdźSerwer(identyfikatorSerwera, zawartośćStrony, bot):
	async with blokadaNaSerwer:
		await sprawdźSerwery(identyfikatorSerwera, zawartośćStrony, bot)
async def sprawdźSerwery(identyfikatorSerwera, zawartośćStrony, bot):
	async with blokadaKonfiguracji:
		konfiguracjaSerwera = (konfiguracja.get("serwery", {}) or {}).get(str(identyfikatorSerwera), {}).copy()

	identyfikatorKanału = konfiguracjaSerwera.get("identyfikator-kanalu")
	if not identyfikatorKanału:
		logiKonsoli.debug(f"Nie ustawiono identyfikatora kanału dla serwera o ID {identyfikatorSerwera}.")
		return
	try:
		kanał = bot.get_channel(int(identyfikatorKanału))
	except (TypeError, ValueError):
		logiKonsoli.warning(f"Nieprawidłowy identyfikator kanału {identyfikatorKanału} dla serwera o ID {identyfikatorSerwera}.")
		return
	if not kanał:
		logiKonsoli.warning(f"Nie znaleziono kanału o ID {identyfikatorKanału} dla serwera o ID {identyfikatorSerwera}.")
		return

	logiKonsoli.debug(f"Sprawdzanie aktualizacji dla serwera o ID {identyfikatorSerwera}.")
	try:
		wybraneKlasy = konfiguracjaSerwera.get("wybrane-klasy", [])
		wybraniNauczyciele = konfiguracjaSerwera.get("wybrani-nauczyciele", [])
		listaKlas = pobierzListęKlas(konfiguracjaSerwera.get("szkoła"))
		informacjeDodatkowe, aktualneWpisyZastępstw = wyodrębnijDane(zawartośćStrony, wybraneKlasy, wybraniNauczyciele, listaKlas)

		sumaKontrolnaAktualnychInformacjiDodatkowych = obliczSumęKontrolną(informacjeDodatkowe)
		sumaKontrolnaAktualnychWpisówZastępstw = obliczSumęKontrolną(aktualneWpisyZastępstw)

		poprzednieDane = await zarządzajPlikiemDanych(identyfikatorSerwera)
		if not isinstance(poprzednieDane, dict):
			poprzednieDane = {}
		sumaKontrolnaPoprzednichInformacjiDodatkowych = poprzednieDane.get("suma-kontrolna-informacji-dodatkowych", "")
		sumaKontrolnaPoprzednichWpisówZastępstw = poprzednieDane.get("suma-kontrolna-wpisow-zastepstw", "")

		if sumaKontrolnaAktualnychInformacjiDodatkowych != sumaKontrolnaPoprzednichInformacjiDodatkowych or sumaKontrolnaAktualnychWpisówZastępstw != sumaKontrolnaPoprzednichWpisówZastępstw:
			if sumaKontrolnaAktualnychWpisówZastępstw == sumaKontrolnaPoprzednichWpisówZastępstw:
				logiKonsoli.info(f"Treść informacji dodatkowych uległa zmianie dla serwera o ID {identyfikatorSerwera}. Zostaną wysłane zaktualizowane informacje.")
			else:
				logiKonsoli.info(f"Treść zastępstw uległa zmianie dla serwera o ID {identyfikatorSerwera}. Zostaną wysłane zaktualizowane zastępstwa.")
			try:
				aktualnyCzas = datetime.now(pytz.timezone("Europe/Warsaw")).strftime("%d-%m-%Y %H:%M:%S")
				if sumaKontrolnaAktualnychInformacjiDodatkowych != sumaKontrolnaPoprzednichInformacjiDodatkowych and sumaKontrolnaAktualnychWpisówZastępstw == sumaKontrolnaPoprzednichWpisówZastępstw:
					await wyślijAktualizacje(kanał, identyfikatorSerwera, informacjeDodatkowe, None, aktualnyCzas)
				elif sumaKontrolnaAktualnychInformacjiDodatkowych == sumaKontrolnaPoprzednichInformacjiDodatkowych and sumaKontrolnaAktualnychWpisówZastępstw != sumaKontrolnaPoprzednichWpisówZastępstw:
					await wyślijAktualizacje(kanał, identyfikatorSerwera, informacjeDodatkowe, aktualneWpisyZastępstw, aktualnyCzas)
				else:
					await wyślijAktualizacje(kanał, identyfikatorSerwera, informacjeDodatkowe, aktualneWpisyZastępstw, aktualnyCzas)

				poprzedniLicznik = int(poprzednieDane.get("licznik-zastepstw", 0))
				if sumaKontrolnaAktualnychWpisówZastępstw != sumaKontrolnaPoprzednichWpisówZastępstw:
					przyrost = policzZastępstwa(aktualneWpisyZastępstw) if aktualneWpisyZastępstw else 0
					nowyLicznik = poprzedniLicznik + przyrost

					statystykiNauczycieli = poprzednieDane.get("statystyki-nauczycieli", {}) or {}
					if not isinstance(statystykiNauczycieli, dict):
						statystykiNauczycieli = {}

					for tytuł, wpisy in (aktualneWpisyZastępstw or []):
						nazwa = (tytuł or "").strip()
						if "Zastępstwa z nieprzypisanymi klasami!" in nazwa:
							for wpis in wpisy:
								if "**Nauczyciel:**" in wpis:
									nauczyciel = wpis.split("**Nauczyciel:**", 1)[1].strip()
									nauczyciel = nauczyciel.split("\n", 1)[0].strip().split("/", 1)[0].strip()
									statystykiNauczycieli[nauczyciel] = int(statystykiNauczycieli.get(nauczyciel, 0)) + 1
							continue

						klucz = nazwa.split("/", 1)[0].strip()
						statystykiNauczycieli[klucz] = int(statystykiNauczycieli.get(klucz, 0)) + len(wpisy)
				else:
					nowyLicznik = poprzedniLicznik
					statystykiNauczycieli = poprzednieDane.get("statystyki-nauczycieli", {}) or {}
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
				logiKonsoli.exception(f"Nie udało się wysłać wszystkich wiadomości do serwera o ID {identyfikatorSerwera}, suma kontrolna nie zostanie zaktualizowana. Więcej informacji: {e}")
		else:
			logiKonsoli.debug(f"Treść nie uległa zmianie dla serwera o ID {identyfikatorSerwera}. Brak nowych aktualizacji.")
	except Exception as e:
		logiKonsoli.exception(f"Wystąpił błąd podczas przetwarzania aktualizacji dla serwera o ID {identyfikatorSerwera}. Więcej informacji: {e}")