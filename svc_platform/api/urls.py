"""
Стандартные эндпоинты сервера
"""


class Urls:
    def __init__(self, port: int = 8000, host: str = 'localhost'):
        self.host = host
        self.port = port
        self.base_url = f'http://{host}:{port}'
        # system
        self.shutdown = self.base_url + '/shutdown/'
        self.health = self.base_url + '/health/'
        self.pid = self.base_url + '/pid/'
        self.docs = self.base_url + '/docs/'
        # engine start/stop
        self.start = self.base_url + '/start/'
        self.stop = self.base_url + '/stop/'
        self.parameters = self.base_url + '/parameters/'
        # Process
        self.process = self.base_url + '/process/'
        self.process_result = self.base_url + '/process_result/'
        self.process_stop = self.base_url + '/process_stop/'
        # Execute
        self.execute = self.base_url + '/execute/'
        self.execute_stop = self.base_url + '/execute_stop/'
        # Streaming
        self.streaming_ws = f'ws://{host}:{port}/ws'
