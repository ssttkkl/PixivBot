class PixivResultError(Exception):
    def __init__(self, err_result):
        self.err_result = err_result
        self.user_message = err_result["user_message"]
        self.message = err_result["message"]
        self.reason = err_result["reason"]
        self.user_message_details = err_result["user_message_details"]
        super(Exception, self).__init__(self, err_result)

    def error(self) -> str:
        if self.user_message != "":
            return self.user_message
        elif self.message != "":
            return self.message
        elif self.reason != "":
            return self.reason
        elif self.user_message_details != "":
            return self.user_message_details
        else:
            return "unknown error"
