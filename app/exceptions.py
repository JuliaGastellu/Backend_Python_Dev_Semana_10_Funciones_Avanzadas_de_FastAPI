class PulseError(Exception):
    error_code = "PULSE_ERROR"

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class NotFoundError(PulseError):
    error_code = "NOT_FOUND"


class DuplicateError(PulseError):
    error_code = "DUPLICATE"


class InUseError(PulseError):
    error_code = "IN_USE"


class UnauthorizedError(PulseError):
    error_code = "UNAUTHORIZED"


class ForbiddenError(PulseError):
    error_code = "FORBIDDEN"


STATUS_BY_ERROR = {"NOT_FOUND": 404, "DUPLICATE": 409, "IN_USE": 409, "UNAUTHORIZED": 401, "FORBIDDEN": 403}


def register_exception_handlers(app) -> None:
    from fastapi import Request
    from fastapi.responses import JSONResponse

    @app.exception_handler(PulseError)
    async def pulse_error_handler(_request: Request, exc: PulseError) -> JSONResponse:
        status_code = STATUS_BY_ERROR.get(exc.error_code, 400)
        return JSONResponse(status_code=status_code, content={"detail": exc.detail, "error_code": exc.error_code, "status_code": status_code})

