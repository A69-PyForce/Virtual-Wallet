from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exception_handlers import RequestValidationError
from common.template_config import CustomJinja2Templates
from fastapi.responses import JSONResponse
from fastapi import Request

templates = CustomJinja2Templates(directory="templates")

def is_api_request(request: Request) -> bool:
    return request.url.path.startswith("/api")

async def not_found(request: Request, exc: StarletteHTTPException):
    if is_api_request(request):
        return JSONResponse({"detail": "Page Not Found"}, status_code=404)
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error_title": "Page Not Found",
            "error_message": "The page you're looking for doesn't exist or has been moved.",
            "error_details": f"Path: {request.url.path}"
        },
        status_code=404
    )

async def bad_request(request: Request, exc: StarletteHTTPException):
    if is_api_request(request):
        return JSONResponse({"detail": "Bad Request"}, status_code=400)
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error_title": "Bad Request",
            "error_message": "The server couldn't understand your request. Please check your input and try again.",
            "error_details": str(exc.detail) if hasattr(exc, 'detail') else None
        },
        status_code=400
    )

async def unauthorized(request: Request, exc: StarletteHTTPException):
    if is_api_request(request):
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error_title": "Unauthorized",
            "error_message": "Please log in to access this page.",
            "error_details": None
        },
        status_code=401
    )

async def forbidden(request: Request, exc: StarletteHTTPException):
    if is_api_request(request):
        return JSONResponse({"detail": "Forbidden"}, status_code=403)
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error_title": "Access Denied",
            "error_message": "You don't have permission to access this page.",
            "error_details": str(exc.detail) if hasattr(exc, 'detail') else None
        },
        status_code=403
    )

async def method_not_allowed(request: Request, exc: StarletteHTTPException):
    if is_api_request(request):
        return JSONResponse({"detail": "Method Not Allowed"}, status_code=405)
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error_title": "Method Not Allowed",
            "error_message": "This operation is not allowed for this resource.",
            "error_details": f"Method: {request.method}\nPath: {request.url.path}"
        },
        status_code=405
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    if is_api_request(request):
        return JSONResponse({"detail": "Unprocessable Content"}, status_code=422)
    
    # Format validation errors in a readable way
    error_details = []
    for error in exc.errors():
        loc = " -> ".join(str(x) for x in error["loc"])
        error_details.append(f"{loc}: {error['msg']}")
    
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error_title": "Validation Error",
            "error_message": "The provided data is invalid. Please check your input and try again.",
            "error_details": "\n".join(error_details)
        },
        status_code=422
    )

async def internal_server_error(request: Request, exc: StarletteHTTPException):
    if is_api_request(request):
        return JSONResponse({"detail": "Internal Server Error"}, status_code=500)
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error_title": "Internal Server Error",
            "error_message": "Something went wrong on our end. Please try again later.",
            "error_details": str(exc.detail) if hasattr(exc, 'detail') else None
        },
        status_code=500
    )

def register_error_handlers(app):
    """Register all error handlers with the FastAPI application"""
    app.exception_handler(404)(not_found)
    app.exception_handler(400)(bad_request)
    app.exception_handler(401)(unauthorized)
    app.exception_handler(403)(forbidden)
    app.exception_handler(405)(method_not_allowed)
    app.exception_handler(RequestValidationError)(validation_exception_handler)
    app.exception_handler(500)(internal_server_error) 