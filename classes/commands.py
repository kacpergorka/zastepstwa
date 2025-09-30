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
import contextlib
import re

# Zewnętrzne biblioteki
import discord

# Wewnętrzne importy
from classes.constants import Constants
from handlers.configuration import konfiguracja
from handlers.logging import logiKonsoli
from helpers.helpers import (
	dopasujWpisyDoListy,
	pobierzListęKlas,
	pobierzSłownikSerwera,
	usuńDuplikaty,
	wyczyśćFiltry,
	zapiszKluczeSerwera
)

class WidokPodsumowania():
	"""
	Widok podsumowujący wcześniej wprowadzoną konfigurację bota dla serwera Discord.
	"""

	@staticmethod
	def utwórz(identyfikatorSerwera: str) -> discord.Embed:
		"""
		Tworzy i zwraca embed podsumowujący konfigurację bota dla serwera Discord.

		Args:
			identyfikatorSerwera (str): ID serwera Discord, dla którego generowany jest embed.

		Returns:
			discord.Embed: Embed z podsumowaniem aktualnej konfiguracji bota dla serwera Discord.
		"""

		konfiguracjaSerwera = pobierzSłownikSerwera(identyfikatorSerwera)
		identyfikatorSzkoły = konfiguracjaSerwera.get("szkoła", "")
		nazwaSzkoły = konfiguracja.get("szkoły", {}).get(identyfikatorSzkoły, {}).get("nazwa", identyfikatorSzkoły)

		kanał = f"<#{konfiguracjaSerwera.get('identyfikator-kanalu', '')}>" if konfiguracjaSerwera.get("identyfikator-kanalu", "") else "Brak"
		klasy = ", ".join(re.sub(r"(\d)\s+([A-Za-z])", r"\1\2", klasa) for klasa in konfiguracjaSerwera.get("wybrane-klasy", [])) or "Brak"
		nauczyciele = ", ".join(f"{nauczyciel}" for nauczyciel in konfiguracjaSerwera.get("wybrani-nauczyciele", [])) or "Brak"

		embed = discord.Embed(
			title="**Zapisano wprowadzone dane!**",
			description=f"Aktualna konfiguracja Twojego serwera dla szkoły **{nazwaSzkoły}** została wyświetlona poniżej.",
			color=Constants.KOLOR
		)
		embed.add_field(
			name="Kanał tekstowy:",
			value=kanał
		)
		embed.add_field(
			name="Wybrane klasy:",
			value=klasy
		)
		embed.add_field(
			name="Wybrani nauczyciele:",
			value=nauczyciele
		)
		embed.set_footer(text=Constants.DŁUŻSZA_STOPKA)
		return embed


class WidokPonownegoWprowadzania(discord.ui.View):
	"""
	Widok umożliwiający użytkownikowi ponowne wprowadzenie danych po naciśnięciu przycisku `Wprowadź ponownie`.

	Attributes:
		typDanych (str): Typ danych do wprowadzenia (np. `klasy` lub `nauczyciele`).
		listaDoDopasowania (list[str]): Lista elementów dostępnych do dopasowania.
		wiadomość (discord.Message): Wiadomość, w której widok jest wyświetlany.
		identyfikatorKanału (str): ID kanału tekstowego Discord, który został wybrany w opcjach polecenia.
		szkoła (str): ID szkoły, której dane przeznacza się do wykorzystania.
		timeout (float): Czas w sekundach, po którym widok wygasa (domyślnie 120.0).
	"""

	def __init__(
		self,
		typDanych: str,
		listaDoDopasowania: list[str],
		wiadomość: discord.Message,
		identyfikatorKanału: str,
		szkoła: str,
		timeout: float=120.0
	) -> None:
		super().__init__(timeout=timeout)
		self.typDanych = typDanych
		self.lista = listaDoDopasowania
		self.wiadomość = wiadomość
		self.identyfikatorKanału = identyfikatorKanału
		self.szkoła = szkoła

	@discord.ui.button(
		label="Wprowadź ponownie",
		style=discord.ButtonStyle.secondary
	)

	async def wprowadźPonownie(
		self,
		interaction: discord.Interaction,
		button: discord.ui.Button
	) -> None:
		try:
			await interaction.response.send_modal(ModalWybierania(self.typDanych, self.lista, self.wiadomość, self.identyfikatorKanału, self.szkoła))
		except Exception as e:
			logiKonsoli.exception(
				f"Wystąpił błąd po naciśnięciu przycisku „Wprowadź ponownie” (w class WidokPonownegoWprowadzania) dla użytkownika {interaction.user} (ID: {interaction.user.id}) na serwerze „{interaction.guild}” (ID: {interaction.id}). Więcej informacji: {e}"
			)
			with contextlib.suppress(Exception):
				await interaction.followup.send(
					"Wystąpił błąd podczas otwierania formularza. Spróbuj ponownie lub skontaktuj się z administratorem bota.",
					ephemeral=True
				)


class WidokAkceptacjiSugestii(discord.ui.View):
	"""
	Widok umożliwiający użytkownikowi akceptację lub ponowne wprowadzenie danych w formularzu konfiguracji dla serwera Discord.

	Attributes:
		typDanych (str): Typ danych do wprowadzenia (np. `klasy` lub `nauczyciele`).
		identyfikatorSerwera (str): ID serwera Discord, dla którego dane są zapisywane.
		idealneDopasowania (list[str]): Lista idealnych dopasowań wprowadzonych danych.
		sugestie (dict[str, str]): Propozycje dopasowania danych w formacie {oryginalne: sugestia}.
		listaDoDopasowania (list[str]): Lista elementów dostępnych do dopasowania.
		wiadomość (discord.Message): Wiadomość, w której widok jest wyświetlany.
		identyfikatorKanału (str): ID kanału tekstowego Discord, który został wybrany w opcjach polecenia.
		szkoła (str): ID szkoły, której dane przeznacza się do wykorzystania.
		timeout (float): Czas w sekundach, po którym widok wygasa (domyślnie 120.0).
	"""

	def __init__(
		self,
		typDanych: str,
		identyfikatorSerwera: str,
		idealneDopasowania: list[str],
		sugestie: dict[str, str],
		listaDoDopasowania: list[str],
		wiadomość: discord.Message,
		identyfikatorKanału: str,
		szkoła: str,
		timeout: float=120.0
	) -> None:
		super().__init__(timeout=timeout)
		self.typDanych = typDanych
		self.identyfikatorSerwera = identyfikatorSerwera
		self.idealneDopasowania = idealneDopasowania[:]
		self.sugestie = sugestie.copy()
		self.lista = listaDoDopasowania
		self.wiadomość = wiadomość
		self.identyfikatorKanału = identyfikatorKanału
		self.szkoła = szkoła

	@discord.ui.button(
		label="Akceptuj sugestie",
		style=discord.ButtonStyle.success
	)

	async def akceptujSugestie(
		self,
		interaction: discord.Interaction,
		button: discord.ui.Button
	) -> None:
		try:
			finalne = []

			for dopasowanie in self.idealneDopasowania:
				if dopasowanie not in finalne:
					finalne.append(dopasowanie)

			for sugestia in self.sugestie.values():
				if sugestia not in finalne:
					finalne.append(sugestia)

			if self.typDanych == "klasy":
				kluczFiltru = "wybrane-klasy"
			elif self.typDanych == "nauczyciele":
				kluczFiltru = "wybrani-nauczyciele"

			finalne = usuńDuplikaty(finalne)
			await zapiszKluczeSerwera(self.identyfikatorSerwera, {"identyfikator-kanalu": self.identyfikatorKanału, "szkoła": self.szkoła, kluczFiltru: finalne})
		except Exception as e:
			logiKonsoli.exception(
				f"Wystąpił błąd po naciśnięciu przycisku „Akceptuj sugestie” dla użytkownika {interaction.user} (ID: {interaction.user.id}) na serwerze „{interaction.guild}” (ID: {interaction.id}). Więcej informacji: {e}"
			)
			with contextlib.suppress(Exception):
				await interaction.followup.send(
					"Wystąpił błąd podczas akceptacji danych. Spróbuj ponownie lub skontaktuj się z administratorem bota.",
					ephemeral=True
				)

		embed = WidokPodsumowania.utwórz(str(interaction.guild.id))
		await interaction.response.edit_message(embed=embed, view=None)

	@discord.ui.button(
		label="Wprowadź ponownie",
		style=discord.ButtonStyle.secondary
	)

	async def wprowadźPonownie(
		self,
		interaction: discord.Interaction,
		button: discord.ui.Button
	) -> None:
		try:
			await interaction.response.send_modal(ModalWybierania(self.typDanych, self.lista, self.wiadomość, self.identyfikatorKanału, self.szkoła))
		except Exception as e:
			logiKonsoli.exception(
				f"Wystąpił błąd po naciśnięciu przycisku „Wprowadź ponownie” (w class WidokAkceptacjiSugestii) dla użytkownika {interaction.user} (ID: {interaction.user.id}) na serwerze „{interaction.guild}” (ID: {interaction.id}). Więcej informacji: {e}"
			)
			with contextlib.suppress(Exception):
				await interaction.followup.send(
					"Wystąpił błąd podczas otwierania formularza. Spróbuj ponownie lub skontaktuj się z administratorem bota.",
					ephemeral=True
				)


class ModalWybierania(discord.ui.Modal):
	"""
	Modal pozwalający użytkownikowi wprowadzić dane do formularza konfiguracji dla serwera Discord.

	Attributes:
		typDanych (str): Typ danych do wprowadzenia (np. `klasy` lub `nauczyciele`).
		listaDoDopasowania (list[str]): Lista elementów dostępnych do dopasowania.
		wiadomość (discord.Message): Wiadomość, w której widok jest wyświetlany.
		identyfikatorKanału (str): ID kanału tekstowego Discord, który został wybrany w opcjach polecenia.
		szkoła (str): ID szkoły, której dane przeznacza się do wykorzystania.
		pole (discord.ui.TextInput): Pole tekstowe w modalu do wprowadzania danych.
	"""

	def __init__(
		self,
		typDanych: str,
		listaDoDopasowania: list[str],
		wiadomość: discord.Message,
		identyfikatorKanału: str,
		szkoła: str
	) -> None:
		super().__init__(title="Wprowadź dane do formularza")
		self.typDanych = typDanych
		self.lista = listaDoDopasowania
		self.wiadomość = wiadomość
		self.identyfikatorKanału = identyfikatorKanału
		self.szkoła = szkoła

		if self.typDanych == "klasy":
			label = "Wprowadź klasy (oddzielaj przecinkami)."
			placeholder = "np. 1A, 2D, 3F"
		elif self.typDanych == "nauczyciele":
			label = "Wprowadź nauczycieli (oddzielaj przecinkami)."
			placeholder = "np. A. Kowalski, W. Nowak"

		self.pole = discord.ui.TextInput(
			label=label,
			style=discord.TextStyle.long,
			placeholder=placeholder,
		)
		self.add_item(self.pole)

	async def on_submit(
		self,
		interaction: discord.Interaction
	) -> None:
		try:
			identyfikatorSerwera = str(interaction.guild.id)
			suroweDane = self.pole.value
			wpisy = [element.strip() for element in re.split(r",|;", suroweDane) if element.strip()]
			idealneDopasowania, sugestie, nieZnaleziono = dopasujWpisyDoListy(wpisy, self.lista, cutoff=0.6)

			if nieZnaleziono:
				embed = discord.Embed(
					title="**Nie znaleziono wprowadzonych danych**",
					description=(
						"Nie znaleziono odpowiadających wpisów dla następujących danych:\n"
						+ "\n".join(f"- **{wprowadzoneDane}**" for wprowadzoneDane in nieZnaleziono)
						+ "\n\nSpróbuj ponownie, naciskając przycisk **Wprowadź ponownie**."
					),
					color=Constants.KOLOR
				)
				embed.set_footer(text=Constants.DŁUŻSZA_STOPKA)
				view = WidokPonownegoWprowadzania(self.typDanych, self.lista, self.wiadomość, self.identyfikatorKanału, self.szkoła)
				await interaction.response.defer()
				await self.wiadomość.edit(embed=embed, view=view)
				return

			if sugestie:
				opis = "**Proponowane dopasowania:**\n"

				for oryginalne, sugestia in sugestie.items():
					opis += f"- **{oryginalne}**  →  **{sugestia}**\n"

				opis += "\nJeśli akceptujesz propozycje, naciśnij przycisk **Akceptuj sugestie**. Jeśli chcesz wpisać ponownie, naciśnij przycisk **Wprowadź ponownie**."

				embed = discord.Embed(
					title="**Sugestie dopasowania wprowadzonych danych**",
					description=opis,
					color=Constants.KOLOR
				)
				embed.set_footer(text=Constants.DŁUŻSZA_STOPKA)
				view = WidokAkceptacjiSugestii(self.typDanych, identyfikatorSerwera, idealneDopasowania, sugestie, self.lista, self.wiadomość, self.identyfikatorKanału, self.szkoła)
				await interaction.response.defer()
				await self.wiadomość.edit(embed=embed, view=view)
				return

			if self.typDanych == "klasy":
				kluczFiltru = "wybrane-klasy"
			elif self.typDanych == "nauczyciele":
				kluczFiltru = "wybrani-nauczyciele"

			finalne = usuńDuplikaty(idealneDopasowania)
			await zapiszKluczeSerwera(identyfikatorSerwera, {"identyfikator-kanalu": self.identyfikatorKanału, "szkoła": self.szkoła, kluczFiltru: finalne})

			embed = WidokPodsumowania.utwórz(str(interaction.guild.id))
			await interaction.response.defer()
			await self.wiadomość.edit(embed=embed, view=None)
		except Exception as e:
			logiKonsoli.exception(
				f"Wystąpił błąd po naciśnięciu przycisku wysyłającego dane do zapisu (on_submit) dla użytkownika {interaction.user} (ID: {interaction.user.id}) na serwerze „{interaction.guild}” (ID: {interaction.id}). Więcej informacji: {e}"
			)
			with contextlib.suppress(Exception):
				await interaction.response.send_message(
					"Wystąpił błąd podczas przetwarzania danych. Spróbuj ponownie lub skontaktuj się z administratorem bota.",
					ephemeral=True
				)


class PrzyciskUczeń(discord.ui.Button):
	"""
	Przycisk umożliwiający użytkownikowi wprowadzenie klas w formularzu konfiguracji dla serwera Discord.

	Attributes:
		identyfikatorKanału (str): ID kanału tekstowego Discord, który został wybrany w opcjach polecenia.
		szkoła (str): ID szkoły, której dane przeznacza się do wykorzystania.
	"""

	def __init__(
		self,
		identyfikatorKanału: str,
		szkoła: str
	) -> None:
		super().__init__(
			label="Uczeń",
			style=discord.ButtonStyle.primary
		)
		self.identyfikatorKanału = identyfikatorKanału
		self.szkoła = szkoła

	async def callback(
		self,
		interaction: discord.Interaction
	) -> None:
		listaKlas = pobierzListęKlas(self.szkoła)
		if listaKlas == []:
			embed = discord.Embed(
				title="**Opcja niedostępna!**",
				description="Ta opcja nie jest dostępna w Twojej szkole. W razie pytań skontaktuj się z administratorem bota.",
				color=Constants.KOLOR
			)
			embed.set_footer(text=Constants.KRÓTSZA_STOPKA)
			await interaction.response.send_message(embed=embed, ephemeral=True)
		else:
			try:
				await interaction.response.send_modal(ModalWybierania("klasy", listaKlas, interaction.message, self.identyfikatorKanału, self.szkoła))
			except Exception as e:
				logiKonsoli.exception(
					f"Wystąpił błąd po naciśnięciu przycisku „Uczeń” dla użytkownika {interaction.user} (ID: {interaction.user.id}) na serwerze „{interaction.guild}” (ID: {interaction.id}). Więcej informacji: {e}"
				)
				with contextlib.suppress(Exception):
					await interaction.followup.send(
						"Wystąpił błąd podczas otwierania formularza. Spróbuj ponownie lub skontaktuj się z administratorem bota.",
						ephemeral=True
					)


class PrzyciskNauczyciel(discord.ui.Button):
	"""
	Przycisk umożliwiający użytkownikowi wprowadzenie nauczycieli w formularzu konfiguracji dla serwera Discord.

	Attributes:
		identyfikatorKanału (str): ID kanału tekstowego Discord, który został wybrany w opcjach polecenia.
		szkoła (str): ID szkoły, której dane przeznacza się do wykorzystania.
	"""

	def __init__(
		self,
		identyfikatorKanału: str,
		szkoła: str
	) -> None:
		super().__init__(
			label="Nauczyciel",
			style=discord.ButtonStyle.primary
		)
		self.identyfikatorKanału = identyfikatorKanału
		self.szkoła = szkoła

	async def callback(
		self,
		interaction: discord.Interaction
	) -> None:
		listaNauczycieli = konfiguracja.get("szkoły", {}).get(self.szkoła, {}).get("lista-nauczycieli", [])
		if listaNauczycieli == []:
			embed = discord.Embed(
				title="**Opcja niedostępna!**",
				description="Ta opcja nie jest dostępna w Twojej szkole. W razie pytań skontaktuj się z administratorem bota.",
				color=Constants.KOLOR
			)
			embed.set_footer(text=Constants.KRÓTSZA_STOPKA)
			await interaction.response.send_message(embed=embed, ephemeral=True)
		else:
			try:
				await interaction.response.send_modal(ModalWybierania("nauczyciele", listaNauczycieli, interaction.message, self.identyfikatorKanału, self.szkoła))
			except Exception as e:
				logiKonsoli.exception(
					f"Wystąpił błąd po naciśnięciu przycisku „Nauczyciel” dla użytkownika {interaction.user} (ID: {interaction.user.id}) na serwerze „{interaction.guild}” (ID: {interaction.id}). Więcej informacji: {e}"
				)
				with contextlib.suppress(Exception):
					await interaction.followup.send(
						"Wystąpił błąd podczas otwierania formularza. Spróbuj ponownie lub skontaktuj się z administratorem bota.",
						ephemeral=True
					)


class PrzyciskWyczyśćFiltry(discord.ui.Button):
	"""
	Przycisk umożliwiający użytkownikowi wyczyszczenie wszystkich filtrów w konfiguracji dla serwera Discord.
	"""

	def __init__(self) -> None:
		super().__init__(
			label="Wyczyść filtry",
			style=discord.ButtonStyle.danger
		)

	async def callback(
		self,
		interaction: discord.Interaction
	) -> None:
		try:
			identyfikatorSerwera = str(interaction.guild.id)
			await wyczyśćFiltry(identyfikatorSerwera)

			embed = discord.Embed(
				title="**Wyczyszczono konfigurację serwera**",
				description="Twój serwer nie będzie otrzymywał powiadomień z nowymi zastępstwami do czasu ponownej ich konfiguracji.",
				color=Constants.KOLOR
			)
			embed.set_footer(text=Constants.KRÓTSZA_STOPKA)
			await interaction.response.edit_message(embed=embed, view=None)
		except Exception as e:
			logiKonsoli.exception(
				f"Wystąpił błąd po naciśnięciu przycisku „Wyczyść filtry” dla użytkownika {interaction.user} (ID: {interaction.user.id}) na serwerze „{interaction.guild}” (ID: {interaction.id}). Więcej informacji: {e}"
			)
			with contextlib.suppress(Exception):
				await interaction.followup.send(
					"Wystąpił błąd podczas przetwarzania danych. Spróbuj ponownie lub skontaktuj się z administratorem bota.",
					ephemeral=True
				)


class WidokGłówny(discord.ui.View):
	"""
	Główny widok konfiguracyjny dla serwera Discord. Zostaje wyświetlony w momencie wywołania polecenia.

	Attributes:
		identyfikatorKanału (str): ID kanału tekstowego Discord, który został wybrany w opcjach polecenia.
		szkoła (str): ID szkoły, której dane przeznacza się do wykorzystania.
	"""

	def __init__(
		self,
		identyfikatorKanału: str,
		szkoła: str
	) -> None:
		super().__init__()
		self.add_item(PrzyciskUczeń(identyfikatorKanału, szkoła))
		self.add_item(PrzyciskNauczyciel(identyfikatorKanału, szkoła))
		self.add_item(PrzyciskWyczyśćFiltry())