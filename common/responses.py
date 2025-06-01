from typing import Any, Mapping
from fastapi import Response
from starlette.background import BackgroundTask
class BadRequest(Response):
    def __init__(self, content=''):
        super().__init__(status_code=400, content=content)


class NotFound(Response):
    def __init__(self, content=''):
        super().__init__(status_code=404, content=content)


class Unauthorized(Response):
    def __init__(self, content=''):
        super().__init__(status_code=401, content=content)


class NoContent(Response):
    def __init__(self):
        super().__init__(status_code=204)


class InternalServerError(Response):
    def __init__(self):
        super().__init__(status_code=500)
        
class Created(Response):
    def __init__(self, content=''):
        super().__init__(status_code=201, content=content)

class ServiceUnavailable(Response):
    def __init__(self, content=''):
        super().__init__(status_code=503, content=content)
        
class OK(Response):
    def __init__(self, content=''):
        super().__init__(status_code=200, content=content)