#!/bin/sh

python3 -m venv venv

echo "✅ Virtual environment created in ./venv"

echo "Activating virtual environment..."
. ./venv/bin/activate

pip install -r requirements.txt
