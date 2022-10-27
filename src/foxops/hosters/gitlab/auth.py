from functools import cache
from starlette.config import Config
from authlib.integrations.starlette_client import OAuth  # type: ignore
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from .settings import get_gitlab_settings

settings = get_gitlab_settings()

config: Config = Config(
    environ={
        'GITLAB_CLIENT_ID': settings.client_id,
        'GITLAB_CLIENT_SECRET': settings.client_secret.get_secret_value()
    }
)

oauth = OAuth(config)

conf_url = f"{settings.address}/.well-known/openid-configuration"
oauth.register(
    name='gitlab',
    server_metadata_url=conf_url,
    client_kwargs={
        'scope': 'api'
    }
)

#: Holds the router for the gitlab authentication endpoints
router = APIRouter()


@router.get("/token")
async def token(request: Request):
    redirect_uri = request.url_for('auth_redirect')
    return await oauth.gitlab.authorize_redirect(request, redirect_uri)  # type: ignore


@router.get('/redirect', include_in_schema=False)
async def auth_redirect(request: Request) -> JSONResponse:
    token: str = await oauth.gitlab.authorize_access_token(request)  # type: ignore
    return JSONResponse(token)


@cache
def get_gitlab_auth_router() -> APIRouter:
    return router
