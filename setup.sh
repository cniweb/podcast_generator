#!/bin/bash

# Farben für die Ausgabe
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}--- Gehirntakko Setup Assistent ---${NC}"

# 1. Prüfen ob Python3 installiert ist
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Fehler: Python 3 ist nicht installiert.${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Python 3 gefunden.${NC}"
fi

# 2. FFmpeg Prüfung und Installation (MacOS/Linux)
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${YELLOW}FFmpeg nicht gefunden. Versuche Installation...${NC}"

    OS="$(uname -s)"
    if [ "$OS" = "Darwin" ]; then
        # MacOS
        if command -v brew &> /dev/null; then
            echo "Nutze Homebrew..."
            brew install ffmpeg
        elif command -v port &> /dev/null; then
            echo "Nutze MacPorts (Sudo erforderlich)..."
            sudo port install ffmpeg
        else
            echo -e "${RED}Weder Homebrew noch MacPorts gefunden. Bitte installiere FFmpeg manuell.${NC}"
            exit 1
        fi
    elif [ "$OS" = "Linux" ]; then
        # Linux (Debian/Ubuntu)
        if command -v apt-get &> /dev/null; then
            echo "Nutze apt-get (Sudo erforderlich)..."
            sudo apt-get update && sudo apt-get install -y ffmpeg
        else
             echo -e "${RED}Konnte Paketmanager nicht bestimmen. Bitte installiere FFmpeg manuell.${NC}"
             exit 1
        fi
    else
        echo -e "${RED}Unbekanntes Betriebssystem. Bitte installiere FFmpeg manuell.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ FFmpeg gefunden.${NC}"
fi

# 3. Python Abhängigkeiten installieren
if [ -f "requirements.txt" ]; then
    echo -e "${YELLOW}Installiere Python Abhängigkeiten...${NC}"
    pip3 install -r requirements.txt
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Abhängigkeiten installiert.${NC}"
    else
        echo -e "${RED}Fehler beim Installieren der Abhängigkeiten.${NC}"
        exit 1
    fi
else
    echo -e "${RED}Fehler: requirements.txt nicht gefunden.${NC}"
    exit 1
fi

# 4. Ordnerstruktur erstellen (Sicherheitshalber)
mkdir -p temp_assets
mkdir -p fertige_episoden

# 5. Abschluss und API Key Check
echo -e "\n${GREEN}--- Installation abgeschlossen! ---${NC}"
echo -e "${YELLOW}Erinnerung: Bitte stelle sicher, dass du folgende Schritte erledigt hast:${NC}"
echo "1. API Key für Gemini in 'podcast_generator.py' eintragen."
echo "2. API Key für Pixabay in 'podcast_generator.py' eintragen."
echo "3. Die Datei 'google_cloud_credentials.json' muss im selben Ordner liegen."
echo -e "\nDu kannst das Programm nun starten mit: ${GREEN}python3 podcast_generator.py${NC}"