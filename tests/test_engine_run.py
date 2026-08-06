"""
Тесты запуска и остановки движка.
start  - загружает тяжелый движок (например llama-cpp, whisper и так далее)
stop   - остановка движка (высвобождение ресурсов)
"""


def test_start_stop(test_engine):
    engine, example_settings, *_ = test_engine
    assert engine.parameters['running'] == False
    engine.start()
    assert engine.parameters['running'] == True
    engine.stop()


def test_double_start(test_engine):
    engine, example_settings, *_ = test_engine
    engine.start()
    engine.start()
    assert engine.parameters['running'] == True
    engine.stop()
