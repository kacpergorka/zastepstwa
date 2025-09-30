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

# Zewnętrzne biblioteki
import discord

# Wewnętrzne importy
from src.classes.constants import Constants
from src.handlers.logging import logiKonsoli
from src.helpers.helpers import (
	ograniczReagowanie,
	ograniczUsuwanie,
	ograniczWysyłanie
)

async def wyślijAktualizacje(
	kanał: discord.TextChannel,
	identyfikatorSerwera: int,
	informacjeDodatkowe: str,
	aktualneWpisyZastępstw: list[tuple[str, list[str]]],
	aktualnyCzas: str
) -> None:
	"""
	Wysyła aktualizacje zastępstw do konkretnego kanału tekstowego Discord.

	Args:
		kanał (discord.TextChannel): Kanał tekstowy Discord, na który zostaną wysłane wiadomości.
		identyfikatorSerwera (int): ID serwera Discord.
		informacjeDodatkowe (str): Tekst informacji dodatkowych nad zastępstwami.
		aktualneWpisyZastępstw (list[tuple[str, list[str]]]): Lista zastępstw.
		aktualnyCzas (str): Aktualny czas, używany w stopce wiadomości.
	"""

	opisTylkoDlaInformacjiDodatkowych = (
		"**Informacje dodatkowe zastępstw:**"
		f"\n{informacjeDodatkowe}"
		"\n\n**Informacja o tej wiadomości:**"
		"\nTa wiadomość zawiera informacje dodatkowe umieszczone nad zastępstwami. Nie znaleziono dla Ciebie żadnych zastępstw pasujących do Twoich filtrów."
	)
	opisDlaInformacjiDodatkowych = (
		"**Informacje dodatkowe zastępstw:**"
		f"\n{informacjeDodatkowe}"
		"\n\n**Informacja o tej wiadomości:**"
		"\nTa wiadomość zawiera informacje dodatkowe umieszczone nad zastępstwami. Wszystkie zastępstwa znajdują się pod tą wiadomością."
	)
	treśćStopkiInformacjiDodatkowych = f"Czas aktualizacji: {aktualnyCzas}\n{Constants.KRÓTSZA_STOPKA}"

	try:
		ostatniaWiadomość = None
		if informacjeDodatkowe and not aktualneWpisyZastępstw:
			embed = discord.Embed(
				title="**Zastępstwa zostały zaktualizowane!**",
				description=opisTylkoDlaInformacjiDodatkowych,
				color=Constants.KOLOR
			)
			embed.set_footer(text=treśćStopkiInformacjiDodatkowych)
			await ograniczWysyłanie(kanał, embed=embed)

		elif (informacjeDodatkowe and aktualneWpisyZastępstw) or (aktualneWpisyZastępstw):
			if kanał.permissions_for(kanał.guild.me).mention_everyone:
				wzmianka = await ograniczWysyłanie(kanał, "@everyone Zastępstwa zostały zaktualizowane!", allowed_mentions=discord.AllowedMentions(everyone=True))
				await asyncio.sleep(5)
				try:
					await ograniczUsuwanie(wzmianka)
				except Exception:
					pass
			else:
				logiKonsoli.warning(
					f"Brak uprawnień do używania @everyone dla serwera o ID {identyfikatorSerwera}. Wzmianka została pominięta."
				)

			embed = discord.Embed(
				title="**Zastępstwa zostały zaktualizowane!**",
				description=opisDlaInformacjiDodatkowych,
				color=Constants.KOLOR
			)
			embed.set_footer(text=treśćStopkiInformacjiDodatkowych)
			await ograniczWysyłanie(kanał, embed=embed)

			tytuł = ""
			for tytuł, wpisyZastępstw in aktualneWpisyZastępstw:
				if "Zastępstwa z nieprzypisanymi klasami!" in tytuł:
					tekstZastępstw = (
						"\n\n".join(wpisyZastępstw)
						+ "\n\n**Informacja o tej wiadomości:**"
						+ "\nTe zastępstwa nie posiadają dołączonej klasy, więc zweryfikuj czy przypadkiem nie dotyczą one Ciebie!"
					)
				else:
					tekstZastępstw = "\n\n".join(wpisyZastępstw)

				embed = discord.Embed(
					title=f"**{tytuł}**",
					description=tekstZastępstw,
					color=Constants.KOLOR
				)

				if not "Zastępstwa z nieprzypisanymi klasami!" in tytuł:
					embed.set_footer(text="Każdy nauczyciel, którego dotyczą zastępstwa pasujące do Twoich filtrów, zostanie załączany w oddzielnej wiadomości.")
				else:
					embed.set_footer(text="Każdy nauczyciel, którego dotyczą zastępstwa bez dołączonej klasy, został załączony w tej wiadomości.")

				ostatniaWiadomość = await ograniczWysyłanie(kanał, embed=embed)

		if ostatniaWiadomość and not "Zastępstwa z nieprzypisanymi klasami!" in tytuł:
			await ograniczReagowanie(ostatniaWiadomość, "❤️")

	except discord.DiscordException as e:
		logiKonsoli.exception(
			f"Wystąpił błąd podczas wysyłania wiadomości do serwera o ID {identyfikatorSerwera}. Więcej informacji: {e}"
		)
	except Exception as e:
		logiKonsoli.exception(
			f"Wystąpił nieoczekiwany błąd podczas wysyłania wiadomości do serwera o ID {identyfikatorSerwera}. Więcej informacji: {e}"
		)