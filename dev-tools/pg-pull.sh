#!/bin/bash

# Generate SQLAlchemy models from existing database
# Usage: ./generate_models.sh [table_names]
# Example: ./generate_models.sh users,orders,products

set -e

# Configuration
MODELS_DIR="shared/models"
BACKUP_DIR="shared/models_backup_$(date +%Y%m%d_%H%M%S)"
POSTGRES_URL_FILE="backend/server/.env"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔧 SQLAlchemy Models Generator${NC}"
echo "================================================"

# Check if POSTGRES_URL exists
if [ ! -f "$POSTGRES_URL_FILE" ]; then
    echo -e "${RED}❌ Error: $POSTGRES_URL_FILE not found!${NC}"
    echo "Please create backend/server/.env with POSTGRES_URL"
    exit 1
fi

# Load POSTGRES_URL from .env
source "$POSTGRES_URL_FILE"

if [ -z "$POSTGRES_URL" ]; then
    echo -e "${RED}❌ Error: POSTGRES_URL not found in $POSTGRES_URL_FILE${NC}"
    echo "Please set POSTGRES_URL in your .env file"
    exit 1
fi

# Convert async URL to sync for sqlacodegen
SYNC_DATABASE_URL=$(echo "$POSTGRES_URL" | sed 's/postgresql+asyncpg:/postgresql:/')

echo -e "${YELLOW}📂 Database URL: ${SYNC_DATABASE_URL%/*}/***${NC}"

# Create backup of existing models
if [ -d "$MODELS_DIR" ] && [ "$(ls -A $MODELS_DIR)" ]; then
    echo -e "${YELLOW}📦 Creating backup at $BACKUP_DIR${NC}"
    cp -r "$MODELS_DIR" "$BACKUP_DIR"
fi

# Create models directory if not exists
mkdir -p "$MODELS_DIR"

# Generate models
echo -e "${GREEN}🚀 Generating models...${NC}"

if [ $# -eq 0 ]; then
    # Generate all tables
    echo "Generating models for all tables..."
    uv run sqlacodegen "$SYNC_DATABASE_URL" \
        --generator declarative \
        --schemas expo \
        --outfile "$MODELS_DIR/generated_models.py"
else
    # Generate specific tables
    TABLES=$1
    echo "Generating models for tables: $TABLES"
    uv run sqlacodegen "$SYNC_DATABASE_URL" \
        --generator declarative \
        --schemas expo \
        --tables "$TABLES" \
        --outfile "$MODELS_DIR/generated_models.py"
fi

# Add import to __init__.py if not exists
INIT_FILE="$MODELS_DIR/__init__.py"
if ! grep -q "from .generated_models import" "$INIT_FILE" 2>/dev/null; then
    echo "" >> "$INIT_FILE"
    echo "# Auto-generated models" >> "$INIT_FILE"
    echo "from .generated_models import *" >> "$INIT_FILE"
fi

echo -e "${GREEN}✅ Models generated successfully!${NC}"
echo ""
echo -e "${YELLOW}📝 Next steps:${NC}"
echo "1. Review generated models in $MODELS_DIR/generated_models.py"
echo "2. Split models into individual files if needed"
echo "3. Adjust Base class inheritance"
echo "4. Add relationships and constraints"
echo "5. Create migration: cd backend/server && alembic revision --autogenerate -m 'import existing schema'"
echo "6. Mark as applied: alembic stamp head"
echo ""
echo -e "${YELLOW}🗂️  Backup available at: $BACKUP_DIR${NC}"