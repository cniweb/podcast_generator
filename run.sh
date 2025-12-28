#!/bin/bash

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. PARAMETER CHECK (Das Thema muss übergeben werden)
if [ -z "$1" ]; then
    echo -e "${RED}Fehler: Kein Thema angegeben!${NC}"
    echo -e "Nutzung: ./run.sh \"Dein Thema\""
    echo -e "Beispiel: ./run.sh \"Schwarze Löcher\""
    exit 1
fi

TOPIC="$1"
SCRIPT_FILE="podcast_generator.py"
ENV_FILE=".env"

# 2. DATEI CHECK
if [ ! -f "$SCRIPT_FILE" ]; then
    echo -e "${RED}Fehler: $SCRIPT_FILE nicht gefunden.${NC}"
    exit 1
fi

# 3. ENV CHECK (API Keys und Pfade)
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Fehler: $ENV_FILE fehlt. Bitte aus Vorlage anlegen und Keys eintragen.${NC}"
    exit 1
fi

set -a
source "$ENV_FILE"
set +a

for var in GEMINI_API_KEY PIXABAY_API_KEY GOOGLE_APPLICATION_CREDENTIALS; do
    value=${!var}
    if [ -z "$value" ] || [[ "$value" == your_* ]]; then
        echo -e "${RED}Fehler: $var ist nicht gesetzt oder noch Platzhalter.${NC}"
        exit 1
    fi
done

if [ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo -e "${YELLOW}Warnung: GOOGLE_APPLICATION_CREDENTIALS Datei wurde unter '$GOOGLE_APPLICATION_CREDENTIALS' nicht gefunden.${NC}"
    echo -e "${YELLOW}Stelle sicher, dass der Pfad im .env korrekt ist.${NC}"
fi

# 4. VIRTUAL ENVIRONMENT (.venv) SETUP
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Erstelle virtuelles Python-Environment (.venv)...${NC}"
    python3 -m venv .venv
fi

# Aktivieren des Environments
source .venv/bin/activate
echo -e "${GREEN}✓ Virtual Environment aktiviert.${NC}"

# 5. ABHÄNGIGKEITEN PRÜFEN (setup.sh aufrufen)
# Wir machen setup.sh ausführbar, falls es das noch nicht ist
if [ -f "setup.sh" ]; then
    chmod +x setup.sh
    # Wir führen setup.sh aus. Da wir im venv sind, nutzt es das pip des venvs.
    ./setup.sh
    if [ $? -ne 0 ]; then
        echo -e "${RED}Setup fehlgeschlagen. Breche ab.${NC}"
        deactivate
        exit 1
    fi
else
    echo -e "${RED}Warnung: setup.sh nicht gefunden. Versuche manuelle Installation...${NC}"
    pip install -r requirements.txt || { echo -e "${RED}pip install fehlgeschlagen.${NC}"; deactivate; exit 1; }
fi

# 6. PROGRAMM STARTEN
echo -e "\n${GREEN}🚀 Starte Gehirntakko Generator mit Thema: '$TOPIC'${NC}"
echo "------------------------------------------------"

# Wir pipen das Thema direkt in das Python-Skript, da dieses 'input()' verwendet.
echo "$TOPIC" | python3 "$SCRIPT_FILE"

# Deaktivieren (optional, da Skript hier endet)
deactivate