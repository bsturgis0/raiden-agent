#!/bin/bash
echo "Building Raiden+ Desktop Application..."
python3 build.py
if [ $? -eq 0 ]; then
    echo "Build successful! Find Raiden in the dist folder."
else
    echo "Build failed with error code $?"
fi
read -p "Press Enter to continue..."
