#!/usr/bin/env python
"""Entry point for running the application"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True, use_reloader=False)
