#!/bin/bash

# Step 1: Install Homebrew if not already installed
if ! command -v brew &> /dev/null
then
    echo "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "Homebrew is already installed."
fi

# Step 2: Install Python3 if not already installed
if ! command -v python3 &> /dev/null
then
    echo "Python3 not found. Installing Python3..."
    brew install python
else
    echo "Python3 is already installed."
fi

# Step 3: Install pip if not already installed
if ! command -v pip3 &> /dev/null
then
    echo "pip3 not found. Installing pip3..."
    brew install pip
else
    echo "pip3 is already installed."
fi

# Step 4: Install virtualenv if not already installed
if ! pip3 show virtualenv &> /dev/null
then
    echo "virtualenv not found. Installing virtualenv..."
    pip3 install virtualenv
else
    echo "virtualenv is already installed."
fi

# Step 5: Create and activate a virtual environment
echo "Creating and activating a virtual environment..."
python3 -m venv myenv
source myenv/bin/activate

# Step 5: Install psycopg2-binary and pandas
echo "Installing psycopg2-binary and pandas..."
pip install psycopg2-binary pandas sqlalchemy

# Step 6: Run the Python script
echo "Running the Python script..."
python DB_Comparator.py

# Deactivate the virtual environment
deactivate

