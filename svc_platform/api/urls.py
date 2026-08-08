"""
Стандартные эндпоинты сервера
"""


class Urls:
    def __init__(self, port: int = 8000, host: str = 'localhost'):
        self._base_url = f'http://{host}:{port}'
        # system
        self.shutdown = self._base_url + '/shutdown/'
        self.health = self._base_url + '/health/'
        # engine start/stop
        self.start = self._base_url + '/start/'
        self.stop = self._base_url + '/stop/'
        self.parameters = self._base_url + '/parameters/'
        # Process
        self.process = self._base_url + '/process/'
        self.process_result = self._base_url + '/process_result/'
        self.process_stop = self._base_url + '/process_stop/'
        # Execute
        self.execute = self._base_url + '/execute/'
        self.execute_stop = self._base_url + '/execute_stop/'
