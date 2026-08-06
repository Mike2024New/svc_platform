class EngineExc:
    class ProcessResultNotCompleted(RuntimeError):
        pass

    class ProcessResultNoFindReqestId(RuntimeError):
        pass

    class ProcessCancelled(RuntimeError):
        pass
