from fastapi import APIRouter, Depends
from fastapi_events.dispatcher import dispatch
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.ormar import paginate

from app.scopes.enums import ScopesEventsEnum
from app.scopes.models import Scope
from app.scopes.schemas import ScopeOut
from app.scopes.utils import _get_scopes

router = APIRouter()


@router.get("", response_model=Page[ScopeOut], response_model_exclude_none=True)
async def get_all_scopes(params: Params = Depends(), role_id: int = None) -> AbstractPage[ScopeOut]:
    """
    Get all scopes

    :param params:
    :param role_id:
    :return:
    """
    dispatch(ScopesEventsEnum.GET_ALL_PRE, payload={"data": {"params": params, "role_id": role_id}})
    scopes = await _get_scopes(params, role_id)
    dispatch(ScopesEventsEnum.GET_ALL_POST, payload={"data": scopes})
    return scopes
