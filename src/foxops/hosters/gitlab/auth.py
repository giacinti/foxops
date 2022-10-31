from typing import Optional, Dict
from pydantic import AnyUrl
from functools import cache
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth, OAuthError  # type: ignore
from fastapi import APIRouter, Request, HTTPException, status, Depends
from foxops.jwt import get_jwt_settings, create_access_token
from .settings import GitLabSettings, get_gitlab_settings

#: Holds the router for the gitlab authentication endpoints
router = APIRouter()


def get_oauth_gitlab(settings: GitLabSettings = Depends(get_gitlab_settings)):
    oauth = OAuth()

    conf_url = f"{settings.address}/.well-known/openid-configuration"
    oauth.register(
        name='gitlab',
        server_metadata_url=conf_url,
        client_id=settings.client_id,
        client_secret=settings.client_secret.get_secret_value(),
        client_kwargs={
            'scope': settings.client_scope
        }
    )
    return oauth.gitlab


@router.get('/login')
async def login(request: Request,
                redirect_uri: Optional[AnyUrl] = None,
                gitlab=Depends(get_oauth_gitlab),
                ) -> RedirectResponse:
    redir: str = request.url_for('token')
    if redirect_uri:
        redir = str(redirect_uri)
    return await gitlab.authorize_redirect(request, redir)  # type: ignore


@router.get('/token')
async def token(request: Request,
                gitlab=Depends(get_oauth_gitlab),
                jwt_settings=Depends(get_jwt_settings),
                ) -> str:
    try:
        access_token: Dict = await gitlab.authorize_access_token(request)  # type: ignore
    except OAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"{e}",
            headers={'WWW-Authenticate': 'Bearer'},
        )
    data = {
        'token_type': 'Bearer',
        'hoster_token': access_token['access_token'],
        'refresh_token': access_token['refresh_token'],
        'user_email': access_token['userinfo']['email']
    }
    return create_access_token(settings=jwt_settings, data=data)


@cache
def get_gitlab_auth_router() -> APIRouter:
    return router
