from werkzeug.routing import BaseConverter


class RegexConverter(BaseConverter):
    """
    Enables flask to use regex as a url route qualifier
    """
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]
