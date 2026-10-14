from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_current
from app.core.db import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.entities import Organization, OrganizationMember, Role, RoleName, User, uid
from app.schemas.common import LoginRequest, RegisterRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


def _ensure_roles(db: Session) -> dict[str, Role]:
    existing = {r.name: r for r in db.scalars(select(Role)).all()}
    for name in RoleName:
        if name.value not in existing:
            role = Role(id=uid(), name=name.value)
            db.add(role)
            existing[name.value] = role
    db.flush()
    return existing


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    if db.scalars(select(User).where(User.email == payload.email.lower())).first():
        raise HTTPException(400, "Email already registered")
    roles = _ensure_roles(db)
    org = Organization(id=uid(), name=payload.organization_name)
    user = User(
        id=uid(),
        email=payload.email.lower(),
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
    )
    db.add_all([org, user])
    db.flush()
    membership = OrganizationMember(
        id=uid(),
        organization_id=org.id,
        user_id=user.id,
        role_id=roles[RoleName.ADMIN.value].id,
    )
    db.add(membership)
    db.commit()
    token = create_access_token(user.id, {"membership_id": membership.id, "org": org.id, "role": RoleName.ADMIN.value})
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalars(select(User).where(User.email == payload.email.lower())).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(401, "Invalid credentials")
    membership = db.scalars(select(OrganizationMember).where(OrganizationMember.user_id == user.id)).first()
    if not membership:
        raise HTTPException(401, "No organization membership")
    role = db.get(Role, membership.role_id)
    token = create_access_token(
        user.id, {"membership_id": membership.id, "org": membership.organization_id, "role": role.name if role else ""}
    )
    return TokenResponse(access_token=token)


from app.core.config import get_settings


@router.get("/me", response_model=UserOut)
def me(auth: AuthContext = Depends(get_current), db: Session = Depends(get_db)) -> UserOut:
    org = db.get(Organization, auth.organization_id)
    settings = get_settings()
    is_demo = (org.name == settings.demo_org_name) if org else False
    return UserOut(
        id=auth.user.id,
        email=auth.user.email,
        full_name=auth.user.full_name,
        organization_id=auth.organization_id,
        organization_name=org.name if org else "",
        role=auth.role_name,
        is_demo=is_demo,
    )
