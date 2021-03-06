from datetime import datetime, timedelta
from trello import TrelloClient, Unauthorized, ResourceUnavailable
import unittest
import os


class TrelloBoardTestCase(unittest.TestCase):
    """
    Tests for TrelloClient API. Note these test are in order to
    preserve dependencies, as an API integration cannot be tested
    independently.
    """

    @classmethod
    def setUpClass(cls):
        cls._trello = TrelloClient(os.environ['TRELLO_API_KEY'],
                                   token=os.environ['TRELLO_TOKEN'])
        for b in cls._trello.list_boards():
            if b.name == os.environ['TRELLO_TEST_BOARD_NAME']:
                cls._board = b
                break

        if not cls._board:
            cls.fail("Couldn't find test board")

        cls._list = cls._board.add_list(str(datetime.now()))

    def _add_card(self, name, description=None):
        try:
            card = self._list.add_card(name, description)
            self.assertIsNotNone(card, msg="card is None")
            self.assertIsNotNone(card.id, msg="id not provided")
            self.assertEquals(card.name, name)
            return card
        except Exception as e:
            print(str(e))
            self.fail("Caught Exception adding card")

    def test40_add_card(self):
        name = "Testing from Python - no desc"
        card = self._add_card(name)

        self.assertIsNotNone(card.closed, msg="closed not provided")
        self.assertIsNotNone(card.url, msg="url not provided")

        card2 = self._trello.get_card(card.id)
        self.assertEqual(card.name, card2.name)

    def test41_add_card(self):
        name = "Testing from Python"
        description = "Description goes here"
        card = self._add_card(name, description)

        self.assertEquals(card.description, description)
        self.assertIsNotNone(card.closed, msg="closed not provided")
        self.assertIsNotNone(card.url, msg="url not provided")
        card.fetch()
        self.assertIsNotNone(card.member_id)
        self.assertIsNotNone(card.short_id)
        self.assertIsNotNone(card.list_id)
        self.assertIsNotNone(card.comments)
        self.assertIsNotNone(card.checklists)
        self.assertIsInstance(card.create_date, datetime)

    def test42_add_card_with_comments(self):
        name = "Card with comments"
        comment = "Hello World!"
        card = self._add_card(name)
        card.comment(comment)
        card.fetch(True)

        self.assertEquals(card.description, '')
        self.assertIsNotNone(card.closed, msg="closed not provided")
        self.assertIsNotNone(card.url, msg="url not provided")
        self.assertEquals(len(card.comments), 1)
        self.assertEquals(card.comments[0]['data']['text'], comment)

    def test43_delete_checklist(self):
        name = "Card with comments"
        card = self._list.add_card(name)
        card.fetch(True)

        name = 'Checklists'
        checklist = card.add_checklist(name,
                                       ['item1', 'item2'])
        self.assertIsNotNone(checklist, msg="checklist is None")
        self.assertIsNotNone(checklist.id, msg="id not provided")
        self.assertEquals(checklist.name, name)
        checklist.delete()
        card.delete()

    def test44_attach_url_to_card(self):
        name = "Testing from Python - url"
        card = self._add_card(name)

        card.attach(name='lwn', url='http://lwn.net/')
        card.fetch()
        self.assertEquals(card.badges['attachments'], 1)
        card.delete()

    def test52_get_cards(self):
        cards = self._board.get_cards()
        self.assertEquals(len(cards), 4)

        for card in cards:
            if card.name == 'Testing from Python':
                self.assertEqual(card.description, 'Description goes here')
            elif card.name == 'Testing from Python - no desc':
                self.assertEqual(card.description, '')
            elif card.name == 'Card with comments':
                self.assertEqual(card.description, '')
            else:
                self.fail(msg='Unexpected card found')

        self.assertIsInstance(self._board.all_cards(), list)
        self.assertIsInstance(self._board.open_cards(), list)
        self.assertIsInstance(self._board.closed_cards(), list)

    def test52_add_card_set_due(self):
        name = "Testing from Python"
        description = "Description goes here"
        card = self._list.add_card(name, description)

        # Set the due date to be 3 days from now
        today = datetime.today()
        day_detla = timedelta(3)
        due_date = today + day_detla
        card.set_due(due_date)
        expected_due_date = card.due
        # Refresh the due date from cloud
        card.fetch()
        actual_due_date = card.due[:10]
        self.assertEquals(expected_due_date, actual_due_date)

    def test53_checklist(self):
        name = "Testing from Python"
        description = "Description goes here"
        card = self._list.add_card(name, description)

        name = 'Checklists'
        checklist = card.add_checklist(name,
                                       ['item1', 'item2'])
        self.assertIsNotNone(checklist, msg="checklist is None")
        self.assertIsNotNone(checklist.id, msg="id not provided")
        self.assertEquals(checklist.name, name)
        checklist.rename('Renamed')
        self.assertEquals(checklist.name, 'Renamed')

    def test54_set(self):
        name = "Testing from Python"
        description = "Description goes here"
        card = self._list.add_card('noname')
        card.set_name(name)
        card.set_description(description)
        self.assertEquals(card.name, name)
        self.assertEquals(card.description, description)

    def test60_delete_cards(self):
        cards = self._board.get_cards()
        for card in cards:
            card.delete()

    def test70_all_members(self):
        self.assertTrue(len(self._board.all_members()) > 0)

    def test71_normal_members(self):
        self.assertTrue(len(self._board.normal_members()) >= 0)

    def test72_admin_members(self):
        self.assertTrue(len(self._board.admin_members()) > 0)

    def test73_owner_members(self):
        members = self._board.owner_members()
        self.assertTrue(len(members) > 0)
        member = members[0].fetch()
        self.assertNotEqual(member.status, None)
        self.assertNotEqual(member.id, None)
        self.assertNotEqual(member.bio, None)
        self.assertNotEqual(member.url, None)
        self.assertNotEqual(member.username, None)
        self.assertNotEqual(member.full_name, None)
        self.assertNotEqual(member.initials, None)
        member2 = self._trello.get_member(member.id)
        self.assertEqual(member.username, member2.username)

    def test80_unauthorized(self):
        client = TrelloClient('a')
        self.assertRaises(Unauthorized,
                          client.list_boards)

    def test81_resource_unavailable(self):
        self.assertRaises(ResourceUnavailable,
                          self._trello.get_card, '0')

    def test90_get_board(self):
        board = self._trello.get_board(self._board.id)
        self.assertEqual(self._board.name, board.name)


def suite():
    # tests = ['test01_list_boards', 'test10_board_attrs', 'test20_add_card']
    # return unittest.TestSuite(map(TrelloBoardTestCase, tests))
    return unittest.TestLoader().loadTestsFromTestCase(TrelloBoardTestCase)

if __name__ == "__main__":
    unittest.main()