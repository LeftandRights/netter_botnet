# Ngrok Website and TCP Forwarder

This project uses Ngrok to expose both a web server and a TCP service. The HTTP server remains accessible via a constant public URL, while the TCP address changes dynamically. The website serves as a convenient way for users to fetch the current TCP address, which is required to access the underlying service.

## Project Overview

- **Static HTTP Address**: The HTTP address remains the same and is used to provide access to the webpage.
- **Dynamic TCP Address**: The TCP address changes each time the service is restarted or forwarded through Ngrok.
- **Fetching TCP Address**: Users access the website to fetch the current TCP address, which they then use to connect to the desired TCP service.

## How It Works

1. **Ngrok Setup**: Ngrok forwards both an HTTP server (using Flask) and a TCP service. The HTTP address is constant, while the TCP address changes with each new connection.
2. **Website**: A Flask web server displays the current TCP address. When users visit the static HTTP address, they can view the dynamically updated TCP address on the page.
3. **TCP Address Retrieval**: When a user accesses the website at the constant HTTP address, they are presented with the current TCP address, which is necessary for connecting to the TCP service.

## Prerequisites

- [Ngrok](https://ngrok.com/) (installed and configured with an API key)
- Python 3.x

## Configuration

Before running the project, ensure you have a properly configured `config.yml` file for Ngrok. Below is an example configuration file:

### Example `config.yml`

```yaml
version: "2"
authtoken: 2aqIya1... # Replace with your actual authtoken from Ngrok
api_key: 2lUcdDMX... # Replace with your actual API key from Ngrok

tunnels:
  http_server:
    labels:
      - edge=edghts_2g28hhz... # Replace with your specific edge ID for HTTP
    addr: http://localhost:59909 # Your Flask app running locally

  tcp_server:
    proto: tcp
    addr: 3451 # The port your local TCP service is running on
```
