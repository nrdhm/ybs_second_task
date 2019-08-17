class InvalidUsage(Exception):
    def __init__(self, message, status_code=500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

    @staticmethod
    def not_found(msg='Не найдено'):
        return InvalidUsage(msg, status_code=404)

    @staticmethod
    def bad_request(msg='Неправильный запрос'):
        return InvalidUsage(msg, status_code=400)
