import common.template_config as template_config
from fastapi import APIRouter, Request

web_home_router = APIRouter()
templates = template_config.CustomJinja2Templates(directory='templates')

@web_home_router.get('/')
def serve_index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})
