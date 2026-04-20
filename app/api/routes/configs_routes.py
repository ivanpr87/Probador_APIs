from typing import List

from fastapi import APIRouter, HTTPException

from app.models.response_models import SavedConfig, SavedConfigCreate
from app.repositories.configs_repository import delete_config, list_configs, save_config

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


@router.delete("/{config_id}", status_code=204)
def remove_config(config_id: int) -> None:
    if not delete_config(config_id):
        raise HTTPException(status_code=404, detail="Config not found")
