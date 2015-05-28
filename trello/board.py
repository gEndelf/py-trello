# -*- coding: utf-8 -*-
from member import Member
from trellolist import List
from card import Card


class Board(object):
    """
    Class representing a Trello board. Board attributes are stored as normal
    Python attributes; access to all sub-objects, however, is always
    an API call (Lists, Cards).
    """

    def __init__(self, client=None, board_id=None, organization=None, name=''):
        """
        :trello: Reference to a Trello object
        :board_id: ID for the board

        Alternative Constructor

        :organization: reference to the parent organization
        :board_id: ID for this board

        """
        if organization is None:
            self.client = client
        else:
            self.organization = organization
            self.client = organization.client
        self.id = board_id
        self.name = name

    @classmethod
    def from_json(cls, trello_client=None, organization=None, json_obj=None):
        """
        Deserialize the board json object to a Board object

        :trello_client: the trello client
        :json_obj: the board json object

        Alternative contrustraction:

        Deserialize the board json object to a board object

        :organization: the organization object that the board belongs to
        :json_obj: the json board object
        """
        if organization is None:
            board = Board(client=trello_client, board_id=json_obj['id'], name=json_obj['name'].encode('utf-8'))
        else:
            board = Board(organization=organization, board_id=json_obj['id'], name=json_obj['name'].encode('utf-8'))

        board.description = json_obj.get('desc', '').encode('utf-8')
        board.closed = json_obj['closed']
        board.url = json_obj['url']
        return board

    def __repr__(self):
        return '<Board %s>' % self.name

    def fetch(self):
        """Fetch all attributes for this board"""
        json_obj = self.client.fetch_json('/boards/' + self.id)
        self.name = json_obj['name']
        self.description = json_obj.get('desc', '')
        self.closed = json_obj['closed']
        self.url = json_obj['url']

    def save(self):
        pass

    def close(self):
        self.client.fetch_json(
            '/boards/' + self.id + '/closed',
            http_method='PUT',
            post_args={'value': 'true', }, )
        self.closed = True

    def get_list(self, list_id):
        obj = self.client.fetch_json('/lists/' + list_id)
        return List.from_json(board=self, json_obj=obj)

    def all_lists(self):
        """Returns all lists on this board"""
        return self.get_lists('all')

    def open_lists(self):
        """Returns all open lists on this board"""
        return self.get_lists('open')

    def closed_lists(self):
        """Returns all closed lists on this board"""
        return self.get_lists('closed')

    def get_lists(self, list_filter):
        # error checking
        json_obj = self.client.fetch_json(
            '/boards/' + self.id + '/lists',
            query_params={'cards': 'none', 'filter': list_filter})
        return [List.from_json(board=self, json_obj=obj) for obj in json_obj]

    def add_list(self, name):
        """Add a list to this board

        :name: name for the list
        :return: the list
        """
        obj = self.client.fetch_json(
            '/lists',
            http_method='POST',
            post_args={'name': name, 'idBoard': self.id}, )
        return List.from_json(board=self, json_obj=obj)

    def all_cards(self):
        """Returns all cards on this board"""
        filters = {
            'filter': 'all',
            'fields': 'all'
        }
        return self.get_cards(filters)

    def open_cards(self):
        """Returns all open cards on this board"""
        filters = {
            'filter': 'open',
            'fields': 'all'
        }
        return self.get_cards(filters)

    def closed_cards(self):
        """Returns all closed cards on this board"""
        filters = {
            'filter': 'closed',
            'fields': 'all'
        }
        return self.get_cards(filters)

    def get_cards(self, filters=None):
        """
        :card_filter: filters on card status ('open', 'closed', 'all')
        :query_params: dict containing query parameters. Eg. {'fields': 'all'}

        More info on card queries:
        https://trello.com/docs/api/board/index.html#get-1-boards-board-id-cards
        """
        json_obj = self.client.fetch_json(
            '/boards/' + self.id + '/cards',
            query_params=filters
        )
        return list([Card.from_json(self, json) for json in json_obj])

    def all_members(self):
        """Returns all members on this board"""
        filters = {
            'filter': 'all',
            'fields': 'all'
        }
        return self.get_members(filters)

    def normal_members(self):
        """Returns all normal members on this board"""
        filters = {
            'filter': 'normal',
            'fields': 'all'
        }
        return self.get_members(filters)

    def admin_members(self):
        """Returns all admin members on this board"""
        filters = {
            'filter': 'admins',
            'fields': 'all'
        }
        return self.get_members(filters)

    def owner_members(self):
        """Returns all owner members on this board"""
        filters = {
            'filter': 'owners',
            'fields': 'all'
        }
        return self.get_members(filters)

    def get_members(self, filters=None):
        json_obj = self.client.fetch_json(
            '/boards/' + self.id + '/members',
            query_params=filters)
        members = list()
        for obj in json_obj:
            m = Member(self.client, obj['id'])
            m.status = obj['status'].encode('utf-8')
            m.id = obj.get('id', '')
            m.bio = obj.get('bio', '')
            m.url = obj.get('url', '')
            m.username = obj['username'].encode('utf-8')
            m.full_name = obj['fullName'].encode('utf-8')
            m.initials = obj['initials'].encode('utf-8')
            members.append(m)

        return members

    def fetch_actions(self, action_filter):
        json_obj = self.client.fetch_json(
            '/boards/' + self.id + '/actions',
            query_params={'filter': action_filter})
        self.actions = json_obj
