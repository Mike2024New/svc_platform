class EngineExc:
    # ============ START ====================
    class StartError(RuntimeError):
        pass

    # ============ STOP ====================

    class StopError(RuntimeError):
        pass

    # ============ EXECUTE ====================

    class ExecuteNoFindReqestId(RuntimeError):
        pass

    class ExecuteRequestIdAlreadyExists(RuntimeError):
        pass

    # ============ PROCESS ====================

    class ProcessNoFindReqestId(RuntimeError):
        pass

    class ProcessRequestIdAlreadyExists(RuntimeError):
        pass

    class ProcessResultNotCompleted(RuntimeError):
        pass

    class ProcessStorageLimit(RuntimeError):
        pass

    # ============ STREAM ====================

    class StreamNoFindReqestId(RuntimeError):
        pass

    class StreamRequestIdAlreadyExists(RuntimeError):
        pass
