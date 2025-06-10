from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import Request
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    messages = []
    for err in errors:
        loc = " -> ".join(str(i) for i in err["loc"] if i != "body")
        msg = f"{loc}: {err['msg']}"
        messages.append(msg)
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": messages}
    )
