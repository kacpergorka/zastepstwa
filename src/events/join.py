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

# Zewnętrzne biblioteki
import discord

# Wewnętrzne importy
from src.classes.constants import Constants
from src.handlers.logging import logiKonsoli
from src.helpers.helpers import ograniczWysyłanie

def ustaw(bot: discord.Client) -> None:
	"""
	Rejestruje event `on_guild_join` w drzewie bota.

	Args:
		bot (discord.Client): Instancja klienta Discord, do której dodawany jest event.
	"""

	@bot.event
	async def on_guild_join(guild: discord.Guild) -> None:
		"""
		Event wywoływany po dodaniu bota do serwera Discord. Wysyła embed z instrukcjami konfiguracji oprogramowania.

		Args:
			guild (discord.Guild): Serwer Discord, na który bot został dodany.
		"""

		dostarczono = False
		dalszaCzęśćOpisu = (
			"Wszystkie ważne informacje dotyczące bota oraz jego administratorów znajdziesz, używając polecenia `/informacje`."
			"\n\n**Konfiguracja bota**"
			"\nKonfiguracja bota zaczyna się od utworzenia dedykowanego kanału tekstowego, na który po konfiguracji będą wysyłane zastępstwa, a następnie użycia polecenia `/skonfiguruj`, gdzie przejdziesz przez wygodny i intuicyjny konfigurator."
			"\n\n**Utrzymanie bota**"
			"\nJeśli napotkasz jakikolwiek błąd lub chcesz zgłosić swoją propozycję, [utwórz zgłoszenie w zakładce `Issues`](https://github.com/kacpergorka/zastepstwa/issues). Jest to bardzo ważne dla prawidłowego funkcjonowania bota!"
		)

		try:
			async for wpis in guild.audit_logs(limit=1, action=discord.AuditLogAction.bot_add):
				dodający = wpis.user

				try:
					embed = discord.Embed(
						description=(
							"**Informacja wstępna**"
							+ f"\nBot został dodany do serwera **{guild.name}**, a ponieważ jesteś administratorem, który go dodał, otrzymujesz tę wiadomość. "
							+ dalszaCzęśćOpisu
						),
						color=Constants.KOLOR
					)
					embed.set_footer(text=Constants.DŁUŻSZA_STOPKA)
					await dodający.send(embed=embed)

					dostarczono = True
					logiKonsoli.info(
						f"Wiadomość z instrukcjami została wysłana do {dodający.name} o ID {dodający.id}, który dodał bota na serwer {guild.name} o ID {guild.id}."
					)
					return
				except discord.Forbidden as e:
					logiKonsoli.warning(
						f"Nie można wysłać wiadomości z instrukcjami do {dodający.name} o ID {dodający.id}, który dodał bota na serwer {guild.name} o ID {guild.id}. Więcej informacji: {e}"
					)
		except discord.Forbidden:
			logiKonsoli.warning(
				f"Brak uprawnień do odczytu logów audytu na serwerze {guild.name} o ID {guild.id}."
			)
		except Exception as e:
			logiKonsoli.exception(
				f"Wystąpił błąd przy próbie odczytu logów audytu na serwerze {guild.name} o ID {guild.id}. Więcej informacji: {e}"
			)

		if not dostarczono:
			kanał = guild.system_channel or next((kanał for kanał in guild.text_channels if kanał.permissions_for(guild.me).send_messages), None)
			if kanał:
				try:
					embed = discord.Embed(
						description=(
							"**Informacja wstępna**"
							+ f"\nBot został dodany do serwera **{guild.name}**, a ponieważ administrator, który dodał bota na serwer nie ma włączonych wiadomości prywatnych, to wiadomość ta zostaje dostarczona na serwer. "
							+ dalszaCzęśćOpisu
						),
						color=Constants.KOLOR
					)
					embed.set_footer(text=Constants.DŁUŻSZA_STOPKA)
					await ograniczWysyłanie(kanał, embed=embed)

					logiKonsoli.info(
						f"Wiadomość z instrukcjami została wysłana na kanał #{kanał.name} o ID {kanał.id} na serwerze {guild.name} o ID {guild.id}, ponieważ żaden administrator nie odebrał prywatnej wiadomości."
					)
				except discord.DiscordException as e:
					logiKonsoli.exception(
						f"Nie można wysłać wiadomości z instrukcjami na serwer {guild.name} o ID {guild.id}. Więcej informacji: {e}"
					)
			else:
				logiKonsoli.warning(
					f"Nie znaleziono kanału tekstowego na serwerze {guild.name} o ID {guild.id}. Wiadomość z instrukcjami nie została dostarczona."
				)