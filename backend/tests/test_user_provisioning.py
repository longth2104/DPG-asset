"""find_user_by_name (app/services/user_provisioning.py) — resolving a
plain-text holder name against an already-fetched HRIS directory. Never
guesses on a collision; only links when the name is unambiguous."""

from app.services.user_provisioning import find_user_by_name


async def test_unique_name_match_links_existing_local_user(db_session, make_user):
    user = await make_user(role="cbnv", email="lmtuan@test.local")
    directory = [{"name": "Lương Minh Tuấn", "email": user.email, "emp_code": "E001"}]

    match = await find_user_by_name(db_session, "Lương Minh Tuấn", directory)
    assert match is not None
    assert match.id == user.id


async def test_match_is_case_and_whitespace_insensitive(db_session, make_user):
    user = await make_user(role="cbnv", email="lmtuan2@test.local")
    directory = [{"name": "Lương Minh Tuấn", "email": user.email}]

    match = await find_user_by_name(db_session, "  lương  minh tuấn ", directory)
    assert match is not None
    assert match.id == user.id


async def test_ambiguous_name_returns_none(db_session, make_user):
    await make_user(role="cbnv", email="a1@test.local")
    directory = [
        {"name": "Nguyễn Văn A", "email": "a1@test.local"},
        {"name": "Nguyễn Văn A", "email": "a2@test.local"},
    ]

    match = await find_user_by_name(db_session, "Nguyễn Văn A", directory)
    assert match is None


async def test_no_match_returns_none(db_session):
    directory = [{"name": "Someone Else", "email": "x@test.local"}]
    match = await find_user_by_name(db_session, "Not In Directory", directory)
    assert match is None


async def test_empty_name_returns_none(db_session):
    directory = [{"name": "Someone", "email": "x@test.local"}]
    assert await find_user_by_name(db_session, "", directory) is None
    assert await find_user_by_name(db_session, None, directory) is None
