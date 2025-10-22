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
from collections import defaultdict
import re
from typing import (
	Iterable,
	Optional
)

# Zewnętrzne biblioteki
from bs4 import (
	BeautifulSoup,
	NavigableString,
	Tag
)

# Wewnętrzne importy
from src.handlers.logging import logiKonsoli
from src.helpers.helpers import (
	normalizujTekst,
	zwróćNazwyKluczy
)

def wyodrębnijDane(
	zawartośćStrony: Optional[BeautifulSoup],
	wybraneKlasy: Optional[list[str]],
	wybraniNauczyciele: Optional[list[str]],
	listaKlas: Optional[list[str]]
) -> tuple[str, list[tuple[str, list[str]]]]:
	"""
	Wyodrębnia, przetwarza i filtruje dane zastępstw z pobranego pliku strony internetowej.

	Args:
		zawartośćStrony (Optional[BeautifulSoup]): Obiekt BeautifulSoup reprezentujący stronę HTML.
		wybraneKlasy (Optional[list[str]]): Lista wybranych klas, które mają być wykorzystane do filtracji.
		wybraniNauczyciele (Optional[list[str]]): Lista wybranych nauczycieli, którzy mają być wykorzystani do filtracji.
		listaKlas (Optional[list[str]]): Lista wszystkich klas wprowadzonych w pliku konfiguracyjnym.

	Returns:
		tuple[str, list[tuple[str, list[str]]]]:
			informacjeDodatkowe: Informacje znajdujące się nad zastępstwami.
			wpisyZastępstw: Wpisy zastępstw sortowane według nauczyciela.
	"""

	def wyczyśćTekst(węzeł: Optional[Tag | str]) -> str:
		"""
		Czyści i normalizuje zawartość pobranego pliku strony internetowej.

		Args:
			węzeł (Optional[Tag | str]): Element strony internetowej do przetworzenia.

		Returns:
			str: Oczyszczony i znormalizowany tekst.
		"""

		if not węzeł:
			return ""

		tymczasowy = BeautifulSoup(str(węzeł), "html.parser")

		try:
			for br in tymczasowy.find_all("br"):
				br.replace_with(NavigableString("\n"))

			for tag in tymczasowy.find_all(True):
				tag.unwrap()
		except Exception as e:
			logiKonsoli.exception(
				f"Wystąpił błąd podczas rozpakowywania tagów. Więcej informacji: {e}"
			)

		tekst = tymczasowy.get_text(separator="")
		tekst = tekst.replace("\r\n", "\n").replace("\r", "\n")
		tekst = tekst.replace("\xa0", " ")
		tekst = re.sub(r"[ \t]*\n[ \t]*", "\n", tekst)
		tekst = re.sub(r"[ \t]{2,}", " ", tekst)
		tekst = re.sub(r"\n\n", "\n", tekst)
		tekst = re.sub(r"\n{3,}", "\n\n", tekst)

		return tekst.strip("\n ")

	def sprawdźKlasyKomórki(
		komórka: Tag,
		nazwy: Iterable[str]
	) -> bool:
		"""
		Sprawdza, czy dana komórka HTML zawiera przynajmniej jedną z podanych klas `(np. class=st0)`.

		Args:
			komórka (Tag): Element HTML (np. <td>) do sprawdzenia.
			nazwy (Iterable[str]): Kolekcja nazw klas (lista, zbiór itp.) do dopasowania.

		Returns:
			bool: True, jeśli komórka zawiera którąkolwiek z klas, False w przeciwnym razie.
		"""

		klasy = komórka.get("class", [])

		if isinstance(klasy, str):
			klasy = [klasy]

		return any(klasa in nazwy for klasa in klasy)

	def sprawdźIstnienieZastępstw(wiersze: list[Tag]) -> bool:
		"""
		Sprawdza, czy w tabeli HTML istnieje przynajmniej jeden wiersz z realnym zastępstwem.

		Args:
			wiersze (list[Tag]): Lista wierszy (<tr>) pobranych z obiektu BeautifulSoup.

		Returns:
			bool: True, jeśli przynajmniej jeden wiersz zawiera dane zastępstwo, False w przeciwnym razie.
		"""

		nagłówki = {"lekcja", "opis", "zastępca", "uwagi"}

		for wiersz in wiersze:
			komórki = wiersz.find_all("td")

			if len(komórki) >= 4:
				teksty = [wyczyśćTekst(td).lower() for td in komórki[:4]]
				jestPuste = all(tekst == "" or tekst == "&nbsp;" for tekst in teksty)
				jestNagłówek = set(tekst.strip().lower() for tekst in teksty) <= nagłówki

				if not jestPuste and not jestNagłówek:
					return True

		return False

	def sprawdźPrzydatne(
		wartość: str,
		etykieta: str
	) -> bool:
		"""
		Sprawdza, czy dana wartość w wierszu tabeli jest przydatna, w celu jej wyświetlenia.

		Args:
			wartość (str): Tekst zawarty w polu wiersza (np. lekcja, opis, zastępca, uwagi).
			etykieta (str): Nagłówek odpowiadający wartości (np. "Lekcja", "Opis", "Zastępca", "Uwagi").

		Returns:
			bool: True, jeśli wartość jest niepusta i różna od etykiety, False w przeciwnym razie.
		"""

		return bool(wartość and wartość.lower() != etykieta.lower())

	def wyodrębnijNauczycieli(
		nazwaNagłówka: Optional[str],
		komórkaZastępcy: Optional[str]
	) -> set[str]:
		"""
		Wyodrębnia nazwiska nauczycieli z nagłówka i treści komórki zastępcy.

		Args:
			nazwaNagłówka (Optional[str]): Tekst nagłówka zawierający nazwisko nauczyciela.
			komórkaZastępcy (Optional[str]): Tekst komórki z informacją o zastępcy.

		Returns:
			set[str]: Zbiór unikalnych nazwisk nauczycieli.
		"""

		wyodrębnieniNauczyciele = set()

		if nazwaNagłówka and nazwaNagłówka.strip():
			wyodrębnieniNauczyciele.add(nazwaNagłówka.strip())

		if komórkaZastępcy and komórkaZastępcy.strip():
			części = re.split(r"[,\n;/&]| i | I ", komórkaZastępcy)

			for nauczyciel in części:
				nauczyciel = nauczyciel.strip()

				if nauczyciel and nauczyciel != "&nbsp;":
					wyodrębnieniNauczyciele.add(nauczyciel)

		return wyodrębnieniNauczyciele

	def sprawdźNauczyciela(
		wyodrębnieniNauczyciele: set[str],
		wybraniNauczyciele: list[str]
	) -> bool:
		"""
		Sprawdza, czy którykolwiek z wyodrębnionych nauczycieli znajduje się na liście wybranych nauczycieli.

		Args:
			wyodrębnieniNauczyciele (set[str]): Zbiór nazwisk nauczycieli wyodrębnionych z wiersza zastępstwa.
			wybraniNauczyciele (list[str]): Lista nauczycieli, których dopasowujemy.

		Returns:
			bool: True, jeśli przynajmniej jeden wyodrębniony nauczyciel pasuje do listy wybranych, False w przeciwnym razie.
		"""

		zbiórKluczy = set()
		kluczeWybranychNauczycieli = set()

		if not wybraniNauczyciele:
			return False

		for dopasowanie in wyodrębnieniNauczyciele:
			zbiórKluczy |= zwróćNazwyKluczy(dopasowanie)

		for nauczyciel in wybraniNauczyciele:
			kluczeWybranychNauczycieli |= zwróćNazwyKluczy(nauczyciel)

		return bool(zbiórKluczy & kluczeWybranychNauczycieli)

	def sprawdźKlasę(
		komórkiWiersza: list[str],
		wybraneKlasy: list[str]
	) -> bool:
		"""
		Sprawdza, czy wiersz HTML (lista wartości z wiersza tabeli) odpowiada którejkolwiek z wybranych klas.

		Args:
			komórkiWiersza (list[str]): Lista wartości z wiersza tabeli (np. lekcja, opis, zastępca, uwagi).
			wybraneKlasy (list[str]): Lista klas, które mają zostać dopasowane.

		Returns:
			bool: True, jeśli wiersz pasuje do przynajmniej jednej z wybranych klas, False w przeciwnym razie.
		"""

		komórki = komórkiWiersza[:]

		if not wybraneKlasy:
			return False

		if len(komórki) > 1 and komórki[1]:
			komórki[1] = komórki[1].split("-", 1)[0]

		tekst = " ".join(komórka or "" for komórka in komórki[:-1])
		tekst = normalizujTekst(tekst)
		tekst = re.sub(r"[\(\)]", " ", tekst)
		tekst = re.sub(r"\s+", " ", tekst)

		for klasa in wybraneKlasy:
			normaKlasy = normalizujTekst(klasa)
			części = normaKlasy.split()
			wzór = r"\b" + r"\s*".join(map(re.escape, części)) + r"\b"

			if re.search(wzór, tekst):
				return True

		return False

	if not zawartośćStrony:
		logiKonsoli.warning(
			"Brak treści pobranej ze strony. Zwracanie pustej zawartości."
		)
		return "", []

	try:
		informacjeDodatkowe = ""
		wiersze = zawartośćStrony.find_all("tr")
		zgrupowane = defaultdict(list)
		aktualnyNauczyciel = None
		komórkaST0 = None
		komórkaST1 = None

		for wiersz in wiersze:
			for komórka in wiersz.find_all("td"):

				if sprawdźKlasyKomórki(komórka, {"st0"}):
					tymczasowy = wyczyśćTekst(komórka).strip()

					if tymczasowy and tymczasowy != "&nbsp;":
						komórkaST0 = komórka
						break

			if komórkaST0:
				break

		if komórkaST0:
			link = komórkaST0.find("a")

			if link and link.get("href"):
				tekstLinku = wyczyśćTekst(link)
				urlLinku = link.get("href")
				link.replace_with(NavigableString(f"[{tekstLinku}]({urlLinku})"))

			tekstST0 = wyczyśćTekst(komórkaST0)
			tekstST0 = re.sub(r"[ \t]+", " ", tekstST0)
			tekstST0 = re.sub(r"\n+\[", " [", tekstST0)

			informacjeDodatkowe = tekstST0

		for wiersz in wiersze:
			komórki = wiersz.find_all("td")

			if len(komórki) == 1:
				aktualnyNauczyciel = wyczyśćTekst(komórki[0])
				continue

			if komórki and sprawdźKlasyKomórki(komórki[0], {"st0"}):
				continue

			if len(komórki) >= 4:
				teksty = [wyczyśćTekst(komórka) for komórka in komórki[:4]]
				lekcja, opis, zastępca, uwagi = teksty
				pola = [lekcja, opis, zastępca, uwagi]
				etykiety = ["Lekcja", "Opis", "Zastępca", "Uwagi"]

				if not any(sprawdźPrzydatne(wartość, etykieta) for wartość, etykieta in zip(pola, etykiety)):
					continue

				komórkiWiersza = [lekcja, opis, zastępca, uwagi]
				dopasowaneDoKlasy = sprawdźKlasę(komórkiWiersza, wybraneKlasy)
				wyodrębnieniNauczyciele = wyodrębnijNauczycieli(aktualnyNauczyciel, zastępca)
				dopasowaneDoNauczyciela = sprawdźNauczyciela(wyodrębnieniNauczyciele, wybraniNauczyciele)
				zastępstwoBezKlasy = False

				if wybraneKlasy:
					pełnyTekst = " ".join(komórkiWiersza)

					if listaKlas:
						znalezionoKlasy = any(re.search(r"\b" + re.escape(normalizujTekst(klasa)) + r"\b", normalizujTekst(pełnyTekst)) for klasa in listaKlas)
						zastępstwoBezKlasy = not znalezionoKlasy
					else:
						if not re.search(r"\d", pełnyTekst):
							zastępstwoBezKlasy = True

				wierszeWpisówZastępstw = []
				nazwaNauczyciela = aktualnyNauczyciel or ", ".join(wyodrębnieniNauczyciele)

				if zastępstwoBezKlasy:
					wierszeWpisówZastępstw.append(f"**Nauczyciel:** {nazwaNauczyciela}")

				for wartość, etykieta in zip(pola, etykiety):
					if sprawdźPrzydatne(wartość, etykieta):
						wierszeWpisówZastępstw.append(f"**{etykieta}:** {wartość}")
					else:
						wierszeWpisówZastępstw.append(f"**{etykieta}:** Brak")

				tekstWpisówZastępstw = "\n".join(wierszeWpisówZastępstw).strip()

				if not tekstWpisówZastępstw:
					continue

				if (wybraneKlasy or wybraniNauczyciele) and (dopasowaneDoKlasy or dopasowaneDoNauczyciela or zastępstwoBezKlasy):
					domyślnyTytuł = "Zastępstwa z nieprzypisanymi klasami!" if zastępstwoBezKlasy else nazwaNauczyciela
					zgrupowane[domyślnyTytuł].append(tekstWpisówZastępstw)

		wpisyZastępstw = [(nauczyciel, zgrupowane[nauczyciel]) for nauczyciel in zgrupowane if zgrupowane[nauczyciel]]
		wpisyZastępstw.sort(key=lambda x: 0 if "Zastępstwa z nieprzypisanymi klasami!" in x[0] else 1)

		if not informacjeDodatkowe and not sprawdźIstnienieZastępstw(wiersze):
			for wiersz in wiersze:
				for komórka in wiersz.find_all("td"):

					if sprawdźKlasyKomórki(komórka, {"st1"}):
						tymczasowy = wyczyśćTekst(komórka).strip()

						if tymczasowy and tymczasowy != "&nbsp;":
							komórkaST1 = komórka
							break

				if komórkaST1:
					break

			if komórkaST1:
				link = komórkaST1.find("a")

				if link and link.get("href"):
					tekstLinku = wyczyśćTekst(link)
					urlLinku = link.get("href")
					link.replace_with(NavigableString(f"[{tekstLinku}]({urlLinku})"))

				tekstST1 = wyczyśćTekst(komórkaST1)
				tekstST1 = re.sub(r"[ \t]+", " ", tekstST1)
				tekstST1 = re.sub(r"\n+\[", " [", tekstST1)

				informacjeDodatkowe = tekstST1

		return informacjeDodatkowe, wpisyZastępstw
	except Exception as e:
		logiKonsoli.exception(
			f"Wystąpił błąd podczas przetwarzania HTML. Więcej informacji: {e}"
		)
		return "", []