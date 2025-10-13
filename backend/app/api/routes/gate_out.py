from fastapi import APIRouter, HTTPException
from sqlmodel import func, select
from typing import Any
# Assuming these dependencies are available:
from app.api.deps import CurrentUser, SessionDep
from app.models.models_depot import (
    GateOut,
    GateOutCreate,
    GateOutUpdate,
    GateOutPublic,
    GateOutList,
    Message
)

router = APIRouter(prefix="/gateout", tags=["GateOut"])

# ----------------------------------------------------------------------

@router.get("/", response_model=GateOutList)
def read_gate_outs(session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve all GateOut entries.
    """
    # Count the total number of items
    count_statement = select(func.count()).select_from(GateOut)
    count = session.exec(count_statement).one()

    # Retrieve the items with offset and limit
    statement = select(GateOut).order_by(GateOut.instance_id).offset(skip).limit(limit)
    items = session.exec(statement).all()

    # Return the data in the list format
    return GateOutList(data=items, count=count)

# ----------------------------------------------------------------------

@router.get("/{instance_id}", response_model=GateOutPublic)
def read_gate_out_by_id(session: SessionDep, current_user: CurrentUser, instance_id: int) -> Any:
    """
    Get a specific GateOut entry by its instance_id.
    """
    item = session.get(GateOut, instance_id)
    if not item:
        raise HTTPException(status_code=404, detail="GateOut not found")
    return item

# ----------------------------------------------------------------------

@router.post("/", response_model=GateOutPublic)
def create_gate_out(*, session: SessionDep, current_user: CurrentUser, item_in: GateOutCreate) -> Any:
    """
    Create a new GateOut entry.
    """
    item = GateOut.model_validate(item_in)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

# ----------------------------------------------------------------------

@router.put("/{instance_id}", response_model=GateOutPublic)
def update_gate_out(*, session: SessionDep, current_user: CurrentUser, instance_id: int, item_in: GateOutUpdate) -> Any:
    """
    Update an existing GateOut entry.
    """
    item = session.get(GateOut, instance_id)
    if not item:
        raise HTTPException(status_code=404, detail="GateOut not found")

    # Update the model with provided fields
    update_dict = item_in.model_dump(exclude_unset=True)
    item.sqlmodel_update(update_dict)

    session.add(item)
    session.commit()
    session.refresh(item)
    return item

# ----------------------------------------------------------------------

@router.delete("/{instance_id}", response_model=Message)
def delete_gate_out(session: SessionDep, current_user: CurrentUser, instance_id: int) -> Message:
    """
    Delete a GateOut entry by its instance_id.
    """
    item = session.get(GateOut, instance_id)
    if not item:
        raise HTTPException(status_code=404, detail="GateOut not found")

    session.delete(item)
    session.commit()
    return Message(message=f"GateOut with ID {instance_id} deleted successfully")