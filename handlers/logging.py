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
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# Zewnętrzne biblioteki
import discord

# Wewnętrzne importy
from classes.timezone import Timezone

def skonfigurujLogi() -> tuple[logging.Logger, logging.Logger]:
	"""
	Konfiguruje globalne logowanie wydarzeń konsoli (`logiKonsoli`) i poleceń (`logiPoleceń`).

	Returns:
		tuple[logging.Logger, logging.Logger]: Logger konsoli `(logiKonsoli)` i logger poleceń `(logiPoleceń)`.
	"""

	folderLogów = Path("logs")
	folderLogów.mkdir(exist_ok=True)

	logiKonsoli = logging.getLogger("discord")
	logiKonsoli.setLevel(logging.INFO)

	logiPoleceń = logging.getLogger("discord.commands")
	logiPoleceń.setLevel(logging.INFO)

	ścieżkaLogów = folderLogów / "console.log"

	obsługaLogów = RotatingFileHandler(
		filename=ścieżkaLogów,
		encoding="utf-8",
		maxBytes=32 * 1024 * 1024,
		backupCount=31
	)

	formatter = Timezone("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
	obsługaLogów.setFormatter(formatter)

	logiKonsoli.addHandler(obsługaLogów)
	logiPoleceń.addHandler(obsługaLogów)
	logiPoleceń.propagate = False

	return logiKonsoli, logiPoleceń

logiKonsoli, logiPoleceń = skonfigurujLogi()


def logujPolecenia(
	interaction: discord.Interaction,
	sukces: bool,
	wiadomośćBłędu: Optional[str] = None
) -> None:
	"""
	Konfiguruje logowanie wykonywanych poleceń wraz z wszystkimi przydatnymi informacjami o interakcji.

	Args:
		interaction (discord.Interaction): Obiekt interakcji wywołanej przez użytkownika.
		sukces (bool): Informuje, czy polecenie zostało wykonane pomyślnie.
		wiadomośćBłędu (str, optional): Wiadomość błędu w przypadku niepowodzenia polecenia.
	"""

	status = "pomyślnie" if sukces else "niepomyślnie"
	informacjaBłędu = (
		f" ({wiadomośćBłędu})"
		if wiadomośćBłędu else ""
	)
	opcje = (
		getattr(interaction, "data", {}).get("options", [])
		if interaction else []
	)
	użyteArgumenty = (
		"Użyte argumenty: " + ", ".join(f"{opcja.get('name', '')} ({opcja.get('value', '')})" for opcja in opcje) + ". "
		if opcje else ""
	)

	try:
		if getattr(interaction, "guild", None):
			miejsce = (
				f"na serwerze „{interaction.guild.name}” (ID: {interaction.guild.id}) "
				f"na kanale tekstowym #{getattr(interaction.channel, 'name', 'N/A')} (ID: {getattr(interaction.channel, 'id', 'N/A')}). "
			)
		else:
			miejsce = "w wiadomości prywatnej. "
	except Exception:
		miejsce = ""

	nazwaPolecenia = getattr(
		getattr(interaction, "command", None), "name", getattr(interaction, "command_name", "Brak nazwy")
	)
	użytkownik = f"{getattr(interaction, 'user', 'Nieznany użytkownik')}"
	identyfikatorUżytkownika = getattr(getattr(interaction, "user", None), "id", "Brak ID")
	wiadomośćLogu = (
		f"Użytkownik: {użytkownik} (ID: {identyfikatorUżytkownika}) "
		f"wywołał polecenie „{nazwaPolecenia}” "
		f"{miejsce}"
		f"{użyteArgumenty}"
		f"Polecenie wykonane {status}.{informacjaBłędu}"
	)
	logiPoleceń.info(wiadomośćLogu)