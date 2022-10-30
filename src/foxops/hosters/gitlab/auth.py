from typing import Optional, Dict
from pydantic import AnyUrl, ValidationError
from functools import cache
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth, OAuthError  # type: ignore
from authlib.oidc.core.claims import UserInfo  # type: ignore
from fastapi import APIRouter, Request, Depends

from foxops.models import User
from foxops.jwt import JWTTokenData, get_jwt_settings, create_jwt_token
from foxops.auth import AuthHTTPException, AuthData
from foxops.logger import get_logger

from .settings import GitLabSettings, get_gitlab_settings

#: Holds the module logger
logger = get_logger(__name__)

#: Holds the router for the gitlab authentication endpoints
router = APIRouter()

#: Hold static OAuth registry instance
oauth = OAuth()


def get_oauth_gitlab(settings: GitLabSettings = Depends(get_gitlab_settings)):
    conf_url = f"{settings.address}/.well-known/openid-configuration"
    # object is cached in OAuth registry
    return oauth.register(
        name='gitlab',
        server_metadata_url=conf_url,
        client_id=settings.client_id,
        client_secret=settings.client_secret.get_secret_value(),
        client_kwargs={
            'scope': settings.client_scope
        }
    )


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
                code: str,  # not used but here for proper openapi documentation
                state: str,  # idem
                gitlab=Depends(get_oauth_gitlab),
                jwt_settings=Depends(get_jwt_settings),
                ) -> str:
    try:
        access_token: Dict = await gitlab.authorize_access_token(request)  # type: ignore
        user_info: UserInfo = await gitlab.userinfo(token=access_token)
        user = User(**user_info)
        # TODO: get scopes from database?
        user.scopes = ['user']
        await AuthData.register(
            AuthData(
                user=user,
                hoster_token=access_token['access_token'],
                refresh_token=access_token['refresh_token']
            )
        )
    except (OAuthError, ValidationError) as e:
        raise AuthHTTPException(detail=f"{e}")

    data = JWTTokenData(sub=user.email, scopes=user.scopes)
    return create_jwt_token(settings=jwt_settings, data=data)


@cache
def get_gitlab_auth_router() -> APIRouter:
    return router
