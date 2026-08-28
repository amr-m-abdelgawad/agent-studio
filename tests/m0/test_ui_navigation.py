from __future__ import annotations

import pytest

from tests.m0.helpers.skips import requires_role, requires_web, web_url

pytestmark = [pytest.mark.m0_isolation, requires_web]

TEST_IDS = {
    "login_email": "login-email",
    "login_password": "login-password",
    "login_submit": "login-submit",
    "login_error": "login-error",
    "invite_password": "invite-password",
    "invite_submit": "invite-submit",
    "invite_error": "invite-error",
    "nav_agents": "nav-agents",
    "nav_runs": "nav-runs",
    "nav_invite": "nav-invite",
    "empty_agents": "empty-agents",
    "logout": "logout",
    "workspace_switcher": "workspace-switcher",
}


@pytest.fixture(scope="session")
def browser_context_args():
    return {"base_url": web_url()}


def _login(page, email: str, password: str) -> None:
    page.goto("/login")
    page.get_by_test_id(TEST_IDS["login_email"]).fill(email)
    page.get_by_test_id(TEST_IDS["login_password"]).fill(password)
    page.get_by_test_id(TEST_IDS["login_submit"]).click()


@requires_role["owner"]
def test_owner_sees_primary_navigation(page, browser_context_args):
    from tests.m0.helpers.skips import role_credentials

    email, password = role_credentials("owner")  # type: ignore[misc]
    _login(page, email, password)
    page.get_by_test_id(TEST_IDS["nav_agents"]).wait_for()
    page.get_by_test_id(TEST_IDS["nav_runs"]).wait_for()
    page.get_by_test_id(TEST_IDS["nav_invite"]).wait_for()
    page.get_by_test_id(TEST_IDS["workspace_switcher"]).wait_for()


@requires_role["owner"]
def test_owner_can_logout(page):
    from tests.m0.helpers.skips import role_credentials

    email, password = role_credentials("owner")  # type: ignore[misc]
    _login(page, email, password)
    page.get_by_test_id(TEST_IDS["logout"]).click()
    page.get_by_test_id(TEST_IDS["login_submit"]).wait_for()


@pytest.mark.parametrize("role", ["editor", "viewer", "runner"])
def test_invite_nav_hidden_for_non_admin_roles(page, role: str):
    from tests.m0.helpers.skips import role_credentials

    creds = role_credentials(role)
    if not creds:
        pytest.skip(f"M0_{role.upper()}_EMAIL and M0_{role.upper()}_PASSWORD are required")
    email, password = creds
    _login(page, email, password)
    page.get_by_test_id(TEST_IDS["nav_agents"]).wait_for()
    assert page.get_by_test_id(TEST_IDS["nav_invite"]).count() == 0


@requires_role["owner"]
def test_empty_agents_state_visible(page):
    from tests.m0.helpers.skips import role_credentials

    email, password = role_credentials("owner")  # type: ignore[misc]
    _login(page, email, password)
    page.get_by_test_id(TEST_IDS["nav_agents"]).click()
    page.get_by_test_id(TEST_IDS["empty_agents"]).wait_for()
