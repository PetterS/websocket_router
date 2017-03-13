
import asyncio

import aiohttp


async def send(session, id, data):
	async with session.post('http://localhost:8080/send', data={'id': id, "text": data}) as resp:
		text = await resp.text()
	assert text == "OK"


async def test_basic(session):
	ws123 = await session.ws_connect('http://localhost:8080/receive?id=123')
	ws100 = await session.ws_connect('http://localhost:8080/receive?id=100')
	print("-- Basic: Sockets connected.")
	
	await asyncio.gather(send(session, "123", "hi"), send(session, "100", "ho"))
	print("-- Basic: Sent.")

	m123, m100 = await asyncio.gather(ws123.receive(), ws100.receive())
	print("-- Basic: Received.")

	assert m123.data == "hi"
	assert m100.data == "ho"

	await asyncio.gather(ws100.close(), ws123.close())


async def test_nonexisting(session):
	await send(session, "not_found_id", "Text")


async def test_send_noid(session):
	async with session.post('http://localhost:8080/send', data={"text": "data"}) as resp:
		text = await resp.text()
	assert text == "Need id and data."


async def test_receive_noid(session):
	async with session.get('http://localhost:8080/receive') as resp:
		text = await resp.text()
	assert text == "Done"


async def test():
	session = aiohttp.ClientSession()
	await test_basic(session)
	await test_nonexisting(session)
	await test_send_noid(session)
	await test_receive_noid(session)
	session.close()

asyncio.get_event_loop().run_until_complete(test())
print("-- OK.")
