import asyncio
import sys
from typing import NamedTuple
from typing import NoReturn
import argparse
import json
import re

HOST = 'irc.chat.twitch.tv'
PORT = 6697
MSG_RE = re.compile('^:([^!]+).* PRIVMSG #[^ ]+ :([^\r]+)')
PRIVMSG = 'PRIVMSG #{channel} :{msg}\r\n'

class Config(NamedTuple):
	username: str
	channel: str
	oauth_token: str
	client_id: str

	def __repr__(self) -> str:
		return (
				f'{type(self).__name__}('
				f'username={self.username!r},'
				f'channel={self.channel!r},'
				f'oauth_token={"***"!r},'
				f'client_id={"***"!r},'
				f')'
		)

async def asyncmain(config: Config, *, quiet: bool) -> NoReturn:
	reader, writer = await asyncio.open_connection(HOST, PORT, ssl=True)

	await send(writer, f'PASS {config.oauth_token}\r\n', quiet=True)
	await send(writer, f'NICK {config.username}\r\n', quiet=quiet)
	await send(writer, f'JOIN #{config.channel}\r\n', quiet=quiet)

	while True:
		data = await recv(reader, quiet=quiet)
		msg = data.decode('UTF-8', errors='backslashreplace')
		print(msg)

async def send(
		writer: asyncio.StreamWriter,
		msg: str,
		*,
		quiet: bool = False,
)-> None:
	if not quiet:
		print(f'< {msg}', end='', flush=True, file=sys.stderr)
	writer.write(msg.encode())
	return await writer.drain()

async def recv(
		reader: asyncio.StreamReader,
		*,
		quiet: bool = False,
)-> bytes:
	data = await reader.readline()
	print(data)	
	if not quiet:
		sys.stderr.buffer.write(b'> ')
		sys.stderr.buffer.write(data)
		sys.stderr.flush()
	return data


def main() -> int:
	parser = argparse.ArgumentParser()
	parser.add_argument('--config', default='config.json')
	parser.add_argument('--verbose', action='store_true')
	args = parser.parse_args()

	with open(args.config) as f:
		config = Config(**json.load(f))
	
	asyncio.run(asyncmain(config, quiet=not args.verbose))
	return 0

if __name__ == '__main__':
	exit(main())
