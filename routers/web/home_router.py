import common.template_config as template_config
from fastapi import APIRouter, Request

web_home_router = APIRouter()
templates = template_config.CustomJinja2Templates(directory='templates')

@web_home_router.get('/')
def serve_index(request: Request):
    """
    Render homepage of the application.

    Args:
        request (Request): FastAPI request object.

    Returns:
        HTML homepage template.
    """
    return templates.TemplateResponse(request=request, name="index.html", context={})
