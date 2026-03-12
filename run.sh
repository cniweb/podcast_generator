#!/bin/bash
# Startskript: validiert .env, richtet venv ein und startet podcast_generator.

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. PARAMETER (Thema optional; wenn leer -> Trends) und Hilfe
RESUME_FLAG=""
FORCE_RESTART_FLAG=""
TOPIC=""

while [ $# -gt 0 ]; do
    case "$1" in
        --help|-h)
            echo "Nutzung: ./run.sh [--resume|--force-restart] [Thema]"
            echo "Beispiel: ./run.sh --resume \"Schwarze Löcher\""
            echo "Beispiel: ./run.sh --force-restart \"Schwarze Löcher\""
            echo "Ohne Thema wird der aktuelle Top-Trend aus Google Trends (Deutschland) genutzt."
            exit 0
            ;;
        --resume)
            RESUME_FLAG="--resume"
            ;;
        --force-restart)
            FORCE_RESTART_FLAG="--force-restart"
            ;;
        *)
            if [ -n "$TOPIC" ]; then
                echo -e "${RED}Fehler: Mehrere Themen wurden uebergeben. Bitte Thema in Anfuehrungszeichen setzen.${NC}"
                exit 1
            fi
            TOPIC="$1"
            ;;
    esac
    shift
done

if [ -n "$RESUME_FLAG" ] && [ -n "$FORCE_RESTART_FLAG" ]; then
    echo -e "${RED}Fehler: --resume und --force-restart koennen nicht kombiniert werden.${NC}"
    exit 1
fi

SCRIPT_FILE="podcast_generator.py"
ENV_FILE=".env"
PYTHON_BIN=${PYTHON_BIN:-python3}

# Bevor wir das venv bauen: bevorzugt Python 3.12 (audioop vorhanden)
if command -v python3.12 >/dev/null 2>&1; then
    PYTHON_BIN=python3.12
fi

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

required_vars=(GEMINI_API_KEY FREESOUND_API_KEY GOOGLE_APPLICATION_CREDENTIALS PODCAST_NAME PODCAST_SLOGAN SCRIPT_DEFAULT_MODEL PODCAST_TEMP_DIR PODCAST_OUTPUT_DIR PODCAST_ASSETS_DIR)
for var in "${required_vars[@]}"; do
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

# 3b. Prüfen ob audioop Modul verfügbar (oder via audioop-lts installiert)
if ! $PYTHON_BIN - <<'PY'
import importlib.util
import sys
sys.exit(0 if importlib.util.find_spec('audioop') else 1)
PY
then
    echo -e "${YELLOW}Hinweis: 'audioop' fehlt in ${PYTHON_BIN}. Wir installieren 'audioop-lts' über requirements.txt.${NC}"
fi

# 3c. Ordner sicherstellen; Temp leeren, Output behalten
mkdir -p "$PODCAST_TEMP_DIR" "$PODCAST_OUTPUT_DIR"
if [ -n "$FORCE_RESTART_FLAG" ]; then
    echo -e "${YELLOW}Leere $PODCAST_TEMP_DIR fuer kompletten Neustart...${NC}"
    find "$PODCAST_TEMP_DIR" -mindepth 1 -delete
elif [ -n "$RESUME_FLAG" ]; then
    echo -e "${YELLOW}Behalte $PODCAST_TEMP_DIR fuer Resume bei...${NC}"
else
    echo -e "${YELLOW}Leere $PODCAST_TEMP_DIR...${NC}"
    find "$PODCAST_TEMP_DIR" -mindepth 1 -delete
fi

# 4. VIRTUAL ENVIRONMENT (.venv) SETUP
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Erstelle virtuelles Python-Environment (.venv)...${NC}"
    $PYTHON_BIN -m venv .venv
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
        if command -v deactivate >/dev/null 2>&1; then
            deactivate
        fi
        exit 1
    fi
else
    echo -e "${RED}Warnung: setup.sh nicht gefunden. Versuche manuelle Installation...${NC}"
    pip install -r requirements.txt || {
        echo -e "${RED}pip install fehlgeschlagen.${NC}"
        if command -v deactivate >/dev/null 2>&1; then
            deactivate
        fi
        exit 1
    }
fi

# 6. PROGRAMM STARTEN
printf "\n%b🚀 Starte %s Generator mit Thema:%b\n'%s'\n\n" "$GREEN" "$PODCAST_NAME" "$NC" "$TOPIC"
echo "------------------------------------------------"

# Wir pipen das Thema direkt in das Python-Skript, da dieses 'input()' verwendet.
python3 "$SCRIPT_FILE" $RESUME_FLAG $FORCE_RESTART_FLAG "$TOPIC"

# Deaktivieren (optional, da Skript hier endet)
if command -v deactivate >/dev/null 2>&1; then
    deactivate
fi
