import os

import pytest

os.environ.setdefault("AZURE_AD_ENABLED", "true")
os.environ.setdefault("AZURE_AD_TENANT_ID", "tenant")
os.environ.setdefault("AZURE_AD_CLIENT_ID", "client")
os.environ.setdefault("AZURE_AD_AUDIENCE", "api://client")
os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@db.invalid:5432/db")


def test_api_import_does_not_initialize_database():
    import src.api.main as api_main

    assert api_main.db is None


@pytest.mark.asyncio
async def test_health_check_does_not_require_database():
    import src.api.main as api_main

    assert await api_main.health() == {"status": "ok", "message": "Healthy"}
