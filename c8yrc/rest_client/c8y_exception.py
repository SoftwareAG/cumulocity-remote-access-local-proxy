class C8yException(Exception):

    def __init__(self, msg, original_exception):
        if original_exception:
            my_msg = '{}: {}'.format(msg, original_exception)
        else:
            my_msg = msg
        super(C8yException, self).__init__(my_msg)
        self.original_exception = original_exception
