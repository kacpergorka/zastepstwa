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
import json
import os
from pathlib import Path
from typing import Any

# Wewnętrzne importy
from src.handlers.logging import logiKonsoli

# Globalna blokada modyfikacji pliku konfiguracyjnego
blokadaKonfiguracji = asyncio.Lock()

# Ścieżka pliku konfiguracyjnego
ścieżkaKonfiguracji = Path("config.json")

def wczytajKonfiguracje(path: Path = ścieżkaKonfiguracji) -> dict[str, Any]:
	"""
	Wczytuje plik konfiguracyjny zapisany w formacie `JSON`.

	Args:
		path (Path): Ścieżka do pliku konfiguracyjnego. Domyślnie `config.json`.

	Returns:
		dict[str, Any]: Zawartość pliku konfiguracyjnego jako słownik.
	"""

	def uporządkuj(
		dane: dict[str, Any],
		wzorzec: dict[str, Any]
	) -> dict[str, Any]:
		"""
		Uporządkowuje słownik `dane` według kolejności kluczy w `wzorzec`, zachowując wszystkie dodatkowe klucze na końcu.

		Args:
			dane (dict[str, Any]): Słownik do uporządkowania.
			wzorzec (dict[str, Any]): Słownik określający domyślną kolejność kluczy.

		Returns:
			dict[str, Any]: Nowy słownik z uporządkowanymi kluczami.
		"""

		wynik = {}

		for klucz in wzorzec:
			if klucz in dane:
				wynik[klucz] = dane[klucz]

		for klucz in dane:
			if klucz not in wynik:
				wynik[klucz] = dane[klucz]

		return wynik

	domyślne = {
		"wersja": "2.3.3.0-stable",
		"token": "",
		"koniec-roku-szkolnego": "2026-06-26",
		"serwery": {},
		"szkoły": {
			"01": {
				"nazwa": "Zespół Szkół Przykładowych w Przykładowicach",
				"url": "https://kacpergorka.com/zastepstwa/01",
				"kodowanie": "iso-8859-2",
				"lista-klas": {
					"1": [],
					"2": [],
					"3": [],
					"4": [],
					"5": []
				},
				"lista-nauczycieli": []
			},
			"02": {
				"nazwa": "LXVII Liceum Ogólnokształcące w Przykładowicach",
				"url": "https://kacpergorka.com/zastepstwa/02",
				"kodowanie": "iso-8859-2",
				"lista-klas": {
					"1": [],
					"2": [],
					"3": [],
					"4": []
				},
				"lista-nauczycieli": []
			}
		},
	}

	if not path.exists():
		path.write_text(json.dumps(domyślne, ensure_ascii=False, indent=4), encoding="utf-8")
		logiKonsoli.warning(
			"Utworzono plik konfiguracyjny z domyślną zawartością. Uzupełnij brakujące i skoryguj domyślnie uzupełnione dane."
		)
		return domyślne

	try:
		dane = json.loads(path.read_text(encoding="utf-8"))

		for klucz, wartość in domyślne.items():
			dane.setdefault(klucz, wartość)

		dane = uporządkuj(dane, domyślne)
		path.write_text(json.dumps(dane, ensure_ascii=False, indent=4), encoding="utf-8")

		if dane.get("wersja", "") != domyślne["wersja"]:
			logiKonsoli.warning(
				f"Aktualizuję wersję oprogramowania z {dane.get('wersja', 'Brak danych')} na {domyślne['wersja']}."
			)
			dane["wersja"] = domyślne["wersja"]
			path.write_text(json.dumps(dane, ensure_ascii=False, indent=4), encoding="utf-8")

		return dane
	except json.JSONDecodeError as e:
		logiKonsoli.exception(
			f"Wystąpił błąd podczas wczytywania pliku konfiguracyjnego. Więcej informacji: {e}"
		)
		raise

konfiguracja = wczytajKonfiguracje()

async def zapiszKonfiguracje(konfiguracja: dict[str, Any]) -> None:
	"""
	Zapisuje słownik konfiguracji do pliku konfiguracyjnego w formacie `JSON`.

	Args:
		konfiguracja (dict[str, Any]): Słownik konfiguracji do zapisania.
	"""

	def zapisz() -> None:
		"""
		Zapisuje słownik konfiguracji do tymczasowego pliku konfiguracyjnego w formacie `JSON`,
		a następnie nadpisuje istniejący plik konfiguracji, dodatkowo tworząc kopię `.old`.
		"""

		tymczasowy = ścieżkaKonfiguracji.with_suffix(".json.tmp")

		with open(tymczasowy, "w", encoding="utf-8") as plik:
			json.dump(konfiguracja, plik, ensure_ascii=False, indent=4)

		try:
			if ścieżkaKonfiguracji.exists():
				kopia = ścieżkaKonfiguracji.with_suffix(".json.old")

				with contextlib.suppress(Exception):
					os.remove(str(kopia))

				os.replace(str(ścieżkaKonfiguracji), str(kopia))
		except Exception as e:
			logiKonsoli.exception(
				f"Wystąpił błąd podczas zapisywania kopii pliku konfiguracyjnego z rozszerzeniem .old dla {ścieżkaKonfiguracji}. Więcej informacji: {e}"
			)

		os.replace(str(tymczasowy), str(ścieżkaKonfiguracji))

	try:
		await asyncio.to_thread(zapisz)
	except Exception as e:
		logiKonsoli.exception(
			f"Wystąpił błąd podczas zapisywania pliku konfiguracyjnego. Więcej informacji: {e}"
		)