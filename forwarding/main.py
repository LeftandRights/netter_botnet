import logging, sys, loguru, threading, signal
from yaml import safe_load
from pyngrok import ngrok
from flask import Flask; app = Flask(
    __name__
)

ADDRESS, PORT = '127.0.0.1', 59909
log = logging.getLogger('werkzeug')
log.disabled = True

cli = sys.modules['flask.cli']
cli.show_server_banner = lambda *x: None

ngrokConfig = ngrok.PyngrokConfig(config_path = 'config.yml', api_key = safe_load(open('config.yml'))['api_key'])

ngrokTcpAddress = ngrok.connect(name = 'tcp_server', pyngrok_config = ngrokConfig)
loguru.logger.success('Server is forwarded to -> ' + (tcpUrl := str(ngrokTcpAddress.public_url)[6:]))

ngrok.connect(name = 'http_server', pyngrok_config = ngrokConfig)
loguru.logger.success('Ngrok edge tunnel has been activated, forwarding port ' + str(PORT))

@app.route('/')
def main() -> str:
    return tcpUrl

serv = threading.Thread(target = lambda: app.run(host = ADDRESS, port = PORT))
serv.daemon = True
serv.start()

signal.signal(signal.SIGINT, signal.SIG_DFL)
loguru.logger.success('HTTP Server running on http://%s:%s/' % (ADDRESS, PORT))
serv.join()
