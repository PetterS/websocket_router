
import argparse
import logging
import logging.handlers
import socket

import aiohttp
import aiohttp.web as web

parser = argparse.ArgumentParser()
parser.add_argument('--syslog_address', default=None, help='Send syslog messages to this address. Default=None')
parser.add_argument('--syslog_port', type=int, default=514, help='Send syslog messages to this port. Default=514')
parser.add_argument('--address', default="127.0.0.1", help='Bind websocket server to this address. Default=127.0.0.1')
parser.add_argument('--port', type=int, default=8080, help='Bind websocket server to this port. Default=8080')
args = parser.parse_args()

app = web.Application()
app["listeners"] = {}


def get_syslogger():
	syslogger = logging.getLogger('SysLogger')
	if args.syslog_address is not None:
		syslogger.setLevel(logging.DEBUG)
		handler = logging.handlers.SysLogHandler(address=(args.syslog_address, args.syslog_port))
		formatter = logging.Formatter('%(asctime)s ' + socket.gethostname() + ' websocket_router: %(message)s', datefmt='%b %d %H:%M:%S')
		handler.setFormatter(formatter)
		syslogger.addHandler(handler)
	else:
		logging.info("Not using syslog.")
	return syslogger


syslogger = get_syslogger()


async def send(request):
	data = await request.post()
	if "id" not in data or "text" not in data:
		logging.info("not valid")
		return web.Response(text="Need id and data.")

	id = data['id']
	text = data['text']

	listeners = app["listeners"]
	if id in listeners:
		for ws in app["listeners"][id]:
			if not ws.closed:
				ws.send_str(text)
	else:
		logging.info("-- No one listens to %s", id)

	return web.Response(text="OK")


async def receive(request):
	if "id" not in request.GET:
		return web.Response(text="Done")
	id = request.GET["id"]

	ws = web.WebSocketResponse()
	await ws.prepare(request)

	syslogger.info("Listener connected to %s", id)
	listeners = app["listeners"]
	if id not in listeners:
		listeners[id] = [ws]
	else:
		listeners[id].append(ws)

	async for msg in ws:
		if msg.type == aiohttp.WSMsgType.TEXT:
			if msg.data == 'close':
				await ws.close()
			else:
				logging.warning("Received unexpected \"%s\"", msg.data)
		elif msg.type == aiohttp.WSMsgType.ERROR:
			logging.warning('ws connection closed with exception %s',
			                ws.exception())

	syslogger.info('Websocket connection closed for id %s', id)

	# Cleanup
	listeners[id].remove(ws)
	if len(listeners[id]) == 0:
		del listeners[id]

	return ws

app.router.add_post('/send', send)
app.router.add_get('/receive', receive)

syslogger.info("Starting server.")
aiohttp.web.run_app(app, host=args.address, port=args.port)
