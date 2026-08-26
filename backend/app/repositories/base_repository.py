from typing import TypeVar, Generic, Type, Optional, List, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from app.core.database import Base
from app.core.exceptions import TenantIsolationException

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic Repository with mandatory tenant_id isolation.
    Every query MUST receive and enforce tenant_id (company_id).
    """

    def __init__(self, model: Type[ModelType], db: Session, tenant_id: int):
        if tenant_id is None:
            raise TenantIsolationException("tenant_id is strictly required for data operations")
        self.model = model
        self.db = db
        self.tenant_id = tenant_id

    def _tenant_query(self):
        """Returns base query strictly scoped to current tenant"""
        if hasattr(self.model, "company_id"):
            return self.db.query(self.model).filter(self.model.company_id == self.tenant_id)
        # For non-tenant models like Company table, match id directly
        if hasattr(self.model, "id"):
            return self.db.query(self.model).filter(self.model.id == self.tenant_id)
        return self.db.query(self.model)

    def get_by_id(self, record_id: int) -> Optional[ModelType]:
        """Fetch a single record by ID with strict tenant scoping"""
        return self._tenant_query().filter(self.model.id == record_id).first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by_col: Optional[str] = None,
        ascending: bool = False
    ) -> List[ModelType]:
        """Fetch records for current tenant with pagination and ordering"""
        query = self._tenant_query()
        if order_by_col and hasattr(self.model, order_by_col):
            col = getattr(self.model, order_by_col)
            query = query.order_by(asc(col) if ascending else desc(col))
        elif hasattr(self.model, "created_at"):
            query = query.order_by(desc(self.model.created_at))
        return query.offset(skip).limit(limit).all()

    def create(self, obj_in: Dict[str, Any]) -> ModelType:
        """Create a new record, automatically attaching tenant_id"""
        data = obj_in.copy()
        if hasattr(self.model, "company_id"):
            data["company_id"] = self.tenant_id
        db_obj = self.model(**data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, db_obj: ModelType, obj_in: Dict[str, Any]) -> ModelType:
        """Update an existing record after confirming tenant ownership"""
        if hasattr(db_obj, "company_id") and db_obj.company_id != self.tenant_id:
            raise TenantIsolationException("Cannot modify record belonging to another tenant")
        
        for field, value in obj_in.items():
            if field not in ("id", "company_id") and hasattr(db_obj, field) and value is not None:
                setattr(db_obj, field, value)
        
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, record_id: int) -> bool:
        """Delete a record by ID with strict tenant scoping"""
        db_obj = self.get_by_id(record_id)
        if not db_obj:
            return False
        self.db.delete(db_obj)
        self.db.commit()
        return True

    def count(self) -> int:
        """Count records for current tenant"""
        return self._tenant_query().count()
