from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.inventory_item import InventoryItem
from app.models.warehouse_location import WarehouseLocation
from app.repositories.base_repository import BaseRepository


class InventoryRepository(BaseRepository[InventoryItem]):
    def __init__(self, db: Session, tenant_id: int):
        super().__init__(InventoryItem, db, tenant_id=tenant_id)

    def list_locations(self) -> List[WarehouseLocation]:
        return self.db.query(WarehouseLocation).filter(WarehouseLocation.company_id == self.tenant_id).all()
