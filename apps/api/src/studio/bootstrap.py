"""Bootstrap CLI: python -m studio.bootstrap"""

from __future__ import annotations

from studio_api.db import get_session_factory, init_db
from studio_api.services.invites import bootstrap_org


def main() -> None:
    init_db()
    db = get_session_factory()()
    try:
        result = bootstrap_org(db)
        if result is None:
            print("Bootstrap skipped: STUDIO_ORG_NAME and BOOTSTRAP_OWNER_EMAIL required")
            return
        org, user = result
        db.commit()
        print(f"Bootstrap complete: org={org.name} owner={user.email}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
