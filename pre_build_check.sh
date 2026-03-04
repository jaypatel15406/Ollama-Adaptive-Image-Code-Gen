#!/bin/bash
# =============================================================================
# Pre-Build Validation Script
# =============================================================================
# This script performs all necessary validations before Docker build
# to avoid wasting hours on failed builds.
#
# Usage: ./pre_build_check.sh
# =============================================================================

set -e

echo ""
echo "================================================================================"
echo "  Ollama Adaptive Image Code Gen - Pre-Build Validation"
echo "================================================================================"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# Function to print success
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

# Function to print error
print_error() {
    echo -e "${RED}✗${NC} $1"
    ERRORS=$((ERRORS + 1))
}

# =============================================================================
# 1. Check Python files syntax
# =============================================================================
echo "[1/6] Checking Python syntax..."

python3 -m py_compile main.py 2>/dev/null && print_success "main.py syntax OK" || print_error "main.py has syntax errors"
python3 -m py_compile utility/config_loader.py 2>/dev/null && print_success "utility/config_loader.py syntax OK" || print_error "utility/config_loader.py has syntax errors"
python3 -m py_compile utility/common_utility.py 2>/dev/null && print_success "utility/common_utility.py syntax OK" || print_error "utility/common_utility.py has syntax errors"
python3 -m py_compile utility/code_execution_utility.py 2>/dev/null && print_success "utility/code_execution_utility.py syntax OK" || print_error "utility/code_execution_utility.py has syntax errors"
python3 -m py_compile utility/ollama_health.py 2>/dev/null && print_success "utility/ollama_health.py syntax OK" || print_error "utility/ollama_health.py has syntax errors"
python3 -m py_compile utility/version.py 2>/dev/null && print_success "utility/version.py syntax OK" || print_error "utility/version.py has syntax errors"

echo ""

# =============================================================================
# 2. Validate configuration files
# =============================================================================
echo "[2/6] Validating configuration files..."

if [ -f "config/config.json" ]; then
    python3 -c "import json; json.load(open('config/config.json'))" 2>/dev/null && print_success "config/config.json is valid JSON" || print_error "config/config.json has JSON syntax errors"
else
    print_error "config/config.json not found"
fi

if [ -f "config/prompt_config.json" ]; then
    python3 -c "import json; json.load(open('config/prompt_config.json'))" 2>/dev/null && print_success "config/prompt_config.json is valid JSON" || print_error "config/prompt_config.json has JSON syntax errors"
else
    print_error "config/prompt_config.json not found"
fi

echo ""

# =============================================================================
# 3. Check version consistency
# =============================================================================
echo "[3/6] Checking version consistency..."

CONFIG_VERSION=$(python3 -c "import json; print(json.load(open('config/config.json')).get('version', 'N/A'))" 2>/dev/null || echo "N/A")
APP_VERSION=$(python3 -c "from utility.version import __version__; print(__version__)" 2>/dev/null || echo "N/A")

if [ "$CONFIG_VERSION" = "$APP_VERSION" ]; then
    print_success "Version consistency: $CONFIG_VERSION"
else
    print_warning "Version mismatch: config.json='$CONFIG_VERSION', app='$APP_VERSION'"
fi

echo ""

# =============================================================================
# 4. Check Dockerfile
# =============================================================================
echo "[4/6] Checking Dockerfile..."

if [ -f "Dockerfile" ]; then
    if grep -q "ollama/ollama:" Dockerfile; then
        OLLAMA_VERSION=$(grep "FROM ollama/ollama:" Dockerfile | cut -d':' -f2)
        print_success "Dockerfile uses ollama/ollama:$OLLAMA_VERSION"
    else
        print_error "Dockerfile doesn't specify ollama base image"
    fi
    
    if grep -q "WORKDIR /app" Dockerfile; then
        print_success "Dockerfile sets WORKDIR /app"
    else
        print_warning "Dockerfile doesn't set WORKDIR"
    fi
    
    if grep -q "ENTRYPOINT" Dockerfile; then
        print_success "Dockerfile has ENTRYPOINT"
    else
        print_error "Dockerfile missing ENTRYPOINT"
    fi
else
    print_error "Dockerfile not found"
fi

echo ""

# =============================================================================
# 5. Check docker-compose.yaml
# =============================================================================
echo "[5/6] Checking docker-compose.yaml..."

if [ -f "docker-compose.yaml" ]; then
    if grep -q "volumes:" docker-compose.yaml; then
        print_success "docker-compose.yaml has volume mounts"
    else
        print_warning "docker-compose.yaml missing volume mounts"
    fi
    
    if grep -q "healthcheck:" docker-compose.yaml; then
        print_success "docker-compose.yaml has healthcheck"
    else
        print_warning "docker-compose.yaml missing healthcheck"
    fi
    
    if grep -q "environment:" docker-compose.yaml; then
        print_success "docker-compose.yaml has environment variables"
    else
        print_warning "docker-compose.yaml missing environment variables"
    fi
else
    print_error "docker-compose.yaml not found"
fi

echo ""

# =============================================================================
# 6. Check requirements.txt
# =============================================================================
echo "[6/6] Checking requirements.txt..."

if [ -f "requirements.txt" ]; then
    if grep -q "ollama==" requirements.txt; then
        print_success "requirements.txt has pinned ollama version"
    else
        print_warning "requirements.txt missing pinned ollama version"
    fi
    
    if grep -q "aiohttp==" requirements.txt; then
        print_success "requirements.txt has pinned aiohttp version"
    else
        print_warning "requirements.txt missing pinned aiohttp version"
    fi
    
    if grep -q "requests==" requirements.txt; then
        print_success "requirements.txt has pinned requests version"
    else
        print_warning "requirements.txt missing pinned requests version"
    fi
else
    print_error "requirements.txt not found"
fi

echo ""

# =============================================================================
# Summary
# =============================================================================
echo "================================================================================"
echo "  Validation Summary"
echo "================================================================================"
echo "  Errors:   $ERRORS"
echo "  Warnings: $WARNINGS"
echo "================================================================================"

if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}✗ VALIDATION FAILED${NC} - Please fix the errors above before building"
    echo ""
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠ VALIDATION PASSED WITH WARNINGS${NC} - You can proceed but review warnings"
    echo ""
    echo "To fix warnings and rebuild:"
    echo "  1. Review warnings above"
    echo "  2. Make necessary changes"
    echo "  3. Run: ./pre_build_check.sh"
    echo "  4. Then: docker compose build"
    echo ""
    exit 0
else
    echo -e "${GREEN}✓ VALIDATION PASSED${NC} - All checks successful!"
    echo ""
    echo "Ready to build! Next steps:"
    echo "  1. docker compose build    # Build Docker image (~5-10 mins first time)"
    echo "  2. docker compose up       # Start Ollama service"
    echo "  3. python3 main.py         # Run application (in another terminal)"
    echo ""
    exit 0
fi
