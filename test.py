
import asyncio

import aiohttp


async def send(session, id, data):
	async with session.post('http://localhost:8080/send', data={'id': id, "text": data}) as resp:
		await resp.text()


async def test():
	session = aiohttp.ClientSession()
	ws123 = await session.ws_connect('http://localhost:8080/receive?id=123')
	ws100 = await session.ws_connect('http://localhost:8080/receive?id=100')
	print("-- Sockets connected.")
	
	await asyncio.gather(send(session, "123", "hi"), send(session, "100", "ho"))
	print("-- Sent.")

	m123, m100 = await asyncio.gather(ws123.receive(), ws100.receive())
	print("-- Received.")

	assert m123.data == "hi"
	assert m100.data == "ho"

	await asyncio.gather(ws100.close(), ws123.close())

	session.close()


asyncio.get_event_loop().run_until_complete(test())
print("-- OK.")
