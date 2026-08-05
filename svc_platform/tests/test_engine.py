def test_engine_base(test_engine):
    assert test_engine.parameters['running'] == False
    test_engine.start()
    assert test_engine.parameters['running'] == True
    test_engine.stop()

def test_engine_double_start(test_engine):
    test_engine.start()
    test_engine.start()
    assert test_engine.parameters['running'] == True
    test_engine.stop()