from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from foxops.dependencies import hoster_token_auth_scheme, get_hoster_auth_router

#: Holds the router for the version endpoint
router = APIRouter(prefix="/auth", tags=["authentication"])

# here we include the hoster authentication router, will use /auth prefix
router.include_router(get_hoster_auth_router())


# FIXME: we probably can get rid of it now...
@router.get("/test", response_class=PlainTextResponse, dependencies=[Depends(hoster_token_auth_scheme)])
def test_authentication_route():
    return "OK"
