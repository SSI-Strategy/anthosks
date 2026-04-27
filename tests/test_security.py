import pytest
from fastapi import HTTPException

import os

os.environ.setdefault("AZURE_AD_ENABLED", "true")
os.environ.setdefault("AZURE_AD_TENANT_ID", "tenant")
os.environ.setdefault("AZURE_AD_CLIENT_ID", "client")
os.environ.setdefault("AZURE_AD_AUDIENCE", "api://client")

from src.api.security import contained_upload_path, user_owner_id, validate_upload_filename
import src.auth.azure_auth as azure_auth
from src.auth.azure_auth import AzureADAuth, is_admin_user


def test_upload_filename_rejects_path_traversal():
    with pytest.raises(HTTPException) as exc:
        validate_upload_filename("../report.pdf")

    assert exc.value.status_code == 400


def test_upload_path_is_generated_under_input_dir(tmp_path):
    destination = contained_upload_path(tmp_path, ".pdf")

    assert destination.parent == tmp_path.resolve()
    assert destination.suffix == ".pdf"
    assert destination.name != "report.pdf"


def test_user_owner_id_requires_stable_identifier():
    assert user_owner_id({"oid": "user-1"}) == "user-1"

    with pytest.raises(HTTPException) as exc:
        user_owner_id({})

    assert exc.value.status_code == 403


def test_azure_auth_fails_closed_when_enabled_but_incomplete(monkeypatch):
    monkeypatch.setattr(azure_auth.config, "AZURE_AD_ENABLED", True)
    monkeypatch.setattr(azure_auth.config, "AZURE_AD_TENANT_ID", None)
    monkeypatch.setattr(azure_auth.config, "AZURE_AD_CLIENT_ID", "client")
    monkeypatch.setattr(azure_auth.config, "AZURE_AD_AUDIENCE", "api://client")

    with pytest.raises(RuntimeError):
        AzureADAuth()


def test_dev_auth_requires_explicit_local_flag(monkeypatch):
    monkeypatch.setattr(azure_auth.config, "AZURE_AD_ENABLED", False)
    monkeypatch.setattr(azure_auth.config, "DEV_AUTH_ENABLED", True)
    monkeypatch.setattr(azure_auth.config, "ENVIRONMENT", "production")

    with pytest.raises(RuntimeError):
        AzureADAuth()


def test_admin_user_accepts_configured_roles(monkeypatch):
    monkeypatch.setattr(azure_auth.config, "ANTHOSKS_ADMIN_ROLES", "Admin")
    monkeypatch.setattr(azure_auth.config, "ANTHOSKS_ADMIN_GROUPS", None)

    assert is_admin_user({"roles": ["Admin"], "groups": []})
    assert not is_admin_user({"roles": ["Reader"], "groups": []})
