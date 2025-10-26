"""Azure AD authentication and authorization for FastAPI."""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
import requests
from jose import jwt, JWTError
from fastapi import HTTPException, Security, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from functools import lru_cache

from src.config import config

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer(auto_error=False)


class AzureADAuth:
    """Azure AD authentication handler."""

    def __init__(self):
        """Initialize Azure AD authentication."""
        self.enabled = config.AZURE_AD_ENABLED

        if not self.enabled:
            logger.info("Azure AD authentication is DISABLED")
            return

        if not all([config.AZURE_AD_TENANT_ID, config.AZURE_AD_CLIENT_ID, config.AZURE_AD_AUDIENCE]):
            logger.warning(
                "Azure AD is enabled but configuration is incomplete. "
                "Please set AZURE_AD_TENANT_ID, AZURE_AD_CLIENT_ID, and AZURE_AD_AUDIENCE"
            )
            self.enabled = False
            return

        self.tenant_id = config.AZURE_AD_TENANT_ID
        self.client_id = config.AZURE_AD_CLIENT_ID
        self.audience = config.AZURE_AD_AUDIENCE
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.allowed_groups = (
            config.AZURE_AD_ALLOWED_GROUPS.split(",") if config.AZURE_AD_ALLOWED_GROUPS else None
        )

        # Cache for signing keys (refreshed periodically)
        self._signing_keys = None
        self._keys_last_fetched = None

        logger.info(f"Azure AD authentication ENABLED for tenant: {self.tenant_id}")

    @lru_cache(maxsize=1)
    def _get_openid_config(self) -> Dict[str, Any]:
        """Fetch OpenID Connect configuration from Azure AD."""
        url = f"{self.authority}/v2.0/.well-known/openid-configuration"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch OpenID configuration: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to fetch authentication configuration"
            )

    def _get_signing_keys(self) -> Dict[str, Any]:
        """Fetch public signing keys from Azure AD."""
        # Cache keys for 24 hours
        if self._signing_keys and self._keys_last_fetched:
            age = (datetime.now() - self._keys_last_fetched).total_seconds()
            if age < 86400:  # 24 hours
                return self._signing_keys

        try:
            openid_config = self._get_openid_config()
            jwks_uri = openid_config["jwks_uri"]

            response = requests.get(jwks_uri, timeout=10)
            response.raise_for_status()
            keys_data = response.json()

            # Convert to dict keyed by kid (key ID)
            keys = {}
            for key in keys_data.get("keys", []):
                kid = key.get("kid")
                if kid:
                    keys[kid] = key

            self._signing_keys = keys
            self._keys_last_fetched = datetime.now()
            logger.debug(f"Fetched {len(keys)} signing keys from Azure AD")

            return keys

        except Exception as e:
            logger.error(f"Failed to fetch signing keys: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to fetch authentication keys"
            )

    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode JWT token from Azure AD.

        Args:
            token: JWT access token

        Returns:
            Decoded token payload with user claims

        Raises:
            HTTPException: If token is invalid or expired
        """
        if not self.enabled:
            # If auth is disabled, return a mock user for development
            return {
                "oid": "dev-user-id",
                "preferred_username": "dev@localhost",
                "name": "Development User",
                "email": "dev@localhost",
                "roles": [],
                "groups": []
            }

        try:
            # Get header to find the key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            if not kid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token missing key ID (kid)"
                )

            # Get the signing key
            signing_keys = self._get_signing_keys()
            signing_key = signing_keys.get(kid)

            if not signing_key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token signature key"
                )

            # Verify and decode token
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=f"{self.authority}/v2.0",
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iat": True,
                    "verify_aud": True,
                    "verify_iss": True,
                }
            )

            # Extract user info
            user = {
                "oid": payload.get("oid"),  # Object ID (unique user identifier)
                "preferred_username": payload.get("preferred_username") or payload.get("upn"),
                "name": payload.get("name"),
                "email": payload.get("email") or payload.get("preferred_username"),
                "roles": payload.get("roles", []),
                "groups": payload.get("groups", []),
                "tid": payload.get("tid"),  # Tenant ID
                "sub": payload.get("sub"),  # Subject
            }

            # Enhanced audit logging for successful authentication
            logger.info(
                f"AUTH_SUCCESS: user={user.get('email', 'N/A')} "
                f"oid={user.get('oid', 'N/A')} "
                f"name={user.get('name', 'N/A')} "
                f"roles={','.join(user.get('roles', []))} "
                f"groups={len(user.get('groups', []))}"
            )
            return user

        except JWTError as e:
            # Enhanced audit logging for failed authentication
            logger.warning(f"AUTH_FAILED: reason=JWT_ERROR error={str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid authentication token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            logger.error(f"Token verification error: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def check_group_membership(self, user: Dict[str, Any]) -> bool:
        """
        Check if user belongs to allowed groups.

        Args:
            user: Decoded user token payload

        Returns:
            True if user is in allowed groups or no groups configured
        """
        if not self.allowed_groups:
            return True  # No group restrictions

        user_groups = user.get("groups", [])
        is_authorized = any(group in user_groups for group in self.allowed_groups)

        if not is_authorized:
            # Enhanced audit logging for authorization failure
            logger.warning(
                f"AUTHZ_FAILED: user={user.get('email', 'N/A')} "
                f"oid={user.get('oid', 'N/A')} "
                f"user_groups={len(user_groups)} "
                f"required_groups={','.join(self.allowed_groups)}"
            )

        return is_authorized


# Global instance
azure_ad_auth = AzureADAuth()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Dict[str, Any]:
    """
    FastAPI dependency to get the current authenticated user.

    Use as: user = Depends(get_current_user)

    Returns:
        User information from validated JWT token

    Raises:
        HTTPException: If authentication fails
    """
    if not azure_ad_auth.enabled:
        # Development mode - return mock user
        return {
            "oid": "dev-user-id",
            "preferred_username": "dev@localhost",
            "name": "Development User",
            "email": "dev@localhost",
            "roles": [],
            "groups": []
        }

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    user = azure_ad_auth.verify_token(token)

    # Check group membership
    if not azure_ad_auth.check_group_membership(user):
        logger.warning(f"User {user.get('email')} not in allowed groups")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not authorized for this application"
        )

    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Optional[Dict[str, Any]]:
    """
    FastAPI dependency for optional authentication.
    Returns user if authenticated, None otherwise.

    Use as: user = Depends(get_optional_user)
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


def require_role(allowed_roles: list[str]):
    """
    Decorator to require specific roles for an endpoint.

    Usage:
        @app.get("/admin")
        @require_role(["Admin", "Contributor"])
        async def admin_endpoint(user = Depends(get_current_user)):
            ...
    """
    def decorator(func):
        async def wrapper(*args, user: Dict[str, Any] = None, **kwargs):
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            user_roles = user.get("roles", [])
            if not any(role in user_roles for role in allowed_roles):
                logger.warning(
                    f"User {user.get('email')} tried to access {func.__name__} "
                    f"but lacks required roles: {allowed_roles}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Required roles: {', '.join(allowed_roles)}"
                )

            return await func(*args, user=user, **kwargs)

        return wrapper
    return decorator
