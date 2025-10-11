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
from datetime import datetime
from zoneinfo import ZoneInfo

# Zewnętrzne biblioteki
import discord

# Wewnętrzne importy
from src.classes.constants import Constants
from src.handlers.configuration import konfiguracja
from src.handlers.logging import (
	logiKonsoli,
	logujPolecenia
)

def ustaw(bot: discord.Client) -> None:
	"""
	Rejestruje polecenie `/informacje` w drzewie bota.

	Args:
		bot (discord.Client): Instancja klienta Discord, do której dodawane jest polecenie.
	"""

	@bot.tree.command(
		name="informacje",
		description="Wyświetl najważniejsze informacje dotyczące bota, jego oprogramowania i administratorów"
	)

	async def informacje(interaction: discord.Interaction) -> None:
		"""
		Wyświetla najważniejsze informacje dotyczące bota, jego oprogramowania i administratorów.

		Args:
			interaction (discord.Interaction): Obiekt interakcji wywołujący polecenie.
		"""

		try:
			embed = discord.Embed(
				title="**Informacje dotyczące bota**",
				description="Otwartoźródłowe oprogramowanie informujące o aktualizacjach zastępstw. W celu skontaktowania się z jednym z administratorów bota, naciśnij jednego z poniżej widniejących. Nastąpi przekierowanie na zewnętrzną stronę internetową.",
				color=Constants.KOLOR
			)
			embed.add_field(
				name="Wersja bota:",
				value=konfiguracja.get("wersja", "Brak danych")
			)
			embed.add_field(
				name="Repozytorium GitHuba:",
				value=("[kacpergorka/zastepstwa](https://github.com/kacpergorka/zastepstwa)")
			)
			embed.add_field(
				name="Administratorzy bota:",
				value="[Kacper Górka](https://kacpergorka.com/)"
			)

			if len(bot.guilds) == 1:
				embed.add_field(
					name="Liczba serwerów:",
					value=(f"Bot znajduje się na **{len(bot.guilds)}** serwerze.")
				)
			else:
				embed.add_field(
					name="Liczba serwerów:",
					value=(f"Bot znajduje się na **{len(bot.guilds)}** serwerach.")
				)

			czasDziałania = datetime.now(ZoneInfo("Europe/Warsaw")) - bot.czas
			dni, reszta = divmod(czasDziałania.total_seconds(), 86400)
			godziny, reszta = divmod(reszta, 3600)
			minuty, sekundy = divmod(reszta, 60)

			embed.add_field(
				name="Bot pracuje bez przerwy przez:",
				value=f"**{int(dni)}** dni, **{int(godziny)}** godz., **{int(minuty)}** min. i **{int(sekundy)}** sek."
			)
			embed.set_footer(text=Constants.DŁUŻSZA_STOPKA)
			await interaction.response.send_message(embed=embed)
			logujPolecenia(interaction, sukces=True)
		except Exception as e:
			logujPolecenia(interaction, sukces=False, wiadomośćBłędu=str(e))
			logiKonsoli.exception(
				f"Wystąpił błąd podczas wywołania polecenia „/informacje”. Więcej informacji: {e}"
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