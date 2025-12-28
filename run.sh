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

# 2. DATEI CHECK
if [ ! -f "$SCRIPT_FILE" ]; then
    echo -e "${RED}Fehler: $SCRIPT_FILE nicht gefunden.${NC}"
    exit 1
fi

# 3. API KEY VALIDIERUNG (Pre-Flight Check)
# Wir prüfen, ob noch die Platzhalter im Python-Skript stehen
if grep -q "DEIN_GEMINI_API_KEY" "$SCRIPT_FILE" || grep -q "DEIN_PIXABAY_API_KEY" "$SCRIPT_FILE"; then
    echo -e "${RED}ACHTUNG: Es scheinen noch Platzhalter für API-Keys in $SCRIPT_FILE zu sein.${NC}"
    echo -e "Bitte bearbeite die Datei und trage deine echten Keys ein, bevor du startest."
    exit 1
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
else
    echo -e "${RED}Warnung: setup.sh nicht gefunden. Versuche manuelle Installation...${NC}"
    pip install -r requirements.txt
fi

# 6. PROGRAMM STARTEN
echo -e "\n${GREEN}🚀 Starte Gehirntakko Generator mit Thema: '$TOPIC'${NC}"
echo "------------------------------------------------"

# Wir pipen das Thema direkt in das Python-Skript, da dieses 'input()' verwendet.
echo "$TOPIC" | python3 "$SCRIPT_FILE"

# Deaktivieren (optional, da Skript hier endet)
deactivate