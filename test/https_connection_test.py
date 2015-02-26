__author__ = 'Gavin Ballard (gavin@gavinballard.com)'


from .connection_test import ConnectionTest
from pyactiveresource import connection


class HTTPSConnectionTest(ConnectionTest):
    """
    This class subclasses the ConnectionTest and runs all of the same tests, but does it over HTTPS rather than HTTP.
    """

    def setUp(self):
        super(HTTPSConnectionTest, self).setUp()
        # Override the base site URL and re-create the connection.
        self.http.site = 'https://localhost'
        self.connection = connection.Connection(self.http.site)
