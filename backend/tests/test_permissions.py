"""Company-scoped visibility (app/api/deps.py::get_scope_company_path) — the
fail-closed rule everything else (asset/request queries) builds on."""

from app.api.deps import NO_COMPANY_SCOPE, get_scope_company_path


async def test_admin_is_unrestricted_even_without_a_company(db_session, make_user):
    admin = await make_user(role="admin")
    assert await get_scope_company_path(db=db_session, user=admin) is None


async def test_user_with_no_company_fails_closed(db_session, make_user):
    user = await make_user(role="cbnv", company=None)
    path = await get_scope_company_path(db=db_session, user=user)
    assert path == NO_COMPANY_SCOPE


async def test_company_with_global_access_is_unrestricted(db_session, make_user, make_company):
    hq = await make_company("HQ", grants_global_access=True)
    user = await make_user(role="phong_thiet_bi", company=hq)
    assert await get_scope_company_path(db=db_session, user=user) is None


async def test_regular_company_scope_is_its_own_path(db_session, make_user, make_company):
    branch = await make_company("BRANCH")
    user = await make_user(role="cbnv", company=branch)
    path = await get_scope_company_path(db=db_session, user=user)
    assert path == branch.path


async def test_child_company_path_extends_parent(make_company):
    parent = await make_company("PARENT")
    child = await make_company("CHILD", parent=parent)
    assert child.path.startswith(parent.path)
    assert child.path != parent.path
