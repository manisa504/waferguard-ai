"""Cognito access-token verification and deliberately isolated local/demo identities."""

import os
import secrets
import time
import uuid

import jwt


class Forbidden(Exception):
    pass


class Authorization:
    def __init__(self, secret=None, cognito=None):
        self.secret = secret or secrets.token_urlsafe(48)
        self.local = os.getenv("WAFERGUARD_LOCAL_AUTH") == "1"
        if self.local and os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
            raise RuntimeError("Local reviewer authentication is prohibited in Lambda")
        self.pool = os.getenv("COGNITO_USER_POOL_ID")
        self.client_id = os.getenv("COGNITO_CLIENT_ID")
        self.region = os.getenv("AWS_REGION", "us-east-2")
        self.cognito = cognito
        self.issuer = f"https://cognito-idp.{self.region}.amazonaws.com/{self.pool}"
        self.jwks = jwt.PyJWKClient(self.issuer + "/.well-known/jwks.json") if self.pool else None

    def issue(self, kind):
        if kind == "local" and not self.local:
            raise Forbidden("Local reviewer mode is disabled")
        identity = uuid.uuid4().hex
        claims = {
            "sub": kind + ":" + identity,
            "kind": kind,
            "scope": "local" if kind == "local" else "demo:" + identity,
            "iss": "waferguard-simulation",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        }
        return jwt.encode(claims, self.secret, algorithm="HS256")

    def authenticate(self, token):
        try:
            # Simulation tokens have their own issuer, algorithm, secret and isolated namespace.
            claims = jwt.decode(
                token,
                self.secret,
                algorithms=["HS256"],
                issuer="waferguard-simulation",
                options={"require": ["sub", "exp", "iat"]},
            )
            if claims.get("kind") == "local" and self.local and claims.get("scope") == "local":
                return claims
            if (
                claims.get("kind") == "demo"
                and claims.get("scope") == "demo:" + claims["sub"][5:]
                and claims["sub"].startswith("demo:")
            ):
                return claims
            raise Forbidden("Invalid simulated identity")
        except jwt.InvalidTokenError:
            if not self.jwks:
                raise Forbidden("Sign-in required") from None
        try:
            key = self.jwks.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                key.key,
                algorithms=["RS256"],
                issuer=self.issuer,
                options={"verify_aud": False, "require": ["sub", "exp", "iat"]},
            )
            if claims.get("token_use") != "access" or claims.get("client_id") != self.client_id:
                raise Forbidden("A matching access token is required")
            return {**claims, "scope": "production", "kind": "cognito"}
        except (jwt.InvalidTokenError, jwt.PyJWKClientError) as error:
            raise Forbidden("Invalid or expired access token") from error

    def revalidate(self, actor):
        if actor["exp"] <= time.time():
            raise Forbidden("Reviewer session expired")
        if actor["kind"] == "demo":
            if actor["scope"] != "demo:" + actor["sub"][5:]:
                raise Forbidden("Demo namespace mismatch")
            return
        if actor["kind"] == "local" and self.local and actor["scope"] == "local":
            return
        if actor["kind"] != "cognito" or "reviewer" not in actor.get("cognito:groups", []):
            raise Forbidden("Reviewer role required")
        if not self.cognito:
            raise Forbidden("Live reviewer revalidation unavailable")
        user = self.cognito.admin_get_user(UserPoolId=self.pool, Username=actor["sub"])
        groups = self.cognito.admin_list_groups_for_user(
            UserPoolId=self.pool, Username=actor["sub"]
        )
        if not user["Enabled"] or "reviewer" not in [row["GroupName"] for row in groups["Groups"]]:
            raise Forbidden("Reviewer permission was revoked")
