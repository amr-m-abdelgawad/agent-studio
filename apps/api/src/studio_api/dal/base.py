from __future__ import annotations

import uuid

from sqlalchemy.orm import Session
from studio_api.auth.dependencies import TenantCtx
from studio_api.errors import APIError


class TenantDAL:
    """Data-access helper that requires an explicit tenant context."""

    def __init__(self, db: Session, tenant: TenantCtx) -> None:
        self.db = db
        self.tenant = tenant

    @property
    def workspace_id(self) -> uuid.UUID:
        return self.tenant.workspace_id

    @property
    def org_id(self) -> uuid.UUID:
        return self.tenant.org_id

    def ensure_workspace(self) -> None:
        if self.tenant.workspace_id is None:
            raise APIError("not_found", "Workspace not found", 404)


def require_tenant_dal(db: Session, tenant: TenantCtx) -> TenantDAL:
    dal = TenantDAL(db, tenant)
    dal.ensure_workspace()
    return dal
