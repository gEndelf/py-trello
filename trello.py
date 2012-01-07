from httplib2 import Http
from urllib import urlencode
from models import AuthenticationError,AuthenticationRequired,NoSuchObjectError
import json

class Trello:

	def __init__(self, username, password):
		self._client = Http()
		self._cookie = None
		self._username = username
		self._password = password
		self.login()

	def login(self):
		"""Log into Trello"""
		body = {
				'user': self._username,
				'password': self._password,
				'returnUrl': '/'}
		headers = {
				'Content-type': 'application/x-www-form-urlencoded',
				'Accept': 'application/json'}
		response, content = self._client.request(
				'https://trello.com/authenticate',
				'POST',
				headers = headers,
				body = urlencode(body))

		if response and response['set-cookie']:
			# auth was successful
			self._cookie = response['set-cookie']

			# grab the token out of the cookie
			start = self._cookie.find('token')
			end = self._cookie.find(' ', start)
			parts = self._cookie[start:(end-1)].split('=')
			self._token = parts[1]
			print self._token
			print self._cookie

		else:
			raise AuthenticationError()

	def logout(self):
		"""Log out of Trello. This method is idempotent."""
		if not self._cookie:
			return

		headers = {'Cookie': self._cookie, 'Accept': 'application/json'}
		response, content = self._client.request(
				'https://trello.com/logout',
				'GET',
				headers = headers,
				)

		# TODO: error checking
		self._cookie = None

	def list_boards(self):
		"""
		Returns all boards for your Trello user

		:return: a list of Python objects representing the Trello boards. Each board has the 
		following noteworthy attributes:
			- _id: the board's identifier
			- name: Name of the board
			- closed: Boolean representing whether this board is closed or not
		Other attributes include: 
			invitations, memberships, idMembersWatching, prefs, 
			nActionsSinceLastView, idOrganization

		@todo: the JSON response contains the values needed to dereference idFoo; be nice and expose 
		these, too
		"""
		if not self._cookie:
			raise AuthenticationRequired()

		headers = {'Cookie': self._cookie, 'Accept': 'application/json'}
		response, content = self._client.request(
				'https://trello.com/data/me/boards',
				'GET',
				headers = headers,
				)

		# TODO: error checking

		json_obj = json.loads(content)
		return json_obj['boards']

	def add_card(self, board_id, name):
		"""Adds a card to the first list in the given board

		:board_id: identifier for the board to which the card is to be added
		:name: name for the new card
		:returns: the id for the new card
		"""

		if not self._cookie:
			raise AuthenticationRequired()

		headers = {'Cookie': self._cookie, 'Accept': 'application/json'}
		response, content = self._client.request(
				'https://trello.com/data/board/'+board_id+'/current',
				'GET',
				headers = headers,
				)

		# TODO: error checking

		json_obj = json.loads(content)

		# get first list
		list_id = None
		for board in json_obj['boards']:
			if board['_id'] == board_id:
				if 'lists' in board:
					list_id = board['lists'][0]['_id']

		if not list_id:
			raise NoSuchObjectError('board', board_id)

		request = {
				'token': self._token,
				'method': 'create',
				'data': {
					'attrs': {
						'name': name,
						'pos': 65536,
						'closed': False,
						'idBoard': board_id,
						"idList": list_id,
						},
					'idParents': [ board_id, list_id ],
					}
				}

		headers = {'Cookie': self._cookie, 'Accept': 'application/json', 'Content-Type': 'application/json'}
		response, content = self._client.request(
				'https://trello.com/api/card',
				'POST',
				headers = headers,
				body = json.dumps(request),
				)

		# TODO: error checking
		json_obj = json.loads(content)
		print content
		return json_obj['_id']

