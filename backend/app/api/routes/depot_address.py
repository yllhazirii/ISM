from fastapi import APIRouter, HTTPException
from sqlmodel import func, select
from typing import Any
# Assuming these dependencies are available:
from app.api.deps import CurrentUser, SessionDep
from app.models.models_depot import (
    DepotAddressPrice,
    DepotAddressPriceCreate,
    DepotAddressPriceUpdate,
    DepotAddressPricePublic,
    DepotAddressPriceList,
    Message
)

router = APIRouter(prefix="/depotaddress", tags=["DepotAddressPrice"])

# ----------------------------------------------------------------------

@router.get("/", response_model=DepotAddressPriceList)
def read_depot_addr_prices(session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve all DepotAddressPrice entries.
    """
    # Count the total number of items
    count_statement = select(func.count()).select_from(DepotAddressPrice)
    count = session.exec(count_statement).one()

    # Retrieve the items with offset and limit
    statement = select(DepotAddressPrice).order_by(DepotAddressPrice.instance_id).offset(skip).limit(limit)
    items = session.exec(statement).all()

    # Return the data in the list format
    return DepotAddressPriceList(data=items, count=count)

# ----------------------------------------------------------------------

@router.get("/{instance_id}", response_model=DepotAddressPricePublic)
def read_depot_addr_price_by_id(session: SessionDep, current_user: CurrentUser, instance_id: int) -> Any:
    """
    Get a specific DepotAddressPrice entry by its instance_id.
    """
    item = session.get(DepotAddressPrice, instance_id)
    if not item:
        raise HTTPException(status_code=404, detail="DepotAddressPrice not found")
    return item

# ----------------------------------------------------------------------

@router.post("/", response_model=DepotAddressPricePublic)
def create_depot_addr_price(*, session: SessionDep, current_user: CurrentUser, item_in: DepotAddressPriceCreate) -> Any:
    """
    Create a new DepotAddressPrice entry.
    """
    item = DepotAddressPrice.model_validate(item_in)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

# ----------------------------------------------------------------------

@router.put("/{instance_id}", response_model=DepotAddressPricePublic)
def update_depot_addr_price(*, session: SessionDep, current_user: CurrentUser, instance_id: int, item_in: DepotAddressPriceUpdate) -> Any:
    """
    Update an existing DepotAddressPrice entry.
    """
    item = session.get(DepotAddressPrice, instance_id)
    if not item:
        raise HTTPException(status_code=404, detail="DepotAddressPrice not found")

    # Update the model with provided fields
    update_dict = item_in.model_dump(exclude_unset=True)
    item.sqlmodel_update(update_dict)

    session.add(item)
    session.commit()
    session.refresh(item)
    return item

# ----------------------------------------------------------------------

@router.delete("/{instance_id}", response_model=Message)
def delete_depot_addr_price(session: SessionDep, current_user: CurrentUser, instance_id: int) -> Message:
    """
    Delete a DepotAddressPrice entry by its instance_id.
    """
    item = session.get(DepotAddressPrice, instance_id)
    if not item:
        raise HTTPException(status_code=404, detail="DepotAddressPrice not found")

    session.delete(item)
    session.commit()
    return Message(message=f"DepotAddressPrice with ID {instance_id} deleted successfully")