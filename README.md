# DS WebApp — Thermal-Stress Simulation Platform

A trame-based web application for thermal-stress simulation.

## Prerequisites

- Python >= 3.9
- pip

## Installation

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (for screenshot testing)
playwright install chromium
```

## Running the App

```bash
python -m app.main
```

The app will open in your default browser at `http://localhost:8080`.

## Running Screenshot Tests

```bash
python tests/test_screenshots.py
```

Screenshots are saved to the `screenshots/` folder.
# finmosa
