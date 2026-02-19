#!/bin/bash
#
# RealmsMUD Launch Script
# =======================
# Starts the fantasy MUD server
#

# Change to the source directory
cd "$(dirname "$0")/src"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Create required directories
mkdir -p ../lib/players ../log ../world/zones

# Set PYTHONPATH
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Display banner
echo ""
echo "    ╔═══════════════════════════════════════════════════════════════╗"
echo "    ║                                                               ║"
echo "    ║   ██████╗ ███████╗ █████╗ ██╗     ███╗   ███╗███████╗         ║"
echo "    ║   ██╔══██╗██╔════╝██╔══██╗██║     ████╗ ████║██╔════╝         ║"
echo "    ║   ██████╔╝█████╗  ███████║██║     ██╔████╔██║███████╗         ║"
echo "    ║   ██╔══██╗██╔══╝  ██╔══██║██║     ██║╚██╔╝██║╚════██║         ║"
echo "    ║   ██║  ██║███████╗██║  ██║███████╗██║ ╚═╝ ██║███████║         ║"
echo "    ║   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝╚══════╝         ║"
echo "    ║                       MUD                                     ║"
echo "    ║                                                               ║"
echo "    ╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "    Starting RealmsMUD server on port 4000..."
echo ""

# Start the server
python3 main.py "$@"
