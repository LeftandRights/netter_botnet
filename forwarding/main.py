from yaml import safe_load
from pyngrok import ngrok
from flask import Flask; app = Flask(
    __name__
)

ngrokConfig = ngrok.PyngrokConfig(config_path = 'config.yml', api_key = safe_load(open('config.yml'))['api_key'])
ngrokTcpAddress = ngrok.connect(name = 'tcp_server', pyngrok_config = ngrokConfig)
ngrok.connect(name = 'http_server', pyngrok_config = ngrokConfig)

@app.route('/')
def main() -> str:
    return str(ngrokTcpAddress.public_url)[6:]

app.run(host = '127.0.0.1', port = 59909)
