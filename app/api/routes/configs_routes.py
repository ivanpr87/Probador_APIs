from typing import List

from fastapi import APIRouter, HTTPException

from app.models.request_models import OpenAPIImportRequest
from app.models.response_models import OpenAPIImportSummary, SavedConfig, SavedConfigCreate
from app.repositories.configs_repository import delete_config, list_configs, save_config
from app.services.openapi_service import import_openapi_spec

router = APIRouter(prefix="/configs", tags=["configs"])


@router.get("", response_model=List[SavedConfig])
def get_configs() -> List[SavedConfig]:
    return list_configs()


@router.post("", response_model=SavedConfig, status_code=201)
def create_config(data: SavedConfigCreate) -> SavedConfig:
    try:
        return save_config(data)
    except Exception as e:
        if "UNIQUE constraint" in str(e):
            raise HTTPException(status_code=409, detail=f"Config name '{data.name}' already exists")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import-openapi", response_model=OpenAPIImportSummary, status_code=201)
def import_openapi(data: OpenAPIImportRequest) -> OpenAPIImportSummary:
    try:
        summary = import_openapi_spec(
            data.spec,
            base_url_override=data.base_url,
            name_prefix=data.name_prefix,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    if not summary.created and summary.errors:
        raise HTTPException(status_code=422, detail=summary.errors)

    return summary


@router.delete("/{config_id}", status_code=204)
def remove_config(config_id: int) -> None:
    if not delete_config(config_id):
        raise HTTPException(status_code=404, detail="Config not found")
