echo "Setting up Mailbot 9000 dev environment..."

echo "Creating virtual environment..."
python3 -m venv mailbot9000

source mailbot9000/bin/activate

if [ -f requirements.txt ]; then  
    pip install -r requirements.txt
else
    echo "requirements.txt file not found \nproceeding with default dependencies..."
    exit 1
fi

echo "Mailbot 9000 dev environment setup complete!"
echo "Please read the README.md file for instructions on how to use the project."