from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from foxops.dependencies import hoster_token_auth_scheme, get_hoster_auth_router

#: Holds the router for the version endpoint
router = APIRouter(prefix="/auth", tags=["authentication"])

router.include_router(get_hoster_auth_router())


@router.get("/test", response_class=PlainTextResponse, dependencies=[Depends(hoster_token_auth_scheme)])
def test_authentication_route():
    return "OK"
