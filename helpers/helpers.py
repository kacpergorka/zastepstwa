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
from collections import defaultdict
import copy
from datetime import datetime
import difflib
import hashlib
import re
from typing import Any
import unicodedata

# Zewnętrzne biblioteki
import discord
import pytz

# Wewnętrzne importy
from handlers.configuration import (
	blokadaKonfiguracji,
	konfiguracja,
	zapiszKonfiguracje
)

# Ograniczenie wykonywania jednoczesnych operacji dla serwera do trzech wątków
blokadaNaSerwer = asyncio.Semaphore(3)

# Zapewnienie, że wysyłanie, usuwanie i reagowanie wiadomości na danym kanale jest sekwencyjne
blokadaNaKanał = defaultdict(lambda: asyncio.Lock())

async def ograniczWysyłanie(
	kanał: discord.TextChannel,
	*args: Any,
	**kwargs: Any
) -> discord.Message:
	"""
	Wysyła wiadomość na kanał w bezpieczny, sekwencyjny sposób.

	Args:
		kanał (discord.TextChannel): Kanał tekstowy Discorda, na który ma zostać wysłana wiadomość.
		*args (Any): Argumenty przekazywane do `kanał.send`.
		**kwargs (Any): Argumenty nazwane przekazywane do `kanał.send`.

	Returns:
		discord.Message: Obiekt wiadomości wysłanej na kanał.
	"""

	async with blokadaNaKanał[kanał.id]:
		wiadomość = await kanał.send(*args, **kwargs)

		return wiadomość


async def ograniczUsuwanie(wiadomość: discord.Message) -> None:
	"""
	Usuwa wiadomość w bezpieczny, sekwencyjny sposób.

	Args:
		wiadomość (discord.Message): Wiadomość do usunięcia.
	"""

	async with blokadaNaKanał[wiadomość.channel.id]:
		await wiadomość.delete()


async def ograniczReagowanie(
	wiadomość: discord.Message,
	emoji: str
) -> None:
	"""
	Dodaje reakcję do wiadomości w bezpieczny, sekwencyjny sposób.

	Args:
		wiadomość (discord.Message): Wiadomość, do której ma zostać dodana reakcja.
		emoji (str): Emoji, które ma zostać dodane jako reakcja.
	"""

	async with blokadaNaKanał[wiadomość.channel.id]:
		await wiadomość.add_reaction(emoji)


def obliczSumęKontrolną(dane: Any) -> str:
	"""
	Oblicza sumę kontrolną (SHA-256) dla podanych danych.

	Args:
		dane (Any): Dane wejściowe.

	Returns:
		str: Ciąg znaków reprezentujący hash SHA-256 danych.
	"""

	if isinstance(dane, str):
		wejście = dane.strip()

	elif isinstance(dane, list):
		części = []

		for tytuł, wpisy in sorted(dane, key=lambda pozycja: pozycja[0]):
			części.append(tytuł.strip())

			for wpis in sorted(wpisy):
				części.append(wpis.strip())

		wejście = "\n".join(części)

	else:
		wejście = str(dane)

	return hashlib.sha256(wejście.encode("utf-8")).hexdigest()


def normalizujTekst(tekst: str) -> str:
	"""
	Normalizuje tekst w celu ujednolicenia go do porównań i filtracji.

	Args:
		tekst (str): Tekst wejściowy do normalizacji.

	Returns:
		str: Oczyszczony i znormalizowany tekst.
	"""

	if not tekst or not isinstance(tekst, str):
		return ""

	tekst = tekst.strip()
	tekst = unicodedata.normalize("NFKD", tekst)
	tekst = "".join(znak for znak in tekst if not unicodedata.combining(znak))
	tekst = tekst.replace(".", " ")
	tekst = re.sub(r"\s+", " ", tekst)

	return tekst.lower()


def zwróćNazwyKluczy(nazwa: str) -> set[str]:
	"""
	Tworzy zestaw kluczy dopasowań dla podanej nazwy.

	Args:
		nazwa (str): Tekst nazwy do przetworzenia.

	Returns:
		set[str]: Zestaw ciągów znaków używanych jako klucze dopasowań.
	"""

	norma = normalizujTekst(nazwa)

	if not norma:
		return set()

	części = norma.split()
	klucze = {norma}

	if części:
		klucze.add(części[-1])

	if len(części) >= 1:
		klucze.add(f"{części[0][0]} {części[-1]}")
		klucze.add(f"{części[0][0]}{części[-1]}")

	return klucze


def pobierzSłownikSerwera(identyfikatorSerwera: str) -> dict[str, Any]:
	"""
	Pobiera słownik konfiguracji dla podanego serwera. Jeśli serwer nie istnieje w konfiguracji, tworzy domyślną strukturę.

	Args:
		identyfikatorSerwera (str): ID serwera Discord.

	Returns:
		dict[str, Any]: Słownik z konfiguracją serwera.
	"""

	identyfikatorSerwera = str(identyfikatorSerwera)
	serwery = konfiguracja.setdefault("serwery", {})
	dane = serwery.setdefault(identyfikatorSerwera, {})

	if "identyfikator-kanalu" not in dane:
		dane["identyfikator-kanalu"] = ""

	if "szkoła" not in dane:
		dane["szkoła"] = ""

	if not isinstance(dane.get("wybrane-klasy"), list):
		dane["wybrane-klasy"] = []

	if not isinstance(dane.get("wybrani-nauczyciele"), list):
		dane["wybrani-nauczyciele"] = []

	serwery[identyfikatorSerwera] = dane
	return dane


def usuńDuplikaty(sekwencja: list[Any]) -> list[Any]:
	"""
	Usuwa duplikaty z listy, zachowując kolejność elementów.

	Args:
		sekwencja (list[Any]): Lista, z której mają zostać usunięte duplikaty.

	Returns:
		list[Any]: Lista bez duplikatów, w tej samej kolejności co oryginał.
	"""

	widziane = set()
	wynik = []

	for element in sekwencja:
		if element not in widziane:
			wynik.append(element)
			widziane.add(element)

	return wynik


async def zapiszKluczeSerwera(
	identyfikatorSerwera: str,
	dane: dict
) -> None:
	"""
	Zapisuje klucze i konfigurację wybranego serwera.

	Args:
		identyfikatorSerwera (str): ID serwera Discord.
		dane (dict): Słownik z danymi do zapisania.
	"""

	identyfikatorSerwera = str(identyfikatorSerwera)
	lokalneDane = dict(dane or {})

	async with blokadaKonfiguracji:
		serwery = konfiguracja.setdefault("serwery", {})
		daneSerwera = pobierzSłownikSerwera(identyfikatorSerwera)
		poprzedniaSzkoła = daneSerwera.get("szkoła", "")
		aktualnaSzkoła = lokalneDane.get("szkoła", "")

		if aktualnaSzkoła and poprzedniaSzkoła and poprzedniaSzkoła != aktualnaSzkoła:
			for klucz in ("wybrane-klasy", "wybrani-nauczyciele"):
				daneSerwera.pop(klucz, None)

		for klucz in ("wybrane-klasy", "wybrani-nauczyciele"):
			if klucz in lokalneDane:
				nowy = lokalneDane.pop(klucz, None)
				istnieje = daneSerwera.get(klucz, [])

				if not isinstance(istnieje, list):
					istnieje = list(istnieje)

				if not nowy:
					nowaLista = []
				elif isinstance(nowy, list):
					nowaLista = nowy
				else:
					nowaLista = [nowy]

				nowaLista = [str(element) for element in nowaLista if element]
				daneSerwera[klucz] = usuńDuplikaty(istnieje + nowaLista)

		if "identyfikator-kanalu" in lokalneDane:
			wartość = lokalneDane.pop("identyfikator-kanalu", "")

			if wartość:
				daneSerwera["identyfikator-kanalu"] = str(wartość)

		if "szkoła" in lokalneDane:
			wartość = lokalneDane.pop("szkoła", "")

			if wartość:
				daneSerwera["szkoła"] = wartość

		for klucz, wartość in lokalneDane.items():
			if wartość:
				daneSerwera[klucz] = wartość

		serwery[identyfikatorSerwera] = daneSerwera
		konfiguracja["serwery"] = serwery
		snapshot = copy.deepcopy(konfiguracja)

	await zapiszKonfiguracje(snapshot)


async def wyczyśćFiltry(identyfikatorSerwera: str) -> None:
	"""
	Czyści wszystkie filtry i konfiguracje dla danego serwera.

	Args:
		identyfikatorSerwera (str): ID serwera Discord.
	"""

	identyfikatorSerwera = str(identyfikatorSerwera)

	async with blokadaKonfiguracji:
		daneSerwera = pobierzSłownikSerwera(identyfikatorSerwera)
		daneSerwera["identyfikator-kanalu"] = ""
		daneSerwera["szkoła"] = ""
		daneSerwera["wybrane-klasy"] = []
		daneSerwera["wybrani-nauczyciele"] = []
		snapshot = copy.deepcopy(konfiguracja)

	await zapiszKonfiguracje(snapshot)


def dopasujWpisyDoListy(
	wpisy: list[str],
	listaDoDopasowania: list[str],
	cutoff: float=0.6
) -> tuple[list[str], dict[str, str], list[str]]:
	"""
	Dopasowuje listę wpisów do listy referencyjnej, próbując znaleźć dokładne lub przybliżone dopasowania.

	Args:
		wpisy (list[str]): Lista wpisów do dopasowania.
		listaDoDopasowania (list[str]): Lista referencyjna, do której mają być dopasowane wpisy.
		cutoff (float, optional): Minimalny próg podobieństwa dla dopasowań przybliżonych (0-1). Domyślnie 0.6.

	Returns:
		tuple[list[str], dict[str, str], list[str]]:
			idealneDopasowania: Lista idealnie dopasowanych wpisów.
			sugestie: Słownik sugestii przybliżonych dopasowań.
			nieZnaleziono: Lista wpisów, dla których nie znaleziono dopasowania.
	"""

	def stwórzKluczeNormalizacyjne(tekst: str) -> list[str]:
		"""
		Tworzy dwie wersje kluczy normalizacyjnych dla podanego tekstu.

		Args:
			tekst (str): Tekst wejściowy do przetworzenia.

		Returns:
			list[str]: Lista dwóch kluczy normalizacyjnych [tekstNormalizowany, brakSpacji].
		"""

		tekstNormalizowany = normalizujTekst(tekst)
		brakSpacji = re.sub(r"\s+", "", tekstNormalizowany)

		return [tekstNormalizowany, brakSpacji]

	def zbudujIndeks(listaDoDopasowania: list[str]) -> tuple[dict[str, list[str]], dict[str, list[str]], list[str]]:
		"""
		Buduje indeksy wyszukiwania dla listy referencyjnej, tworząc mapowanie kluczy normalizacyjnych do oryginalnych elementów.

		Args:
			listaDoDopasowania (list[str]): Lista elementów do przetworzenia.

		Returns:
			tuple[dict[str, list[str]], dict[str, list[str]], list[str]]:
				mapaKluczy: Słownik, w którym każdy klucz normalizacyjny mapuje do listy odpowiadających mu oryginalnych elementów.
				normalizowaneDoOryginalnych: Słownik odwzorowujący pełną znormalizowaną nazwę na listę oryginalnych elementów.
				listaNormalizowanych: Lista wszystkich pełnych znormalizowanych nazw występujących w liście elementów do przetworzenia.
		"""

		mapaKluczy = defaultdict(list)
		normalizowaneDoOryginalnych = defaultdict(list)
		listaNormalizowanych = []

		for element in listaDoDopasowania:
			pełnaNorma = re.sub(r"\s+", "", normalizujTekst(element))
			normalizowaneDoOryginalnych[pełnaNorma].append(element)
			listaNormalizowanych.append(pełnaNorma)

			for klucz in stwórzKluczeNormalizacyjne(element):
				mapaKluczy[klucz].append(element)

		return mapaKluczy, normalizowaneDoOryginalnych, listaNormalizowanych

	mapaKluczy, normalizowaneDoOryginalnych, listaNormalizowanych = zbudujIndeks(listaDoDopasowania)

	idealneDopasowania = []
	sugestie = {}
	nieZnaleziono = []

	for wpis in wpisy:
		kluczeWpisu = stwórzKluczeNormalizacyjne(wpis)
		znalezioneIdealneDopasowania = None

		for klucz in kluczeWpisu:
			if klucz in mapaKluczy:
				znalezioneIdealneDopasowania = mapaKluczy[klucz][0]
				break

		if znalezioneIdealneDopasowania:
			if znalezioneIdealneDopasowania not in idealneDopasowania:
				idealneDopasowania.append(znalezioneIdealneDopasowania)

			continue

		# Dopasowanie przybliżone
		normaWpisu = re.sub(r"\s+", "", normalizujTekst(wpis))
		normaKandydatów = difflib.get_close_matches(normaWpisu, listaNormalizowanych, n=1, cutoff=cutoff)

		if normaKandydatów:
			normaKandydata = normaKandydatów[0]
			kandydat = normalizowaneDoOryginalnych[normaKandydata][0]
			sugestie[wpis] = kandydat
		else:
			nieZnaleziono.append(wpis)

	return idealneDopasowania, sugestie, nieZnaleziono


def pobierzListęKlas(szkoła: str | None=None) -> list[str]:
	"""
	Pobiera listę klas dla wybranej szkoły z konfiguracji.

	Args:
		szkoła (str | None, optional): Szkoła, dla której mają zostać pobrane klasy.

	Returns:
		list[str]: Lista klas przypisanych do danej szkoły.
	"""

	suroweDane = (konfiguracja.get("szkoły", {})).get(szkoła, {}).get("lista-klas", {})

	if isinstance(suroweDane, dict):
		return [klasa for grupy in suroweDane.values() for klasa in grupy]

	if isinstance(suroweDane, list):
		return suroweDane

	return []


def policzZastępstwa(aktualneWpisyZastępstw: list[tuple[str, list[str]]]) -> int:
	"""
	Oblicza łączną liczbę zastępstw w podanej strukturze danych.

	Args:
		aktualneWpisyZastępstw (list[tuple[str, list[str]]]): Wpisy zastępstw sortowane według nauczyciela

	Returns:
		int: Suma wszystkich wpisów zastępstw. Zwraca 0, jeśli lista jest pusta lub niepoprawna.
	"""

	if not aktualneWpisyZastępstw:
		return 0

	try:
		return sum(len(wpisy) for _, wpisy in aktualneWpisyZastępstw)
	except Exception:
		return 0


def odmieńZastępstwa(licznik: int) -> str:
	"""
	Odmienia słowo „zastępstwo” w zależności od liczby zastępstw.

	Args:
		licznik (int): Liczba zastępstw.

	Returns:
		str: Poprawna forma słowa „zastępstwo” dopasowana do liczby.
	"""

	if abs(licznik) == 1:
		return "zastępstwo"

	if 11 <= abs(licznik) % 100 <= 14:
		return "zastępstw"

	if abs(licznik) % 10 in (2, 3, 4):
		return "zastępstwa"

	return "zastępstw"


def pobierzLiczbęSerwerów(bot: discord.Client) -> int:
	"""
	Pobiera liczbę serwerów, na których znajduje się bot.

	Args:
		bot (discord.Client): Instancja klienta Discord.

	Returns:
		int: Liczba serwerów, na których znajduje się bot.
	"""

	return len(bot.guilds)


def pobierzCzasDziałania(bot: discord.Client) -> str:
	"""
	Oblicza czas działania bota od momentu jego uruchomienia.

	Args:
		bot (discord.Client): Instancja klienta Discord.

	Returns:
		str: Sformatowany ciąg tekstowy z czasem działania w dniach, godzinach, minutach i sekundach.
	"""

	czasDziałania = datetime.now(pytz.timezone("Europe/Warsaw")) - bot.zaczynaCzas
	dni, reszta = divmod(czasDziałania.total_seconds(), 86400)
	godziny, reszta = divmod(reszta, 3600)
	minuty, sekundy = divmod(reszta, 60)

	return f"**{int(dni)}** dni, **{int(godziny)}** godz., **{int(minuty)}** min. i **{int(sekundy)}** sek."