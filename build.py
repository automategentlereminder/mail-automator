import os
import subprocess

def build_executable():
    print("Building Smart Mailer...")
    
    # We will use pyinstaller directly
    # Adjust options as needed
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onedir", # Using onedir is generally better for PySide6 because onefile is too slow to unpack, but user requested single .exe
        "--windowed", # No console
        "--name", "SmartMailer",
        "main.py"
    ]
    
    # We'll build as onefile as requested by the user: "bundle the app into a single .exe"
    cmd[2] = "--onefile"
    
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd)
    print("Build complete! Check the 'dist' folder.")

if __name__ == "__main__":
    build_executable()
