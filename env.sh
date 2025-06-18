#!/bin/bash
set -euo pipefail

# Constants
CONFIG_FILE="config.yml"
VENV_DIR=".venv"
REQUIREMENTS_FILE="requirements.txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print error and exit
error_exit() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
    exit 1
}

# Function to print success message
success_msg() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Function to print warning message
warning_msg() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to check dependencies
check_dependencies() {
    local missing=()
    
    # Check Python 3
    if ! command -v python3 &> /dev/null; then
        missing+=("Python 3")
    fi
    
    # Check venv module (built into Python 3)
    if ! python3 -c "import venv" &> /dev/null; then
        missing+=("Python 3 venv module")
    fi
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        error_exit "Missing dependencies: ${missing[*]}"
    fi
    
    success_msg "All dependencies are installed"
}

# Function to create and activate virtual environment
setup_venv() {
    if [[ -d "$VENV_DIR" ]]; then
        warning_msg "Virtual environment already exists at $VENV_DIR"
    else
        echo "Creating virtual environment..."
        if ! python3 -m venv "$VENV_DIR"; then
            error_exit "Failed to create virtual environment"
        fi
        success_msg "Virtual environment created"
    fi
    
    echo "Activating virtual environment..."
    # shellcheck source=/dev/null
    source "$VENV_DIR/bin/activate" || error_exit "Failed to activate virtual environment"
    success_msg "Virtual environment activated"
    
    # Ensure pip is up to date in the virtual environment
    echo "Upgrading pip..."
    if ! pip install --upgrade pip; then
        warning_msg "Failed to upgrade pip, continuing with existing version"
    else
        success_msg "pip upgraded"
    fi
}

# Function to install dependencies
install_dependencies() {
    if [[ -f "$REQUIREMENTS_FILE" ]]; then
        echo "Installing dependencies from $REQUIREMENTS_FILE..."
        if ! pip install -r "$REQUIREMENTS_FILE"; then
            error_exit "Failed to install dependencies"
        fi
        success_msg "Dependencies installed"
    else
        warning_msg "No $REQUIREMENTS_FILE found, skipping dependency installation"
    fi
}

# Function to check config file
check_config() {
    if [[ ! -f "$CONFIG_FILE" ]]; then
        error_exit "Config file $CONFIG_FILE not found"
    fi
    success_msg "Config file $CONFIG_FILE found"
}

# Function to run the appropriate Python script
run_script() {
    local script_name="env_$1.py"
    
    if [[ ! -f "$script_name" ]]; then
        error_exit "Script $script_name not found"
    fi
    
    echo "Running $script_name..."
    if ! python "$script_name"; then
        error_exit "Failed to execute $script_name"
    fi
    
    success_msg "$script_name executed successfully"
}

# Main function
main() {
    if [[ $# -eq 0 ]]; then
        error_exit "Usage: $0 <environment> (e.g., dev, prod, test)"
    fi
    
    local environment="$1"
    
    echo -e "\n=== Setting up $environment environment ==="
    
    # Step 1: Check dependencies
    echo -e "\n1. Checking dependencies..."
    check_dependencies
    
    # Step 2: Setup virtual environment
    echo -e "\n2. Setting up virtual environment..."
    setup_venv
    
    # Step 3: Install dependencies
    echo -e "\n3. Installing dependencies..."
    install_dependencies
    
    # Step 4: Check config file
    echo -e "\n4. Checking config file..."
    check_config
    
    # Step 5: Run the appropriate script
    echo -e "\n5. Running environment script..."
    run_script "$environment"
    
    echo -e "\n=== Environment setup completed successfully ==="
}

# Execute main function with arguments
main "$@"
