-- SSO Configuration Table DDL
-- This table stores SSO (Single Sign-On) configurations for third-party system integration

-- PostgreSQL DDL
CREATE TABLE IF NOT EXISTS sso_configs (
    id VARCHAR(36) PRIMARY KEY DEFAULT (uuid_generate_v4()),
    tenant_id VARCHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    provider VARCHAR(16) NOT NULL DEFAULT 'custom',
    status VARCHAR(16) NOT NULL DEFAULT 'active',
    secret_key VARCHAR(255) NOT NULL,
    token_expire_minutes INTEGER NOT NULL DEFAULT 60,
    default_role VARCHAR(32) NOT NULL DEFAULT 'editor',
    config TEXT,
    created_by VARCHAR(36) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(36),
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS sso_configs_tenant_id_idx ON sso_configs(tenant_id);
CREATE INDEX IF NOT EXISTS sso_configs_provider_idx ON sso_configs(provider);

-- Comments
COMMENT ON TABLE sso_configs IS 'SSO configuration for third-party system integration';
COMMENT ON COLUMN sso_configs.id IS 'Unique identifier';
COMMENT ON COLUMN sso_configs.tenant_id IS 'Tenant/workspace ID';
COMMENT ON COLUMN sso_configs.name IS 'SSO configuration name';
COMMENT ON COLUMN sso_configs.provider IS 'SSO provider type: custom, oidc, saml';
COMMENT ON COLUMN sso_configs.status IS 'Configuration status: active, disabled';
COMMENT ON COLUMN sso_configs.secret_key IS 'Secret key for JWT token signing';
COMMENT ON COLUMN sso_configs.token_expire_minutes IS 'Token expiration time in minutes';
COMMENT ON COLUMN sso_configs.default_role IS 'Default role for new users: owner, admin, editor, normal, dataset_operator';
COMMENT ON COLUMN sso_configs.config IS 'Additional configuration in JSON format';
COMMENT ON COLUMN sso_configs.created_by IS 'User ID who created this configuration';
COMMENT ON COLUMN sso_configs.updated_by IS 'User ID who last updated this configuration';
