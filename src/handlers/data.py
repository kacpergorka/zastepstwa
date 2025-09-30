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
import contextlib
import json
import os
from pathlib import Path
from typing import Any

# Wewnętrzne importy
from src.handlers.logging import logiKonsoli

# Ścieżka folderu z plikami danych
folderDanych = Path("resources")
folderDanych.mkdir(exist_ok=True)

# Globalna blokada modyfikacji pliku danych per serwer
blokadaPlikuNaSerwer = defaultdict(lambda: asyncio.Lock())

async def zarządzajPlikiemDanych(
	identyfikatorSerwera: str,
	dane: Any = None
) -> dict[str, Any]:
	"""
	Zarządza plikiem danych w formacie `JSON` dla konkretnego serwera Discord.

	Args:
		identyfikatorSerwera (str): ID serwera Discord, którego dane mają być odczytane lub zapisane.
		dane (Any, optional): Jeśli podane, zostaną zapisane w pliku danych serwera. Domyślnie None.

	Returns:
		dict[str, Any]: Zawartość pliku danych serwera po operacji odczytu, lub pusty słownik w przypadku błędu.
  """

	identyfikatorSerwera = str(identyfikatorSerwera)
	ścieżkaPliku = folderDanych / f"{identyfikatorSerwera}.json"

	tymczasowy = ścieżkaPliku.with_suffix(".json.tmp")
	kopia = ścieżkaPliku.with_suffix(".json.old")
	uszkodzony = ścieżkaPliku.with_suffix(".json.bad")

	async with blokadaPlikuNaSerwer[identyfikatorSerwera]:
		try:
			if dane is not None:
				def zapisz() -> None:
					"""
					Funkcja pomocnicza zapisująca dane serwera Discord do pliku danych w formacie `JSON`.
					"""

					with open(tymczasowy, "w", encoding="utf-8") as plik:
						json.dump(dane, plik, ensure_ascii=False, indent=4)

					try:
						if ścieżkaPliku.exists():
							with contextlib.suppress(Exception):
								os.remove(str(kopia))

							os.replace(str(ścieżkaPliku), str(kopia))
					except Exception as e:
						logiKonsoli.exception(
							f"Wystąpił błąd podczas zapisywania kopii pliku danych z rozszerzeniem .old dla {ścieżkaPliku}. Więcej informacji: {e}"
						)

					os.replace(str(tymczasowy), str(ścieżkaPliku))
				await asyncio.to_thread(zapisz)

			def odczytaj() -> bool:
				"""
				Funkcja pomocnicza odczytująca plik danych serwera Discord.

				Returns:
					bool: True, jeśli plik danych istnieje, False w przeciwnym wypadku.
				"""

				return ścieżkaPliku.exists()

			if await asyncio.to_thread(odczytaj):
				try:
					def wczytaj() -> Any:
						"""
						Wczytuje i parsuje zawartość pliku danych serwera Discord jako `JSON`.

						Returns:
							Any: Zawartość pliku danych w formacie `JSON`.
						"""

						return json.loads(ścieżkaPliku.read_text(encoding="utf-8"))

					return await asyncio.to_thread(wczytaj)
				except (json.JSONDecodeError, UnicodeDecodeError) as e:
					logiKonsoli.exception(
						f"Wystąpił błąd podczas wczytywania pliku danych. Więcej informacji: {e}"
					)
					try:
						await asyncio.to_thread(os.replace, str(ścieżkaPliku), str(uszkodzony))
						logiKonsoli.exception(
							f"Uszkodzony plik danych został przeniesiony do {uszkodzony}. Wczytano pustą zawartość."
						)
					except Exception as e:
						logiKonsoli.exception(
							f"Wystąpił błąd podczas przenoszenia uszkodzonego pliku danych. Więcej informacji: {e}"
						)

					return {}

			return {}
		except Exception as e:
			logiKonsoli.exception(
				f"Wystąpił błąd podczas operacji na pliku danych. Więcej informacji: {e}"
			)

			if tymczasowy.exists():
				try:
					tymczasowy.unlink()
				except Exception as e:
					logiKonsoli.exception(
						f"Nie udało się usunąć tymczasowego pliku danych ({tymczasowy}). Więcej informacji: {e}"
					)
					pass

			return {}