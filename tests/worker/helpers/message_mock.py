class MessageMock(dict):
    """Class to mock the queuing messages for
    the purpose of passing data during testing
    """

    def __init__(self, *args, **kwargs):
        super(MessageMock, self).__init__(*args, **kwargs)
        self.__dict__ = self

    def delete(self):
        pass
