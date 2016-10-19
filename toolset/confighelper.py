import json

__author__ = 'Alfred, S.-Y., Wei'


class Config(dict):
    """
    This class handle custom configuration
    """

    def __init__(self, path):
        """
        Constructor, set the default pathes
        """
        self.path = path
        self.load()

    def load(self):
        with open(self.path, encoding='utf-8') as fin:
            self.update(json.load(fin))
