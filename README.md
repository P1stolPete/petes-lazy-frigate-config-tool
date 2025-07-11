# Pete's Lazy Frigate Config Tool

A powerful Python tool for generating Frigate camera configuration at scale. Perfect for deploying Frigate across multiple locations with dozens or hundreds of IP cameras.

## Features

- **Bulk Configuration**: Generate Frigate camera configs from CSV camera lists
- **Connectivity Testing**: Automatically ping cameras to check availability
- **Smart Organization**: Online cameras at top, offline cameras at bottom
- **URL Sanitization**: Ensures valid camera names for RTSP streams
- **Duplicate Handling**: Automatically resolves naming conflicts
- **Cross-Platform**: Works on Windows, Linux, and macOS
- **Error Handling**: Comprehensive validation and error reporting

## Prerequisites

- Python 3.6+
- Network access to camera IPs for connectivity testing
- CSV file with camera details

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/petes-lazy-frigate-config-tool.git
cd petes-lazy-frigate-config-tool
```

2. Install dependencies:
```bash
pip install pyyaml
```

## CSV Format

Create a `cameralist.csv` file with the following columns:

| Username | Password | IP | Camera Name |
|----------|----------|----|-----------| 
| admin | password123 | 192.168.1.100 | Front Door |
| admin | password123 | 192.168.1.101 | Back Yard |
| admin | password123 | 192.168.1.102 | Driveway |

**Required Columns:**
- `Username`: Camera login username
- `Password`: Camera login password  
- `IP`: Camera IP address
- `Camera Name`: Descriptive name for the camera

## Usage

1. Place your `cameralist.csv` file in the same directory as the script
2. Run the generator:
```bash
python petes_lazy_frigate_config_tool.py
```

3. The script will:
   - Read your CSV file
   - Ping each camera to test connectivity
   - Generate `config.yaml` with proper Frigate formatting
   - Provide a detailed summary

4. Simply copy & paste each section of the generated config into your Frigate config.yaml file. Refer to Frigate Doc's for detailed information.
## Generated Configuration

The tool generates a compatible Frigate camera configuration with:

- **Go2RTC Streams**: Main and sub streams for each camera
- **Camera Definitions**: Proper ffmpeg inputs with record/detect roles
- **Audio Support**: AAC audio encoding for all streams
- **Organized Layout**: Online cameras first, offline cameras at bottom

### Example Output Structure:
```yaml
        MAIN FEED STREAMS

  streams:
    #Camera ID
    Front_Door:
      - rtsp://admin:password123@192.168.1.100:554/s0
      - ffmpeg:Front_Door#audio=aac
    Front_Door_Sub:
      - rtsp://admin:password123@192.168.1.100:554/s1
      - ffmpeg:Front_Door_Sub#audio=aac

        FFMPEG STREAMS

cameras:
  #Camera ID
  Front_Door:
    ffmpeg:
      inputs:
        - path: rtsp://127.0.0.1:8554/Front_Door
          roles:
            - record
        - path: rtsp://127.0.0.1:8554/Front_Door_Sub
          roles:
            - detect
      output_args:
        record: preset-record-generic-audio-aac
```

## Perfect for Enterprise Deployments

This tool is ideal for:

- **Large Organisations**: Deploy Frigate across multiple buildings/locations
- **Security Companies**: Rapidly configure client installations
- **System Integrators**: Streamline camera system deployments
- **Multi-Site Deployments**: Consistent configuration across locations
- **Camera Migrations**: Easily transition from other NVR systems

## Advanced Features

### Connectivity Testing
- Pings each camera before configuration
- 3-second timeout per camera
- Visual feedback (✓ online, ✗ offline)
- Offline cameras grouped at bottom of config

### Name Sanitization
- Replaces spaces and hyphens with underscores
- Ensures valid RTSP URLs
- Maintains readability while ensuring compatibility

### Duplicate Resolution
- Automatically handles duplicate camera names
- Appends numbers to resolve conflicts
- Warns about renamed cameras

## Scale Benefits

When deploying Frigate at scale, this tool provides:

- **Time Savings**: Minutes instead of hours for configuration
- **Consistency**: Standardised configurations across deployments
- **Error Reduction**: Automated validation prevents common mistakes
- **Troubleshooting**: Quick identification of offline cameras
- **Maintenance**: Easy updates when camera details change

## Error Handling

The script handles various error conditions:

- Missing CSV files
- Invalid IP addresses
- Missing required columns
- Network connectivity issues
- Duplicate camera names
- Invalid camera credentials

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- Create an issue for bug reports
- Use discussions for questions
- Include CSV sample and error output when reporting issues

## Acknowledgments

- [Frigate NVR](https://github.com/blakeblackshear/frigate) - The amazing open-source NVR
- [Go2RTC](https://github.com/AlexxIT/go2rtc) - Real-time streaming server
- [P1stolPete](https://github.com/P1stolPete) - Systems Builder & Administrator

---
