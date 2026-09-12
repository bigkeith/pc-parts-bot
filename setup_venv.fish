#!/usr/bin/env fish
# setup_venv.fish
# Sets up the Python virtual environment for the PC Parts Price Bot
# on a new machine. Run this once from inside the pc-parts-bot folder.

echo "Creating virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate.fish

echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo ""
echo "Done! The venv is active in this terminal session."
echo "Next time you open a new terminal, activate it again with:"
echo "    source venv/bin/activate.fish"
echo ""
echo "Don't forget to also create your .env file with:"
echo "    GMAIL_ADDRESS=youremail@gmail.com"
echo "    GMAIL_APP_PASSWORD=your16charapppassword"
echo "    EBAY_CLIENT_ID=your_ebay_client_id"
echo "    EBAY_CLIENT_SECRET=your_ebay_client_secret"