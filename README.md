# JellyHat

JellyHat is a Python-based "Now Playing" dashboard for the Pimoroni Display HAT Mini, specifically designed to interface with Jellyfin media servers. It provides real-time track metadata, album/artist artwork, and hardware monitoring for your Raspberry Pi.

## Features

- **Real-time Metadata**: Displays current track title and artist from active Jellyfin sessions.
- **Dynamic Artwork**: Tries to use backdrop, primary cover, then logo from JellyFin, before falling back to a local placeholder for the main display.
- **Hardware Monitoring**: Real-time CPU temperature display with a configurable LED warning system (transitions to red if the Pi gets too hot).
- **Energy Saving**: Automatic screen blanking after a configurable period of inactivity.
- **Robust Rendering**: Support for screen rotation for flexible mounting.

## Hardware Requirements

- Raspberry Pi (tested on Pi 4)
- Pimoroni Display HAT Mini
- **SPI Enabled**: Must be enabled via `raspi-config`.

## Installation

1. **Enable Hardware Interfaces**:

   The Display HAT Mini requires SPI to communicate with the screen.

   ```bash
   sudo raspi-config
   # Go to Interface Options -> SPI -> Yes. Then reboot.
   ```

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/freakylefty/jellyhat.git
   cd jellyhat
   ```

1. **Install Dependencies**:

   If you encounter issues with numpy or st7789, ensure you have system dependencies installed:

   ```bash
   sudo apt install python3-pip python3-venv libjpeg-dev zlib1g-dev libfreetype6-dev liblcms2-dev libopenjp2-7-dev libtiff5-dev libatlas-base-dev gfortran -y
   ```

1. **Set up Virtual Environment**:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

1. **Configure Environment**:

   Copy the example environment file and add your Jellyfin details:

   ```bash
   cp .env.example .env
   nano .env
   ```

   Required variables:
   - `JELLYFIN_URL`: Your server address (e.g., `http://192.168.1.50:8096`)
   - `JELLYFIN_API_KEY`: Generated in Jellyfin Dashboard -> API Keys

## Usage

Always run the script using the Python binary within your virtual environment:

```bash
./venv/bin/python3 jellyhat.py
```

### Command Line Arguments

- `--interval (-i)`: Refresh rate in seconds (Default: 5)
- `--threshold (-t)`: CPU Temp (°C) to trigger Red LED (Default: 70.0)
- `--rotate (-r)`: Rotate display 180 degrees (Default: False)
- `--blank (-b)`: Minutes of idle before screen blanking (Default: 10)
- `--hide-temp (-H)`: Hide the CPU temperature text (Default: False)
- `--debug (-d)`: Enable verbose console logging (Default: False)

### Customization

JellyHat uses a centralized THEME dictionary at the top of the script. This allows you to easily modify the look and feel of the interface—including colors, font sizes, and UI element positions—without needing to rewrite the core logic.

#### Example: Changing the Background Color

To change the background from black to a dark navy blue, locate the colors section in the THEME object and update the RGB values:

```Python

"colors": {
    "background": (0, 0, 20),  # Modified for a dark navy look
    "text_main": (255, 255, 255),
    ...
}
```

#### Key Theme Settings

- fonts: Set the path to your .ttf file and adjust sizes for titles and status text.
- colors: Define RGB tuples for text, backgrounds, and temperature-based LED warnings.
- layout: Adjust X/Y coordinates to shift text or change the maximum dimensions for artwork.

## Running As a Service

Create the service file

```bash
sudo nano /etc/systemd/system/jellyhat.service
```

Paste the configuration (make sure to update the paths and your_username):

```ini
[Unit]
Description=JellyHat Display Service
After=network.target

[Service]
# Replace with your actual user, path and options
# e.g. ExecStart=/home/pi/jellyhat/venv/bin/python3 /home/pi/jellyhat/jellyhat.py -r
User=<username>
WorkingDirectory=<path_to_project>
# Note: We point directly to the python binary inside the venv
ExecStart=<path_to_project>/venv/bin/python3 <path_to_project>/jellyhat.py

# Auto-restart logic
Restart=always
RestartSec=5

# Ensure output goes to system logs
StandardOutput=inherit
StandardError=inherit

[Install]
WantedBy=multi-user.target
```

Start and enable the service:

```bash
# Reload systemd to recognize the new file
sudo systemctl daemon-reload

# Enable it to run at boot
sudo systemctl enable jellyhat.service

# Start it now
sudo systemctl start jellyhat.service
```

Management:

| Task            | Command                                 |
| --------------- | --------------------------------------- |
| Check Status    | sudo systemctl status jellyhat.service  |
| Stop Service    | sudo systemctl stop jellyhat.service    |
| Restart Service | sudo systemctl restart jellyhat.service |
| View Live Logs  | journalctl -u jellyhat.service -f       |

## Project Structure

- `jellyhat.py`: The main application logic.
- `jellyfin_client.py`: JellyFin interaction code.
- `renderer.py`: Layout and output code.
- `hardware.py`: Display abstraction and hardware-specific calls.
- `config.py`: Centralized THEME and configuration logic.
- `requirements.txt`: Pinned library versions for stability.
- `fonts/`: Directory for UI fonts (e.g., Roboto).
- `assets/`: Directory for UI icons and placeholder album art.
- `.env`: (User Created) Secure storage for API credentials.

## License

This project is licensed under the MIT License.

## Thanks

Assets from [Kenney](https://www.kenney.nl/).
