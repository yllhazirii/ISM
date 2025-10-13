from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select
from app.api.deps import CurrentUser, SessionDep # Assuming these dependencies are available
from app.models.models_depot import (
    DepotMaster,
    DepotMasterCreate,
    DepotMasterUpdate,
    DepotMasterPublic,
    DepotMasterList,
    Message
)

router = APIRouter(prefix="/depotmaster", tags=["DepotMaster"])

@router.get("/", response_model=DepotMasterList)
def read_depot_masters(session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve all DepotMaster entries.
    """
    # Count the total number of items
    count_statement = select(func.count()).select_from(DepotMaster)
    count = session.exec(count_statement).one()

    # Retrieve the items with offset and limit
    statement = select(DepotMaster).order_by(DepotMaster.instance_id).offset(skip).limit(limit)
    items = session.exec(statement).all()

    # Return the data in the list format
    return DepotMasterList(data=items, count=count)

# ----------------------------------------------------------------------

@router.get("/{instance_id}", response_model=DepotMasterPublic)
def read_depot_master_by_id(session: SessionDep, current_user: CurrentUser, instance_id: int) -> Any:
    """
    Get a specific DepotMaster entry by its instance_id.
    """
    # Use the primary key name from the model (instance_id)
    item = session.get(DepotMaster, instance_id)
    if not item:
        raise HTTPException(status_code=404, detail="DepotMaster not found")
    return item

# ----------------------------------------------------------------------

@router.post("/", response_model=DepotMasterPublic)
def create_depot_master(*, session: SessionDep, current_user: CurrentUser, item_in: DepotMasterCreate) -> Any:
    """
    Create a new DepotMaster entry.
    """
    # Validate the input model and create the database object
    item = DepotMaster.model_validate(item_in)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

# ----------------------------------------------------------------------

@router.put("/{instance_id}", response_model=DepotMasterPublic)
def update_depot_master(*, session: SessionDep, current_user: CurrentUser, instance_id: int, item_in: DepotMasterUpdate) -> Any:
    """
    Update an existing DepotMaster entry.
    """
    # Fetch the existing item
    item = session.get(DepotMaster, instance_id)
    if not item:
        raise HTTPException(status_code=404, detail="DepotMaster not found")

    # Update the model with provided fields
    update_dict = item_in.model_dump(exclude_unset=True)
    item.sqlmodel_update(update_dict)

    session.add(item)
    session.commit()
    session.refresh(item)
    return item

# ----------------------------------------------------------------------

@router.delete("/{instance_id}", response_model=Message)
def delete_depot_master(session: SessionDep, current_user: CurrentUser, instance_id: int) -> Message:
    """
    Delete a DepotMaster entry by its instance_id.
    """
    # Fetch the existing item
    item = session.get(DepotMaster, instance_id)
    if not item:
        raise HTTPException(status_code=404, detail="DepotMaster not found")

    session.delete(item)
    session.commit()
    return Message(message=f"DepotMaster with ID {instance_id} deleted successfully")