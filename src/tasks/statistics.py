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
from src.classes.constants import Constants
from src.handlers.configuration import (
	blokadaKonfiguracji,
	konfiguracja
)
from src.handlers.data import zarządzajPlikiemDanych
from src.handlers.logging import logiKonsoli
from src.helpers.helpers import (
	blokadaNaSerwer,
	odmieńZastępstwa,
	ograniczUsuwanie,
	ograniczWysyłanie,
	zwróćNazwyKluczy
)

async def sprawdźKoniecRoku(bot: discord.Client) -> None:
	"""
	Monitoruje datę zakończenia roku szkolnego i generuje raport podsumowujący statystyki zastępstw.

	Args:
		bot (discord.Client): Instancja klienta Discord.
	"""

	await bot.wait_until_ready()
	while not bot.is_closed():
		try:
			async with blokadaKonfiguracji:
				dataZakończeniaRoku = konfiguracja.get("koniec-roku-szkolnego", "").strip()
				serwery = list(konfiguracja.get("serwery", {}).keys())

			if not dataZakończeniaRoku:
				logiKonsoli.warning(
					"Nie ustawiono daty zakończenia roku szkolnego w pliku konfiguracyjnym. Uzupełnij brakujące dane i spróbuj ponownie."
				)
				await asyncio.sleep(3600)
				continue

			daneCzasu = None

			for formatCzasu in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
				try:
					daneCzasu = datetime.strptime(dataZakończeniaRoku, formatCzasu)
					break
				except ValueError:
					continue

			if not daneCzasu:
				logiKonsoli.error(
					f"Niepoprawny format daty zakończenia roku szkolnego w pliku konfiguracyjnyn ({dataZakończeniaRoku}). Oczekiwane formaty: YYYY-MM-DD lub YYYY-MM-DD HH:MM:SS."
				)
				await asyncio.sleep(3600)
				continue

			if len(dataZakończeniaRoku) == 10:
				daneCzasu = daneCzasu.replace(hour=0, minute=0, second=0)

			koniecRoku = pytz.timezone("Europe/Warsaw").localize(daneCzasu)
			aktualnyCzas = datetime.now(pytz.timezone("Europe/Warsaw"))

			if aktualnyCzas >= koniecRoku:
				for identyfikatorSerwera in serwery:
					identyfikatorSerwera = int(identyfikatorSerwera)

					try:
						async with blokadaKonfiguracji:
							konfiguracjaSerwera = konfiguracja.get("serwery", {}).get(str(identyfikatorSerwera), {}).copy()

						identyfikatorKanału = konfiguracjaSerwera.get("identyfikator-kanalu", "")
						kanał = bot.get_channel(int(identyfikatorKanału))

						if not identyfikatorKanału or not kanał:
							continue

						dane = await zarządzajPlikiemDanych(identyfikatorSerwera) or {}
						licznik = int(dane.get("licznik-zastepstw", 0))

						if licznik == 0:
							dane["ostatni-raport"] = dataZakończeniaRoku
							dane["licznik-zastepstw"] = 0
							dane["statystyki-nauczycieli"] = {}

							for klucz in ("suma-kontrolna-informacji-dodatkowych", "suma-kontrolna-wpisow-zastepstw"):
								if klucz not in dane:
									dane[klucz] = ""

							await zarządzajPlikiemDanych(identyfikatorSerwera, dane)
							continue

						ostatniRaport = dane.get("ostatni-raport", "").strip()

						if ostatniRaport == dataZakończeniaRoku:
							continue

						if kanał.permissions_for(kanał.guild.me).mention_everyone:
							async with blokadaNaSerwer:
								wzmianka = await ograniczWysyłanie(kanał, "@everyone Podsumowanie roku szkolnego!", allowed_mentions=discord.AllowedMentions(everyone=True))
							await asyncio.sleep(5)

							try:
								await ograniczUsuwanie(wzmianka)
							except Exception:
								pass
						else:
							logiKonsoli.warning(
								f"Brak uprawnień do używania @everyone dla serwera o ID {identyfikatorSerwera}. Wzmianka została pominięta."
							)

						tytuł = "**Podsumowanie roku szkolnego!**"
						opis = f"Dla tego serwera w tym roku szkolnym dostarczono **{licznik}** {odmieńZastępstwa(licznik)}! Poniżej znajduje się lista nauczycieli z największą liczbą zarejestrowanych zastępstw."
						stopka = f"Udanych i przede wszystkim bezpiecznych wakacji!\n{Constants.KRÓTSZA_STOPKA}"

						wybraniNauczyciele = konfiguracjaSerwera.get("wybrani-nauczyciele", [])
						wybraneKlasy = konfiguracjaSerwera.get("wybrane-klasy", [])
						statystyki = dane.get("statystyki-nauczycieli", {})

						if wybraneKlasy and not wybraniNauczyciele:
							embed = discord.Embed(
								title=tytuł,
								description=opis,
								color=Constants.KOLOR
							)

							if isinstance(statystyki, dict) and statystyki:
								sortowanie = sorted(statystyki.items(), key=lambda x: (-int(x[1]), x[0]))
								wolneMiejsca = 24 - len(embed.fields)

								if wolneMiejsca > 0:
									for nauczyciel, liczba in sortowanie[:wolneMiejsca]:
										embed.add_field(name=str(nauczyciel), value=f"Liczba zastępstw: {int(liczba)}", inline=True)

							embed.set_footer(text=stopka)
							async with blokadaNaSerwer:
								await ograniczWysyłanie(kanał, embed=embed)
							logiKonsoli.info(
								f"Roczne podsumowanie statystyk zastępstw zostało pomyślnie dostarczone do serwera o ID {identyfikatorSerwera}."
							)

						elif (wybraneKlasy and wybraniNauczyciele) or (wybraniNauczyciele and not wybraneKlasy):
							embed = discord.Embed(
								title=tytuł,
								description=(f"{opis} (Pominięto nauczycieli ustawionych w filtrze)."),
								color=Constants.KOLOR
							)

							wykluczeni = set()
							pozostali = {}

							for nauczyciel in wybraniNauczyciele:
								wykluczeni |= zwróćNazwyKluczy(nauczyciel)

							if isinstance(statystyki, dict):
								for nazwa, liczba in statystyki.items():
									if not (zwróćNazwyKluczy(nazwa) & wykluczeni):
										pozostali[nazwa] = int(liczba)

							if pozostali:
								sortowanie = sorted(pozostali.items(), key=lambda x: (-int(x[1]), x[0]))
								wolneMiejsca = 24 - len(embed.fields)

								if wolneMiejsca > 0:
									for nauczyciel, liczba in sortowanie[:wolneMiejsca]:
										embed.add_field(name=str(nauczyciel), value=f"Liczba zastępstw: {int(liczba)}", inline=True)
							else:
								embed.add_field(name="Brak danych", value="Nie znaleziono odpowiednich statystyk dla tego serwera.", inline=False)

							embed.set_footer(text=stopka)
							async with blokadaNaSerwer:
								await ograniczWysyłanie(kanał, embed=embed)
							logiKonsoli.info(
								f"Roczne podsumowanie statystyk zastępstw zostało pomyślnie dostarczone do serwera o ID {identyfikatorSerwera}."
							)

						dane["ostatni-raport"] = dataZakończeniaRoku
						dane["licznik-zastepstw"] = 0
						dane["statystyki-nauczycieli"] = {}

						for klucz in ("suma-kontrolna-informacji-dodatkowych", "suma-kontrolna-wpisow-zastepstw"):
							if klucz not in dane:
								dane[klucz] = ""

						await zarządzajPlikiemDanych(identyfikatorSerwera, dane)

					except Exception as e:
						logiKonsoli.exception(
							f"Wystąpił błąd podczas raportowania statystyk zastępstw na koniec roku dla serwera o ID {identyfikatorSerwera}. Więcej informacji: {e}"
						)
			await asyncio.sleep(24 * 3600)
		except Exception as e:
			logiKonsoli.exception(
				f"Wystąpił nieoczekiwany błąd podczas sprawdzania, czy nastąpiło zakończenie roku szkolnego. Więcej informacji: {e}"
			)
			await asyncio.sleep(3600)