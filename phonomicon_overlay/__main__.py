"""
Entry point for running Phonomicon overlay as a module.

Usage:
    python -m phonomicon_overlay --host 127.0.0.1 --port 8794
"""

from phonomicon_overlay.server import main

if __name__ == "__main__":
    main()
