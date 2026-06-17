class DbOperationError(Exception):
    pass


class DbConflictError(DbOperationError):
    pass


class DbUnavailableError(DbOperationError):
    pass
