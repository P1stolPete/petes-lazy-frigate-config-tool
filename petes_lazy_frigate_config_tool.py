#!/usr/bin/env python3
"""

Pete's Lazy Frigate Config Tool  - v1.1107.2025

Converts camera details from CSV to Frigate-compatible config.yaml

https://github.com/P1stolPete

"""

import csv
import yaml
import sys
import subprocess
import platform
from typing import Dict, List, Any, Tuple

def read_camera_csv(filename: str) -> List[Dict[str, str]]:
    """
    Read camera details from CSV file.

    Args:
        filename: Path to the CSV file

    Returns:
        List of camera dictionaries
    """
    cameras = []

    try:
        with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            # Check if required columns exist
            required_columns = ['Username', 'Password', 'IP', 'Camera Name']
            if not all(col in reader.fieldnames for col in required_columns):
                missing = [col for col in required_columns if col not in reader.fieldnames]
                raise ValueError(f"Missing required columns: {missing}")

            for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
                # Check for missing data
                missing_fields = [col for col in required_columns if not row[col].strip()]
                if missing_fields:
                    print(f"Warning: Row {row_num} has missing data in columns: {missing_fields}")
                    continue

                # Clean the data
                camera = {
                    'username': row['Username'].strip(),
                    'password': row['Password'].strip(),
                    'ip': row['IP'].strip(),
                    'camera_name': row['Camera Name'].strip()
                }

                # Basic validation
                if not camera['ip'].replace('.', '').isdigit():
                    print(f"Warning: Row {row_num} has invalid IP format: {camera['ip']}")
                    continue

                cameras.append(camera)

    except FileNotFoundError:
        print(f"Error: CSV file '{filename}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)

    return cameras

def ping_camera(ip: str, timeout: int = 3) -> bool:
    """
    Ping a camera IP to check if it's alive.

    Args:
        ip: IP address to ping
        timeout: Timeout in seconds

    Returns:
        True if camera responds, False otherwise
    """
    try:
        # Determine ping command based on operating system
        if platform.system().lower() == 'windows':
            # Windows ping command
            cmd = ['ping', '-n', '1', '-w', str(timeout * 1000), ip]
        else:
            # Unix/Linux/Mac ping command
            cmd = ['ping', '-c', '1', '-W', str(timeout), ip]

        # Run ping command
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout + 1)
        return result.returncode == 0

    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False

def check_camera_status(cameras: List[Dict[str, str]]) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """
    Check the status of all cameras by pinging them.

    Args:
        cameras: List of camera dictionaries

    Returns:
        Tuple of (online_cameras, offline_cameras)
    """
    online_cameras = []
    offline_cameras = []

    print("Checking camera connectivity...")
    print("-" * 40)

    for camera in cameras:
        ip = camera['ip']
        name = camera['camera_name']

        print(f"Pinging {name} ({ip})...", end=" ")

        if ping_camera(ip):
            print("✓ Online")
            online_cameras.append(camera)
        else:
            print("✗ Offline")
            offline_cameras.append(camera)

    print("-" * 40)
    print(f"Status: {len(online_cameras)} online, {len(offline_cameras)} offline")

    if offline_cameras:
        print("\nOffline cameras will be placed at the bottom of the config.")

    return online_cameras, offline_cameras

def sanitize_camera_name(name: str) -> str:
    """
    Sanitize camera name for Frigate compatibility.

    Frigate requires camera names to match pattern: ^[a-zA-Z0-9_-]+$
    This function removes/replaces all invalid characters.

    Args:
        name: Original camera name

    Returns:
        Sanitized camera name that matches Frigate's requirements
    """
    import re

    # First, normalize whitespace and remove any non-breaking spaces or other unicode spaces
    name = re.sub(r'\s+', ' ', name.strip())

    # Replace spaces, forward slashes, and other common separators with underscores
    name = name.replace(' ', '_').replace('/', '_').replace('\\', '_')

    # Remove or replace any character that's not alphanumeric, underscore, or hyphen
    # This ensures compliance with Frigate's ^[a-zA-Z0-9_-]+$ pattern
    name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)

    # Remove multiple consecutive underscores
    name = re.sub(r'_+', '_', name)

    # Remove leading/trailing underscores
    name = name.strip('_')

    # Ensure name is not empty and starts with alphanumeric character
    if not name or not re.match(r'^[a-zA-Z0-9]', name):
        name = f"Camera_{name}" if name else "Camera"

    return name

def generate_frigate_config(online_cameras: List[Dict[str, str]], offline_cameras: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Generate Frigate configuration from camera lists.

    Args:
        online_cameras: List of online camera dictionaries
        offline_cameras: List of offline camera dictionaries

    Returns:
        Frigate configuration dictionary
    """
    config = {
        'go2rtc': {
            'streams': {}
        },
        'cameras': {}
    }

    # Track camera names to avoid duplicates
    used_names = set()

    # Process online cameras first, then offline cameras
    all_cameras = online_cameras + offline_cameras

    for camera in all_cameras:
        # Sanitize camera name for URL compatibility
        base_name = sanitize_camera_name(camera['camera_name'])

        # Handle duplicate camera names
        if base_name in used_names:
            counter = 2
            while f"{base_name}_{counter}" in used_names:
                counter += 1
            base_name = f"{base_name}_{counter}"
            print(f"Warning: Duplicate camera name detected. Using '{base_name}' instead.")

        used_names.add(base_name)
        sub_name = f"{base_name}_Sub"

        # Generate RTSP URLs
        main_rtsp = f"rtsp://{camera['username']}:{camera['password']}@{camera['ip']}:554/s0"
        sub_rtsp = f"rtsp://{camera['username']}:{camera['password']}@{camera['ip']}:554/s1"

        # Add to go2rtc streams
        config['go2rtc']['streams'][base_name] = [
            main_rtsp,
            f"ffmpeg:{base_name}#audio=aac"
        ]

        config['go2rtc']['streams'][sub_name] = [
            sub_rtsp,
            f"ffmpeg:{sub_name}#audio=aac"
        ]

        # Add to cameras section
        config['cameras'][base_name] = {
            'ffmpeg': {
                'inputs': [
                    {
                        'path': f"rtsp://127.0.0.1:8554/{base_name}",
                        'roles': ['record']
                    },
                    {
                        'path': f"rtsp://127.0.0.1:8554/{sub_name}",
                        'roles': ['detect']
                    }
                ],
                'output_args': {
                    'record': 'preset-record-generic-audio-aac'
                }
            }
        }

    return config

def write_yaml_with_comments(config: Dict[str, Any], online_cameras: List[Dict[str, str]], offline_cameras: List[Dict[str, str]], filename: str) -> None:
    """
    Write YAML config with proper formatting and comments.

    Args:
        config: Configuration dictionary
        online_cameras: List of online cameras
        offline_cameras: List of offline cameras
        filename: Output filename
    """
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            # Write go2rtc section with comments
            file.write("        MAIN FEED STREAMS\n\n")
            file.write("  streams:\n")

            # Create ordered list of camera names (online first, then offline)
            ordered_cameras = []
            for camera in online_cameras + offline_cameras:
                base_name = sanitize_camera_name(camera['camera_name'])
                ordered_cameras.append(base_name)

            # Write streams with camera name comments in order
            offline_section_started = False
            for i, stream_name in enumerate(ordered_cameras):
                if stream_name in config['go2rtc']['streams']:
                    # Add offline section header if we're starting offline cameras
                    if not offline_section_started and i >= len(online_cameras):
                        file.write("    # OFFLINE CAMERAS\n")
                        offline_section_started = True

                    file.write(f"    #Camera ID\n")
                    file.write(f"    {stream_name}:\n")
                    for item in config['go2rtc']['streams'][stream_name]:
                        file.write(f"      - {item}\n")

                    # Write corresponding sub stream
                    sub_name = f"{stream_name}_Sub"
                    if sub_name in config['go2rtc']['streams']:
                        file.write(f"    {sub_name}:\n")
                        for item in config['go2rtc']['streams'][sub_name]:
                            file.write(f"      - {item}\n")

            file.write("\n        FFMPEG STREAMS\n\n")
            file.write("cameras:\n")

            # Write cameras section with comments in order
            offline_section_started = False
            for i, camera_name in enumerate(ordered_cameras):
                if camera_name in config['cameras']:
                    # Add offline section header if we're starting offline cameras
                    if not offline_section_started and i >= len(online_cameras):
                        file.write("  # OFFLINE CAMERAS\n")
                        offline_section_started = True

                    file.write(f"  #Camera ID\n")
                    file.write(f"  {camera_name}:\n")
                    camera_config = config['cameras'][camera_name]
                    file.write("    ffmpeg:\n")
                    file.write("      inputs:\n")

                    for input_config in camera_config['ffmpeg']['inputs']:
                        file.write(f"        - path: {input_config['path']}\n")
                        file.write("          roles:\n")
                        for role in input_config['roles']:
                            file.write(f"            - {role}\n")

                    file.write("      output_args:\n")
                    file.write(f"        record: {camera_config['ffmpeg']['output_args']['record']}\n")

    except Exception as e:
        print(f"Error writing YAML file: {e}")
        sys.exit(1)

def main():
    """Main function to orchestrate the config generation."""
    csv_filename = 'cameralist.csv'
    output_filename = 'config.yaml'

    print("Pete's Lazy Frigate Config Tool - v1.1107.2025")
    print("=" * 30)

    # Read camera data from CSV
    print(f"Reading camera data from {csv_filename}...")
    cameras = read_camera_csv(csv_filename)

    if not cameras:
        print("No valid camera data found in CSV file.")
        sys.exit(1)

    print(f"Found {len(cameras)} valid camera(s)")

    # Check camera connectivity
    online_cameras, offline_cameras = check_camera_status(cameras)

    # Generate Frigate config
    print("\nGenerating Frigate configuration...")
    config = generate_frigate_config(online_cameras, offline_cameras)

    # Write config file
    print(f"Writing configuration to {output_filename}...")
    write_yaml_with_comments(config, online_cameras, offline_cameras, output_filename)

    print("Configuration generated successfully!")
    print(f"Output file: {output_filename}")

    # Display summary
    print("\nSummary:")
    print(f"- {len(cameras)} cameras total")
    print(f"- {len(online_cameras)} cameras online")
    print(f"- {len(offline_cameras)} cameras offline")
    print(f"- {len(config['go2rtc']['streams'])} streams created")
    print(f"- Main streams: {len([s for s in config['go2rtc']['streams'].keys() if not s.endswith('_Sub')])}")
    print(f"- Sub streams: {len([s for s in config['go2rtc']['streams'].keys() if s.endswith('_Sub')])}")

    # Show camera names that were sanitized
    sanitized_names = []
    for camera in cameras:
        original = camera['camera_name']
        sanitized = sanitize_camera_name(original)
        if original != sanitized:
            sanitized_names.append(f"'{original}' -> '{sanitized}'")

    if sanitized_names:
        print("\nCamera names sanitized for URL compatibility:")
        for name_change in sanitized_names:
            print(f"  - {name_change}")

    if offline_cameras:
        print(f"\nOffline cameras (placed at bottom of config):")
        for camera in offline_cameras:
            print(f"  - {camera['camera_name']} ({camera['ip']})")




    print(f"\nThanks for using Pete's Lazy Frigate Config Tool! Give him a high five!")

if __name__ == "__main__":
    main()
