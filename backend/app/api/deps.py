from __future__ import annotations
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import decode_token
from app.models.entities import OrganizationMember, Role, User

bearer = HTTPBearer(auto_error=False)

ROLE_RANK = {
    "Viewer": 1,
    "Reviewer": 2,
    "Operations Manager": 3,
    "Compliance Manager": 4,
    "Admin": 5,
}


class AuthContext:
    def __init__(self, user: User, membership: OrganizationMember, role: Role):
        self.user = user
        self.membership = membership
        self.role = role
        self.organization_id = membership.organization_id
        self.role_name = role.name


def get_current(creds: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> AuthContext:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    try:
        payload = decode_token(creds.credentials)
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    user = db.get(User, payload.get("sub"))
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid user")
    membership = db.get(OrganizationMember, payload.get("membership_id"))
    if not membership or membership.user_id != user.id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid membership")
    role = db.get(Role, membership.role_id)
    return AuthContext(user, membership, role)


def require_roles(*names: str):
    def _inner(auth: AuthContext = Depends(get_current)) -> AuthContext:
        if auth.role_name not in names and auth.role_name != "Admin":
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient role")
        return auth

    return _inner


def org_owned(obj, auth: AuthContext) -> None:
    if getattr(obj, "organization_id", None) != auth.organization_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
