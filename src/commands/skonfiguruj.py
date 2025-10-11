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
from src.classes.commands import WidokGłówny
from src.classes.constants import Constants
from src.handlers.configuration import konfiguracja
from src.handlers.logging import (
	logiKonsoli,
	logujPolecenia
)

def ustaw(bot: discord.Client) -> None:
	"""
	Rejestruje polecenie `/skonfiguruj` w drzewie bota.

	Args:
		bot (discord.Client): Instancja klienta Discord, do której dodawane jest polecenie.
	"""

	@bot.tree.command(
		name="skonfiguruj",
		description="Skonfiguruj bota, wybierając szkołę, docelowy kanał tekstowy i filtry zastępstw."
	)
	@discord.app_commands.describe(
		kanał="Kanał tekstowy, na który będą wysyłane powiadomienia z zastępstwami.",
		szkoła="Szkoła, z której to strony będą pobierane informacje o zastępstwach."
	)
	@discord.app_commands.guild_only()
	@discord.app_commands.choices(
		szkoła=[
			discord.app_commands.Choice(
				name=nazwaSzkoły.get("nazwa", identyfikatorSzkoły),
				value=str(identyfikatorSzkoły)
			)
			for identyfikatorSzkoły, nazwaSzkoły in konfiguracja.get("szkoły", {}).items()
		]
	)

	async def skonfiguruj(
		interaction: discord.Interaction,
		szkoła: str,
		kanał: discord.TextChannel
	) -> None:
		"""
		Pozwala skonfigurować bota, dzięki opcjom wyboru szkoły, docelowego kanału tekstowego i filtracji zastępstw.

		Args:
			interaction (discord.Interaction): Obiekt interakcji wywołujący polecenie.
		"""

		try:
			if not interaction.user.guild_permissions.administrator:
				embed = discord.Embed(
					title="**Polecenie nie zostało wykonane!**",
					description="Nie masz uprawnień do użycia tego polecenia. Może ono zostać użyte wyłącznie przez administratora serwera.",
					color=Constants.KOLOR
				)
				embed.set_footer(text=Constants.KRÓTSZA_STOPKA)
				await interaction.response.send_message(embed=embed, ephemeral=True)
				logujPolecenia(interaction, sukces=False, wiadomośćBłędu="Brak uprawnień.")
				return

			view = WidokGłówny(identyfikatorKanału=str(kanał.id), szkoła=szkoła)
			embed = discord.Embed(
				title="**Skonfiguruj filtrowanie zastępstw**",
				description=(
					"**Jesteś uczniem?**"
					"\nAby dostawać powiadomienia z nowymi zastępstwami przypisanymi Twojej klasie, naciśnij przycisk **Uczeń**."
					"\n\n**Jesteś nauczycielem?**"
					"\nAby dostawać powiadomienia z nowymi zastępstwami przypisanymi Tobie, naciśnij przycisk **Nauczyciel**."
					"\n\nAby wyczyścić wszystkie ustawione filtry, naciśnij przycisk **Wyczyść filtry**."
				),
				color=Constants.KOLOR
			)
			embed.set_footer(text=Constants.DŁUŻSZA_STOPKA)
			await interaction.response.send_message(embed=embed, view=view)
			logujPolecenia(interaction, sukces=True)
		except Exception as e:
			logujPolecenia(interaction, sukces=False, wiadomośćBłędu=str(e))
			logiKonsoli.exception(
				f"Wystąpił błąd podczas wywołania polecenia „/skonfiguruj”. Więcej informacji: {e}"
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