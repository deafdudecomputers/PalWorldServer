import subprocess, os, sys, importlib, datetime, time, json, ctypes, base64, zipfile, re, shutil, logging, socket, platform, urllib.request, filecmp, threading, tempfile, signal, fnmatch
from datetime import datetime
external_libs = os.path.abspath(os.path.join(os.path.dirname(__file__), 'external_libs'))
os.makedirs(external_libs, exist_ok=True)
sys.path.insert(0, external_libs)
def ensure_package_installed(package_name):
    try:
        importlib.import_module(package_name)
        print(f"{package_name} is already installed.")
    except ImportError:
        print(f"Installing {package_name}...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", package_name, "-t", external_libs],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print(f"{package_name} installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {package_name}. Error: {e}")
for package in ['requests', 'psutil', 'mcrcon']:
    ensure_package_installed(package)
import psutil, requests
from mcrcon import MCRcon