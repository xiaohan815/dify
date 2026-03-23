import logging

from flask import redirect, request
from flask_restx import Resource
from pydantic import BaseModel, Field

from configs import dify_config
from controllers.common.schema import register_schema_models
from controllers.console import console_ns
from libs.helper import extract_remote_ip
from models.sso import SsoConfigStatus
from services.errors.account import AccountRegisterError
from services.sso_service import SsoService

logger = logging.getLogger(__name__)


class SsoLoginPayload(BaseModel):
    sso_config_id: str = Field(..., description="SSO configuration ID")
    token: str = Field(..., description="SSO token from third-party system")


class SsoTokenPayload(BaseModel):
    sso_config_id: str = Field(..., description="SSO configuration ID")
    user_identifier: str = Field(..., description="Unique user identifier from third-party system")
    email: str = Field(..., description="User email address")
    name: str | None = Field(None, description="User display name")
    additional_data: dict | None = Field(None, description="Additional user data")


class SsoConfigCreatePayload(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="SSO configuration name")
    secret_key: str = Field(..., min_length=32, max_length=255, description="Secret key for token signing")
    provider: str = Field(default="custom", description="SSO provider type")
    token_expire_minutes: int = Field(default=60, ge=1, le=1440, description="Token expiration in minutes")
    default_role: str = Field(default="editor", description="Default role for new users")


register_schema_models(console_ns, SsoLoginPayload, SsoTokenPayload, SsoConfigCreatePayload)


@console_ns.route("/sso/login")
class SsoLoginApi(Resource):
    @console_ns.doc("sso_login")
    @console_ns.doc(description="Login via SSO token")
    @console_ns.expect(console_ns.models[SsoLoginPayload.__name__])
    @console_ns.response(200, "Login successful")
    @console_ns.response(401, "Invalid SSO token")
    def post(self):
        payload = SsoLoginPayload.model_validate(console_ns.payload or {})

        sso_config = SsoService.get_sso_config(payload.sso_config_id)
        if not sso_config:
            return {"error": "SSO configuration not found"}, 404

        if sso_config.status != SsoConfigStatus.ACTIVE:
            return {"error": "SSO configuration is disabled"}, 403

        try:
            account, is_new_user, token_pair = SsoService.authenticate_with_sso(
                sso_config=sso_config,
                token=payload.token,
                ip_address=extract_remote_ip(request),
            )
        except ValueError as e:
            logger.warning("SSO authentication failed: %s", str(e))
            return {"error": str(e)}, 401
        except AccountRegisterError as e:
            logger.warning("SSO registration failed: %s", e.description)
            return {"error": e.description}, 403

        return {
            "access_token": token_pair.access_token,
            "refresh_token": token_pair.refresh_token,
            "csrf_token": token_pair.csrf_token,
            "is_new_user": is_new_user,
            "account": {
                "id": account.id,
                "name": account.name,
                "email": account.email,
            },
        }


@console_ns.route("/sso/callback")
class SsoCallbackApi(Resource):
    @console_ns.doc("sso_callback")
    @console_ns.doc(description="SSO callback endpoint for browser redirect")
    @console_ns.response(302, "Redirect to console")
    def get(self):
        sso_config_id = request.args.get("sso_config_id")
        token = request.args.get("token")
        redirect_url = request.args.get("redirect", "/")

        if not sso_config_id or not token:
            return {"error": "Missing sso_config_id or token"}, 400

        sso_config = SsoService.get_sso_config(sso_config_id)
        if not sso_config:
            return {"error": "SSO configuration not found"}, 404

        if sso_config.status != SsoConfigStatus.ACTIVE:
            return {"error": "SSO configuration is disabled"}, 403

        try:
            account, is_new_user, token_pair = SsoService.authenticate_with_sso(
                sso_config=sso_config,
                token=token,
                ip_address=extract_remote_ip(request),
            )
        except ValueError as e:
            logger.warning("SSO authentication failed: %s", str(e))
            return {"error": str(e)}, 401
        except AccountRegisterError as e:
            logger.warning("SSO registration failed: %s", e.description)
            return {"error": e.description}, 403

        from flask import make_response

        response = make_response(redirect(redirect_url))
        response.set_cookie(
            "access_token",
            token_pair.access_token,
            max_age=60 * 60 * 24 * 7,
            httponly=True,
            secure=False,
            samesite="Lax",
            path="/",
        )
        response.set_cookie(
            "refresh_token",
            token_pair.refresh_token,
            max_age=60 * 60 * 24 * 30,
            httponly=True,
            secure=False,
            samesite="Lax",
            path="/",
        )

        return response


@console_ns.route("/sso/iframe")
class SsoIframeApi(Resource):
    @console_ns.doc("sso_iframe")
    @console_ns.doc(description="SSO iframe endpoint for embedded scenarios")
    @console_ns.response(200, "HTML page for iframe")
    def get(self):
        sso_config_id = request.args.get("sso_config_id")
        token = request.args.get("token")
        redirect_url = request.args.get("redirect", "/apps")

        if not sso_config_id or not token:
            return {"error": "Missing sso_config_id or token"}, 400

        sso_config = SsoService.get_sso_config(sso_config_id)
        if not sso_config:
            return {"error": "SSO configuration not found"}, 404

        if sso_config.status != SsoConfigStatus.ACTIVE:
            return {"error": "SSO configuration is disabled"}, 403

        try:
            account, is_new_user, token_pair = SsoService.authenticate_with_sso(
                sso_config=sso_config,
                token=token,
                ip_address=extract_remote_ip(request),
            )
        except ValueError as e:
            logger.warning("SSO authentication failed: %s", str(e))
            return {"error": str(e)}, 401
        except AccountRegisterError as e:
            logger.warning("SSO registration failed: %s", e.description)
            return {"error": e.description}, 403

        from flask import make_response

        html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>SSO Login</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f5f5f5; }}
        .loading {{ text-align: center; }}
        .spinner {{ width: 40px; height: 40px; border: 3px solid #e0e0e0; border-top-color: #528bff; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 16px; }}
        @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    </style>
</head>
<body>
    <div class="loading">
        <div class="spinner"></div>
        <p>Logging in...</p>
    </div>
    <script>
        (function() {{
            var tokens = {{
                access_token: '{token_pair.access_token}',
                refresh_token: '{token_pair.refresh_token}',
                csrf_token: '{token_pair.csrf_token}'
            }};
            var redirectUrl = '{redirect_url}';
            
            // Set cookies (works because we're on the same domain)
            document.cookie = 'access_token=' + tokens.access_token + '; path=/; max-age=' + (60 * 60 * 24 * 7);
            document.cookie = 'refresh_token=' + tokens.refresh_token + '; path=/; max-age=' + (60 * 60 * 24 * 30);
            
            // Notify parent window via postMessage
            if (window.parent !== window) {{
                window.parent.postMessage({{
                    type: 'dify-sso-login',
                    success: true,
                    tokens: tokens,
                    redirect: redirectUrl
                }}, '*');
            }}
            
            // Redirect to target page
            setTimeout(function() {{
                window.location.href = redirectUrl;
            }}, 100);
        }})();
    </script>
</body>
</html>'''

        response = make_response(html_content)
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        return response


@console_ns.route("/sso/token")
class SsoTokenApi(Resource):
    @console_ns.doc("sso_generate_token")
    @console_ns.doc(description="Generate SSO token for testing (admin only)")
    @console_ns.expect(console_ns.models[SsoTokenPayload.__name__])
    @console_ns.response(200, "Token generated successfully")
    @console_ns.response(404, "SSO configuration not found")
    def post(self):
        payload = SsoTokenPayload.model_validate(console_ns.payload or {})

        sso_config = SsoService.get_sso_config(payload.sso_config_id)
        if not sso_config:
            return {"error": "SSO configuration not found"}, 404

        token = SsoService.generate_sso_token(
            sso_config=sso_config,
            user_identifier=payload.user_identifier,
            email=payload.email,
            name=payload.name,
            additional_data=payload.additional_data,
        )

        return {"token": token}


@console_ns.route("/sso/configs")
class SsoConfigListApi(Resource):
    @console_ns.doc("list_sso_configs")
    @console_ns.doc(description="List SSO configurations for current tenant")
    @console_ns.response(200, "SSO configurations retrieved successfully")
    def get(self):
        from libs.login import current_account_with_tenant

        current_user, current_tenant_id = current_account_with_tenant()

        if not current_user.is_admin_or_owner:
            return {"error": "Permission denied"}, 403

        configs = SsoService.get_sso_configs_by_tenant(current_tenant_id)

        return {
            "data": [
                {
                    "id": config.id,
                    "name": config.name,
                    "provider": config.provider,
                    "status": config.status,
                    "token_expire_minutes": config.token_expire_minutes,
                    "default_role": config.default_role,
                    "created_at": config.created_at.isoformat() if config.created_at else None,
                }
                for config in configs
            ]
        }

    @console_ns.doc("create_sso_config")
    @console_ns.doc(description="Create SSO configuration")
    @console_ns.expect(console_ns.models[SsoConfigCreatePayload.__name__])
    @console_ns.response(201, "SSO configuration created successfully")
    def post(self):
        from libs.login import current_account_with_tenant

        current_user, current_tenant_id = current_account_with_tenant()

        if not current_user.is_admin_or_owner:
            return {"error": "Permission denied"}, 403

        payload = SsoConfigCreatePayload.model_validate(console_ns.payload or {})

        from models.sso import SsoProvider

        try:
            config = SsoService.create_sso_config(
                tenant_id=current_tenant_id,
                name=payload.name,
                secret_key=payload.secret_key,
                created_by=current_user.id,
                provider=SsoProvider(payload.provider) if payload.provider else SsoProvider.CUSTOM,
                token_expire_minutes=payload.token_expire_minutes,
                default_role=payload.default_role,
            )
        except Exception as e:
            logger.exception("Failed to create SSO config")
            return {"error": str(e)}, 400

        return {"id": config.id, "name": config.name}, 201


@console_ns.route("/sso/configs/<uuid:sso_config_id>")
class SsoConfigApi(Resource):
    @console_ns.doc("get_sso_config")
    @console_ns.doc(description="Get SSO configuration details")
    @console_ns.response(200, "SSO configuration retrieved successfully")
    @console_ns.response(404, "SSO configuration not found")
    def get(self, sso_config_id):
        from libs.login import current_account_with_tenant

        current_user, current_tenant_id = current_account_with_tenant()

        if not current_user.is_admin_or_owner:
            return {"error": "Permission denied"}, 403

        config = SsoService.get_sso_config(str(sso_config_id))
        if not config or config.tenant_id != current_tenant_id:
            return {"error": "SSO configuration not found"}, 404

        return {
            "id": config.id,
            "name": config.name,
            "provider": config.provider,
            "status": config.status,
            "token_expire_minutes": config.token_expire_minutes,
            "default_role": config.default_role,
            "created_at": config.created_at.isoformat() if config.created_at else None,
            "updated_at": config.updated_at.isoformat() if config.updated_at else None,
        }

    @console_ns.doc("delete_sso_config")
    @console_ns.doc(description="Delete SSO configuration")
    @console_ns.response(204, "SSO configuration deleted successfully")
    @console_ns.response(404, "SSO configuration not found")
    def delete(self, sso_config_id):
        from libs.login import current_account_with_tenant

        current_user, current_tenant_id = current_account_with_tenant()

        if not current_user.is_admin_or_owner:
            return {"error": "Permission denied"}, 403

        try:
            SsoService.delete_sso_config(str(sso_config_id), current_tenant_id)
        except ValueError as e:
            return {"error": str(e)}, 404

        return "", 204
