#!/usr/bin/env bash
set -euo pipefail

PYTHON_REQUIRED="3.11"
VENV_DIR=".venv"
ENV_FILE=".env"
ENV_EXAMPLE=".env.example"

echo "=== StarSeek Setup ==="
echo ""

# ── 1. Check prerequisites ──────────────────────────────

if command -v python3.11 &>/dev/null; then
    PYTHON_BIN="python3.11"
elif command -v python3 &>/dev/null; then
    PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if [ "$PY_VERSION" = "$PYTHON_REQUIRED" ]; then
        PYTHON_BIN="python3"
    else
        echo "ERROR: Python $PYTHON_REQUIRED is required, but found Python $PY_VERSION."
        echo ""
        echo "Install Python 3.11 using one of:"
        echo "  pyenv install 3.11 && pyenv local 3.11"
        echo "  sudo dnf install python3.11  (Fedora)"
        echo "  sudo apt install python3.11  (Debian/Ubuntu)"
        exit 1
    fi
else
    echo "ERROR: Python 3 not found. Install Python $PYTHON_REQUIRED."
    exit 1
fi

echo "✓ Found $($PYTHON_BIN --version)"

# ── 2. Create virtual environment ────────────────────────

if [ -d "$VENV_DIR" ]; then
    echo "✓ Virtual environment already exists at $VENV_DIR"
else
    echo "Creating virtual environment..."
    $PYTHON_BIN -m venv "$VENV_DIR"
    echo "✓ Created $VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
pip install --upgrade pip --quiet

# ── 3. Install dependencies ─────────────────────────────

echo "Installing dependencies..."
pip install -r requirements.txt --quiet

if [ "${1:-}" = "--dev" ] || [ "${1:-}" = "-d" ]; then
    echo "Installing dev dependencies..."
    pip install -r requirements-dev.txt --quiet
fi

if python -c "import swisseph" 2>/dev/null; then
    echo "✓ pyswisseph installed successfully"
else
    echo "ERROR: pyswisseph failed to import. Check installation logs above."
    exit 1
fi

# ── 4. Scaffold .env ────────────────────────────────────

if [ -f "$ENV_FILE" ]; then
    echo "✓ $ENV_FILE already exists (skipping)"
else
    cp "$ENV_EXAMPLE" "$ENV_FILE"

    echo ""
    echo "StarSeek uses GeoNames (free) for city-to-coordinates lookup."
    echo "Register at: https://www.geonames.org/login"
    echo ""
    read -rp "Enter your GeoNames username (or press Enter to skip for now): " GEONAMES_USER

    if [ -n "$GEONAMES_USER" ]; then
        sed -i "s/^GEONAMES_USERNAME=.*/GEONAMES_USERNAME=$GEONAMES_USER/" "$ENV_FILE"
        echo "✓ GeoNames username saved to $ENV_FILE"
    else
        echo "⚠ Skipped. Set GEONAMES_USERNAME in $ENV_FILE later."
    fi

    echo ""
    read -rp "Set admin password (default: 'admin'): " ADMIN_PASS
    if [ -n "$ADMIN_PASS" ]; then
        sed -i "s/^STARSEEK_ADMIN_PASSWORD=.*/STARSEEK_ADMIN_PASSWORD=$ADMIN_PASS/" "$ENV_FILE"
    fi
fi

# ── 5. Smoke test ────────────────────────────────────────

echo "Running smoke test..."
python -c "
import swisseph as swe
swe.set_ephe_path('')
jd = swe.julday(2000, 1, 1, 0.0)
xx, _ = swe.calc_ut(jd, swe.SUN)
swe.close()
sign_names = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
              'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
sign = sign_names[int(xx[0] / 30)]
deg = int(xx[0] % 30)
print(f'✓ Smoke test passed: Sun at {deg}° {sign} on J2000.0')
"

# ── 6. Done ──────────────────────────────────────────────

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  source .venv/bin/activate     # Activate the virtual environment"
echo "  make run                      # Start the API server"
echo "  make test                     # Run the test suite"
echo ""
