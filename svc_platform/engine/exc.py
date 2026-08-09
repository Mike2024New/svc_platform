class EngineExc:
    class StartError(RuntimeError):
        pass

    class StopError(RuntimeError):
        pass

    class ProcessResultNotCompleted(RuntimeError):
        pass

    class ProcessResultNoFindReqestId(RuntimeError):
        pass

    class ProcessCancelled(RuntimeError):
        pass

    class ProcessLimit(RuntimeError):
        pass

    class ProcessRequestIdAlreadyExists(RuntimeError):
        pass

    class ExecuteNoFindReqestId(RuntimeError):
        pass

    class ExecuteLimit(RuntimeError):
        pass

    class ExecuteRequestIdAlreadyExists(RuntimeError):
        pass

    class StreamRequestIdAlreadyExists(RuntimeError):
        pass

    class StreamNoFindReqestId(RuntimeError):
        pass
