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

# Zewnętrzne biblioteki
import discord

# Wewnętrzne importy
from src.classes.constants import Constants
from src.handlers.configuration import (
	blokadaKonfiguracji,
	konfiguracja
)
from src.handlers.data import zarządzajPlikiemDanych
from src.handlers.logging import (
	logiKonsoli,
	logujPolecenia
)
from src.helpers.helpers import (
	odmieńZastępstwa,
	zwróćNazwyKluczy
)

def ustaw(bot: discord.Client) -> None:
	"""
	Rejestruje polecenie `/statystyki` w drzewie bota.

	Args:
		bot (discord.Client): Instancja klienta Discord, do której dodawane jest polecenie.
	"""

	@bot.tree.command(
		name="statystyki",
		description="Wyświetl bieżące statystyki dostarczonych zastępstw w aktualnym roku szkolnym."
	)
	@discord.app_commands.guild_only()

	async def statystyki(interaction: discord.Interaction) -> None:
		"""
		Wyświetla bieżące statystyki dostarczonych zastępstw w aktualnym roku szkolnym.

		Args:
			interaction (discord.Interaction): Obiekt interakcji wywołujący polecenie.
		"""

		try:
			identyfikatorSerwera = str(interaction.guild.id)
			dane = await zarządzajPlikiemDanych(identyfikatorSerwera)

			if not isinstance(dane, dict):
				dane = {}

			licznik = int(dane.get("licznik-zastepstw", 0))
			statystyki = dane.get("statystyki-nauczycieli", {})

			async with blokadaKonfiguracji:
				konfiguracjaSerwera = konfiguracja.get("serwery", {}).get(identyfikatorSerwera, {}).copy()

			wybraniNauczyciele = konfiguracjaSerwera.get("wybrani-nauczyciele", [])
			wybraneKlasy = konfiguracjaSerwera.get("wybrane-klasy", [])

			if licznik == 0:
				embed = discord.Embed(
					title="**Statystyki zastępstw**",
					description="Dla tego serwera od rozpoczęcia roku szkolnego nie odnotowano jeszcze żadnych zastępstw.",
					color=Constants.KOLOR
				)
				embed.set_footer(text=Constants.DŁUŻSZA_STOPKA)
				await interaction.response.send_message(embed=embed)
				return

			if wybraneKlasy and not wybraniNauczyciele:
				embed = discord.Embed(
					title="**Statystyki zastępstw**",
					description=(
						f"Dla tego serwera od rozpoczęcia roku szkolnego dostarczono **{licznik}** {odmieńZastępstwa(licznik)}! "
						"Poniżej znajduje się lista nauczycieli z największą liczbą zarejestrowanych zastępstw."
					),
					color=Constants.KOLOR
				)

				if isinstance(statystyki, dict) and statystyki:
					sortowanie = sorted(statystyki.items(), key=lambda x: (-int(x[1]), x[0]))
					wolneMiejsca = 25 - len(embed.fields)

					if wolneMiejsca > 0:
						for nauczyciel, liczba in sortowanie[:wolneMiejsca]:
							embed.add_field(
								name=str(nauczyciel),
								value=f"Liczba zastępstw: {int(liczba)}",
								inline=True
							)
				embed.set_footer(text=Constants.DŁUŻSZA_STOPKA)
				await interaction.response.send_message(embed=embed)

			elif wybraniNauczyciele:
				embed = discord.Embed(
					title="**Statystyki zastępstw**",
					description=(
						f"Dla tego serwera od rozpoczęcia roku szkolnego dostarczono **{licznik}** {odmieńZastępstwa(licznik)}! "
						"Poniżej znajduje się lista nauczycieli z największą liczbą zarejestrowanych zastępstw. (Pominięto nauczycieli ustawionych w filtrze)."
					),
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
					wolneMiejsca = 25 - len(embed.fields)

					if wolneMiejsca > 0:
						for nauczyciel, liczba in sortowanie[:wolneMiejsca]:
							embed.add_field(
								name=str(nauczyciel),
								value=f"Liczba zastępstw: {int(liczba)}",
								inline=True
							)
				else:
					embed.add_field(
						name="Brak danych",
						value="Nie znaleziono odpowiednich statystyk dla tego serwera.",
						inline=False
					)
				embed.set_footer(text=Constants.DŁUŻSZA_STOPKA)
				await interaction.response.send_message(embed=embed)

			else:
				if not wybraneKlasy and not wybraniNauczyciele:
					embed = discord.Embed(
						title="**Polecenie nie zostało wykonane!**",
						description="Aby wykonać to polecenie, poproś administratora o skonfigurowanie zastępstw. Jesteś administratorem? Użyj polecenia `/skonfiguruj` i postępuj zgodnie z instrukcjami.",
						color=Constants.KOLOR
					)
					embed.set_footer(text=Constants.KRÓTSZA_STOPKA)
					await interaction.response.send_message(embed=embed, ephemeral=True)
					logujPolecenia(interaction, sukces=False, wiadomośćBłędu="Zastępstwa nie zostały skonfigurowane.")
					return

			logujPolecenia(interaction, sukces=True)
		except Exception as e:
			logujPolecenia(interaction, sukces=False, wiadomośćBłędu=str(e))
			logiKonsoli.exception(
				f"Wystąpił błąd podczas wywołania polecenia „/statystyki”. Więcej informacji: {e}"
			)
			with contextlib.suppress(Exception):
				if not interaction.response.is_done():
					await interaction.response.send_message(
						"Wystąpił błąd. Spróbuj ponownie lub skontaktuj się z administratorem bota.",
						ephemeral=True
					)
				else:
					await interaction.followup.send(
						"Wystąpił błąd. Spróbuj ponownie lub skontaktuj się z administratorem bota.",
						ephemeral=True
					)