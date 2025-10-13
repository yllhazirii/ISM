from sqlmodel import SQLModel, Field
from datetime import datetime

class DepotMasterBase(SQLModel):
    vendor: str | None = Field(default=None, max_length=255)
    depot: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=255)
    customer: str | None = Field(default=None, max_length=255)
    invoice: str | None = Field(default=None, max_length=255)
    ven_invoice_number: str | None = Field(default=None, max_length=255)
    po_number: str | None = Field(default=None, max_length=255)
    acceptance_number: str | None = Field(default=None, max_length=255)
    release_number: str | None = Field(default=None, max_length=255)
    container_number: str | None = Field(default=None, max_length=255)
    type: str | None = Field(default=None, max_length=255)
    condition: str | None = Field(default=None, max_length=255)
    flp: str | None = Field(default=None, max_length=255)
    lb: str | None = Field(default=None, max_length=255)
    color: str | None = Field(default=None, max_length=255)
    berth_eta: datetime | None = Field(default=None)
    gate_in_date: datetime | None = Field(default=None)
    pc: str | None = Field(default=None, max_length=255)
    puc: str | None = Field(default=None, max_length=255)
    price: float | None = Field(default=None)
    damage: float | None = Field(default=None)
    approved: str | None = Field(default=None, max_length=255)
    price_after_damage: float | None = Field(default=None)
    gate_out_date: datetime | None = Field(default=None)

class DepotMasterCreate(DepotMasterBase):
    pass

class DepotMasterUpdate(DepotMasterBase):
    pass

class DepotMasterPublic(DepotMasterBase):
    instance_id: int

class DepotMasterList(SQLModel):
    data: list[DepotMasterPublic]
    count: int

class DepotMaster(DepotMasterBase, table=True):
    instance_id: int = Field(default_factory=int, primary_key=True)

class Message(SQLModel):
    message: str

class GateOutBase(SQLModel):
    city: str | None = Field(default=None, max_length=255)
    customer: str | None = Field(default=None, max_length=255)
    ism_order_number: str | None = Field(default=None, max_length=255)
    ven_invoice_number: str | None = Field(default=None, max_length=255)
    po_number: str | None = Field(default=None, max_length=255)
    acceptance_number: str | None = Field(default=None, max_length=255)
    release_number: str | None = Field(default=None, max_length=255)
    container_number: str | None = Field(default=None, max_length=255)
    type: str | None = Field(default=None, max_length=255)
    condition: str | None = Field(default=None, max_length=255)
    flp: str | None = Field(default=None, max_length=255)
    lb: str | None = Field(default=None, max_length=255)
    color: str | None = Field(default=None, max_length=255)
    berth_eta: datetime | None = Field(default=None)
    gate_in_date: datetime | None = Field(default=None)
    pc: str | None = Field(default=None, max_length=255)
    puc: str | None = Field(default=None, max_length=255)
    price: float | None = Field(default=None)
    damage: float | None = Field(default=None)
    approved: str | None = Field(default=None, max_length=255)
    price_after_damage: float | None = Field(default=None)
    gate_out_date: datetime | None = Field(default=None)

class GateOutCreate(GateOutBase):
    pass

class GateOutUpdate(GateOutBase):
    pass

class GateOutPublic(GateOutBase):
    instance_id: int

class GateOutList(SQLModel):
    data: list[GateOutPublic]
    count: int

class GateOut(GateOutBase, table=True):
    instance_id: int = Field(default_factory=int, primary_key=True)

class Message(SQLModel):
    message: str

class DepotAddressPriceBase(SQLModel):
    depot_name: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=255)
    accpt: str | None = Field(default=None, max_length=255)
    rels: str | None = Field(default=None, max_length=255)
    contact_name: str | None = Field(default=None, max_length=255)
    phone_number: str | None = Field(default=None, max_length=255)
    gate_in: float | None = Field(default=None)
    gate_out: float | None = Field(default=None)
    lift_on: float | None = Field(default=None)
    lift_off: float | None = Field(default=None)
    mr_labor_hr: float | None = Field(default=None)
    split: float | None = Field(default=None)
    ten_std: float | None = Field(default=None)
    twenty_duo: float | None = Field(default=None)
    twenty_std: float | None = Field(default=None)
    twenty_hc: float | None = Field(default=None)
    forty_std: float | None = Field(default=None)
    forty_hc: float | None = Field(default=None)
    forty_hcdd: float | None = Field(default=None)
    forty_five: float | None = Field(default=None)
    fifty_three: float | None = Field(default=None)
    address: str | None = Field(default=None, max_length=255)
    email_1: str | None = Field(default=None, max_length=255)
    email_2: str | None = Field(default=None, max_length=255)
    fab_split: str | None = Field(default=None, max_length=255)

class DepotAddressPriceCreate(DepotAddressPriceBase):
    pass

class DepotAddressPriceUpdate(DepotAddressPriceBase):
    pass

class DepotAddressPricePublic(DepotAddressPriceBase):
    instance_id: int

class DepotAddressPriceList(SQLModel):
    data: list[DepotAddressPricePublic]
    count: int

class DepotAddressPrice(DepotAddressPriceBase, table=True):
    instance_id: int = Field(default_factory=int, primary_key=True)

class Message(SQLModel):
    message: str
