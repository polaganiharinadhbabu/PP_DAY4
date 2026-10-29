from typing import Annotated
from fastapi import Depends, Header, HTTPException


def common_paging(skip: int = 0, limit: int = 20):
    return {
        "skip": max(skip, 0),
        "limit": min(max(limit, 1), 100)
    }


Paging = Annotated[dict, Depends(common_paging)]


DEMO_USERS = {
    "demo-viewer-token": {"id": 1, "role": "viewer"},
    "demo-admin-token": {"id": 2, "role": "admin"}
}


def get_current_user(
    authorization: Annotated[str | None, Header()] = None
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )

    token = authorization.removeprefix("Bearer ").strip()
    user = DEMO_USERS.get(token)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    return user


def require_admin(user=Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="Forbidden"
        )

    return user
