# Dify SSO 集成指南

本文档介绍如何配置和使用Dify的SSO（单点登录）功能，允许第三方系统实现用户自动登录。

## 环境配置

在 `docker/.env` 中添加以下配置：

```bash
# SSO (Single Sign-On) Configuration
SSO_ENABLED=true
SSO_ALLOW_REGISTER=true
SSO_DEFAULT_ROLE=editor
SSO_DEFAULT_LANGUAGE=zh-Hans
SSO_DEFAULT_TIMEZONE=Asia/Shanghai
```

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `SSO_ENABLED` | 是否启用SSO功能 | `false` |
| `SSO_ALLOW_REGISTER` | 是否允许通过SSO自动创建新用户 | `true` |
| `SSO_DEFAULT_ROLE` | 新用户的默认角色 | `editor` |
| `SSO_DEFAULT_LANGUAGE` | 新用户的默认语言 | `zh-Hans` |
| `SSO_DEFAULT_TIMEZONE` | 新用户的默认时区 | `Asia/Shanghai` |

### iframe嵌套配置（跨子域名）
我测试过了,只要域名一致就行,不用子域名一样也可以登录,底下这2个参数(COOKIE_DOMAIN,NEXT_PUBLIC_COOKIE_DOMAIN)可以不用配置
如果需要在iframe中嵌套Dify，且父页面和Dify在不同子域名（如 `z4s.example.com` 和 `dify.example.com`），需要配置Cookie域名：

```bash
# Cookie域名配置（跨子域名共享Cookie）
COOKIE_DOMAIN=.example.com
NEXT_PUBLIC_COOKIE_DOMAIN=1
```

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `COOKIE_DOMAIN` | Cookie域名，允许子域名共享 | `.example.com` |
| `NEXT_PUBLIC_COOKIE_DOMAIN` | 前端Cookie域名配置 | `1` |

**注意：** 
- `COOKIE_DOMAIN` 需要设置为父域名，如 `.example.com`
- 前面的点号 `.` 是可选的，现代浏览器会自动处理
- 配置后需要重启容器生效

## API端点

### 认证说明

部分API需要管理员权限，请在请求头中添加Dify管理员的access token：

```http
Authorization: Bearer {your_dify_access_token}
```

**获取access token的方式：**

Dify登录后，token存储在浏览器Cookie中。获取方式：

1. **从浏览器Cookie获取**（推荐）：
   - 登录Dify控制台
   - 打开浏览器开发者工具（F12）
   - 切换到 "Application" 或 "存储" 标签
   - 找到 Cookies → 选择Dify域名
   - 复制 `access_token` 的值

2. **从浏览器控制台获取**：
   ```javascript
   // 在浏览器控制台执行
   document.cookie.split('; ').find(c => c.startsWith('access_token=')).split('=')[1]
   ```

**注意**：
- `localStorage` 中的 `console_token` 可能会过期
- 推荐使用Cookie中的 `access_token`

---

## 1. 创建SSO配置

管理员创建SSO配置，设置用于签名JWT token的密钥。

**请求：**

```http
POST /console/api/sso/configs
Content-Type: application/json
Authorization: Bearer {admin_access_token}

{
  "name": "My SSO Provider",
  "secret_key": "your-256-bit-secret-key-at-least-32-characters-long",
  "provider": "custom",
  "token_expire_minutes": 60,
  "default_role": "editor"
}
```

**参数说明：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 | SSO配置名称 |
| `secret_key` | string | 是 | JWT签名密钥，至少32个字符 |
| `provider` | string | 否 | SSO提供商类型，默认 `custom` |
| `token_expire_minutes` | int | 否 | Token过期时间（分钟），默认60 |
| `default_role` | string | 否 | 新用户默认角色，默认 `editor` |

**响应：**

```json
{
  "id": "52b0e35b-bea3-4c6c-bcad-f5e31426f02b",
  "name": "My SSO Provider"
}
```

---

## 2. 生成SSO Token

第三方系统使用配置的 `secret_key` 生成JWT token。

### 2.1 使用API生成（测试用）

**请求：**

```http
POST /console/api/sso/token
Content-Type: application/json

{
  "sso_config_id": "52b0e35b-bea3-4c6c-bcad-f5e31426f02b",
  "user_identifier": "user-123",
  "email": "user@example.com",
  "name": "User Name"
}
```

**响应：**

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 2.2 第三方系统生成（生产环境）

第三方系统应使用 `secret_key` 在服务端生成JWT token：

**Python示例：**

```python
import jwt
from datetime import datetime, timedelta, UTC

def generate_sso_token(secret_key: str, sso_config_id: str, user_email: str, 
                       user_identifier: str, user_name: str = None,
                       expire_minutes: int = 60) -> str:
    """
    生成SSO JWT Token
    
    Args:
        secret_key: SSO配置的密钥
        sso_config_id: SSO配置ID
        user_email: 用户邮箱
        user_identifier: 第三方系统的用户唯一标识
        user_name: 用户显示名称
        expire_minutes: Token过期时间（分钟）
    
    Returns:
        JWT token字符串
    """
    payload = {
        "iss": f"dify_sso:{sso_config_id}",
        "sub": user_identifier,
        "email": user_email,
        "name": user_name or user_email.split("@")[0],
        "exp": datetime.now(UTC) + timedelta(minutes=expire_minutes),
        "iat": datetime.now(UTC),
        "type": "sso_auth",
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")

# 使用示例
token = generate_sso_token(
    secret_key="your-256-bit-secret-key-at-least-32-characters-long",
    sso_config_id="52b0e35b-bea3-4c6c-bcad-f5e31426f02b",
    user_email="user@example.com",
    user_identifier="user-123",
    user_name="John Doe"
)
```

**Node.js示例：**

```javascript
const jwt = require('jsonwebtoken');

function generateSsoToken(secretKey, ssoConfigId, userEmail, userIdentifier, userName = null, expireMinutes = 60) {
    const payload = {
        iss: `dify_sso:${ssoConfigId}`,
        sub: userIdentifier,
        email: userEmail,
        name: userName || userEmail.split('@')[0],
        exp: Math.floor(Date.now() / 1000) + expireMinutes * 60,
        iat: Math.floor(Date.now() / 1000),
        type: 'sso_auth',
    };
    return jwt.sign(payload, secretKey, { algorithm: 'HS256' });
}

// 使用示例
const token = generateSsoToken(
    'your-256-bit-secret-key-at-least-32-characters-long',
    '52b0e35b-bea3-4c6c-bcad-f5e31426f02b',
    'user@example.com',
    'user-123',
    'John Doe'
);
```

**Java示例：**

```java
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;
import javax.crypto.SecretKey;

public class SsoTokenGenerator {
    
    public static String generateSsoToken(String secretKey, String ssoConfigId, 
                                          String userEmail, String userIdentifier,
                                          String userName, int expireMinutes) {
        SecretKey key = Keys.hmacShaKeyFor(secretKey.getBytes(StandardCharsets.UTF_8));
        
        long now = System.currentTimeMillis();
        Map<String, Object> claims = new HashMap<>();
        claims.put("iss", "dify_sso:" + ssoConfigId);
        claims.put("sub", userIdentifier);
        claims.put("email", userEmail);
        claims.put("name", userName != null ? userName : userEmail.split("@")[0]);
        claims.put("type", "sso_auth");
        
        return Jwts.builder()
                .claims(claims)
                .issuedAt(new Date(now))
                .expiration(new Date(now + expireMinutes * 60 * 1000L))
                .signWith(key)
                .compact();
    }
}
```

---

## 3. SSO登录

使用生成的token进行登录。

**请求：**

```http
POST /console/api/sso/login
Content-Type: application/json

{
  "sso_config_id": "52b0e35b-bea3-4c6c-bcad-f5e31426f02b",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**响应：**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "836e2c6ab4d657455a3cb9faa347c5a3...",
  "csrf_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "is_new_user": true,
  "account": {
    "id": "9472f97b-2d3e-4d66-bed4-2b547e8a1dea",
    "name": "John Doe",
    "email": "user@example.com"
  }
}
```

**响应字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `access_token` | string | Dify访问令牌，用于后续API调用 |
| `refresh_token` | string | 刷新令牌 |
| `csrf_token` | string | CSRF防护令牌 |
| `is_new_user` | boolean | 是否是新创建的用户 |
| `account` | object | 用户信息 |

---

## 4. 管理SSO配置

### 4.1 获取SSO配置列表

```http
GET /console/api/sso/configs
Authorization: Bearer {admin_access_token}
```

**响应：**

```json
{
  "data": [
    {
      "id": "52b0e35b-bea3-4c6c-bcad-f5e31426f02b",
      "name": "My SSO Provider",
      "provider": "custom",
      "status": "active",
      "token_expire_minutes": 60,
      "default_role": "editor",
      "created_at": "2026-03-16T12:00:00"
    }
  ]
}
```

### 4.2 获取单个SSO配置

```http
GET /console/api/sso/configs/{sso_config_id}
Authorization: Bearer {admin_access_token}
```

### 4.3 删除SSO配置

```http
DELETE /console/api/sso/configs/{sso_config_id}
Authorization: Bearer {admin_access_token}
```

---

## 5. 完整集成流程

### 场景：第三方系统嵌入Dify

1. **用户在第三方系统登录**
2. **第三方系统生成SSO Token**
   - 使用预先配置的 `secret_key`
   - 包含用户邮箱和唯一标识
3. **重定向到Dify SSO回调端点**
   - Dify验证Token并设置Cookie
   - 自动跳转到目标页面
4. **用户已登录Dify，可直接使用**

### SSO回调端点（推荐）

使用GET请求的回调端点，Dify会自动设置Cookie并重定向：

```
GET /console/api/sso/callback?sso_config_id={config_id}&token={sso_token}&redirect={target_url}
```

**参数说明：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `sso_config_id` | string | 是 | SSO配置ID |
| `token` | string | 是 | SSO JWT Token |
| `redirect` | string | 否 | 登录后跳转的目标页面，默认 `/` |

**示例：跳转到应用列表页面**

```
http://192.168.31.214:9001/console/api/sso/callback?sso_config_id=52b0e35b-bea3-4c6c-bcad-f5e31426f02b&token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...&redirect=/apps
```

### 前端集成示例

**方式1：直接重定向（推荐）**

```javascript
// 第三方系统后端生成token后，前端直接跳转
function redirectToDify(ssoToken) {
    const ssoConfigId = '52b0e35b-bea3-4c6c-bcad-f5e31426f02b';
    const targetUrl = '/apps';
    
    const callbackUrl = `http://192.168.31.214:9001/console/api/sso/callback?` +
        `sso_config_id=${ssoConfigId}&` +
        `token=${encodeURIComponent(ssoToken)}&` +
        `redirect=${encodeURIComponent(targetUrl)}`;
    
    window.location.href = callbackUrl;
}
```

**方式2：后端重定向**

```python
# Python Flask 示例
from flask import redirect
import urllib.parse

def sso_login_redirect(sso_token: str):
    sso_config_id = "52b0e35b-bea3-4c6c-bcad-f5e31426f02b"
    target_url = "/apps"
    
    callback_url = f"http://192.168.31.214:9001/console/api/sso/callback?" + \
        f"sso_config_id={sso_config_id}&" + \
        f"token={urllib.parse.quote(sso_token)}&" + \
        f"redirect={urllib.parse.quote(target_url)}"
    
    return redirect(callback_url)
```

**方式3：AJAX登录（同域场景）**

```javascript
// 仅适用于同域场景，跨域无法设置Cookie
async function ssoLogin(ssoConfigId, ssoToken) {
  const response = await fetch('http://192.168.31.214:9001/console/api/sso/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      sso_config_id: ssoConfigId,
      token: ssoToken
    }),
    credentials: 'include'
  });
  
  const data = await response.json();
  if (data.access_token) {
    // 登录成功，跳转到应用列表
    window.location.href = '/apps';
  }
}
```

**方式4：iframe嵌套（跨域场景）**

使用专门的 `/sso/iframe` 端点，在Dify域名下设置Cookie后自动跳转：

```html
<!-- 父页面 (http://localhost:8081) -->
<iframe 
  id="dify-iframe" 
  src="http://192.168.31.214:9001/console/api/sso/iframe?sso_config_id=52b0e35b-bea3-4c6c-bcad-f5e31426f02b&token=YOUR_SSO_TOKEN&redirect=/apps"
  style="width: 100%; height: 100vh; border: none;">
</iframe>

<script>
// 监听iframe发来的消息（可选）
window.addEventListener('message', function(event) {
    // 安全检查：验证消息来源
    if (event.origin !== 'http://192.168.31.214:9001') return;
    
    if (event.data.type === 'dify-sso-login' && event.data.success) {
        console.log('SSO登录成功');
        // iframe会自动跳转到Dify页面
    }
});
</script>
```

**工作原理：**

1. iframe加载 `/sso/iframe` 页面（在Dify域名下）
2. 页面设置Cookie（同域，浏览器允许）
3. 页面自动跳转到Dify目标页面
4. Dify页面读取Cookie，用户已登录

**注意：** iframe方式下，用户在Dify中的操作都在iframe内完成，父页面无法直接访问Dify的数据。

---

## 6. 安全注意事项

1. **密钥安全**
   - `secret_key` 必须妥善保管，不要泄露
   - 建议使用至少256位（32字符）的随机密钥
   - 定期更换密钥

2. **Token安全**
   - Token有过期时间，默认60分钟
   - Token只使用一次后建议销毁
   - 使用HTTPS传输

3. **用户验证**
   - 确保token中的用户信息准确
   - 邮箱用于唯一标识用户
   - `user_identifier` 用于关联第三方系统用户

4. **权限控制**
   - 新用户默认角色为 `editor`
   - 可通过 `default_role` 参数配置
   - 管理员可在Dify中调整用户角色

---

## 7. 错误处理

| 错误信息 | 原因 | 解决方案 |
|----------|------|----------|
| `SSO configuration not found` | SSO配置不存在 | 检查 `sso_config_id` 是否正确 |
| `SSO configuration is disabled` | SSO配置已禁用 | 启用SSO配置 |
| `Token has expired` | Token已过期 | 重新生成Token |
| `Invalid token` | Token无效 | 检查密钥是否正确 |
| `SSO registration is not allowed` | 禁止SSO注册 | 设置 `SSO_ALLOW_REGISTER=true` |
| `Account is banned` | 账户已被禁用 | 联系管理员解封账户 |

---

## 8. 数据库迁移

首次部署需要执行数据库迁移创建 `sso_configs` 表：

```bash
# 进入API容器
docker exec -it docker-api-1 bash

# 执行迁移
flask db upgrade
```

或使用DDL直接创建：

```sql
CREATE TABLE sso_configs (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    provider VARCHAR(16) DEFAULT 'custom',
    secret_key VARCHAR(255) NOT NULL,
    token_expire_minutes INTEGER DEFAULT 60,
    default_role VARCHAR(32) DEFAULT 'editor',
    config TEXT,
    status VARCHAR(16) DEFAULT 'active',
    created_by VARCHAR(36) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sso_configs_tenant_id ON sso_configs(tenant_id);
CREATE INDEX idx_sso_configs_status ON sso_configs(status);
```

---

## 9. SSO 用户邮箱变更修复记录

### 问题描述

当用户在 IdP 侧修改邮箱后再次通过 SSO 登录时，系统会报 `UniqueViolation` 错误，导致登录失败。

**根本原因：** 原代码仅按邮箱查找账号，邮箱变更后找不到旧账号，会尝试注册新账号并建立 SSO 绑定，但 `account_integrates` 表的 `(provider, open_id)` 唯一约束导致插入冲突——因为旧账号已经绑定了同一个 SSO 身份。

**复现场景：**

1. 用户 `lps_test2`（邮箱 `lps_test2@qq.com`）首次 SSO 登录 → 创建账号 + SSO 绑定 `(sso_custom, lps_test2) → account_A`
2. 用户在 IdP 修改邮箱为 `lps_test2ok@qq.com`，再次 SSO 登录
3. 系统按新邮箱查找 → 找不到 → 注册新账号 `account_B` → 调用 `link_account_integrate(sso_custom, lps_test2, account_B)` → **UniqueViolation 崩溃**

### 修复方案

修改 SSO 登录的账号查找逻辑，改为三级查找：

```
1. 先通过 (provider, open_id) 查 account_integrates 表 → 找到 SSO 绑定 → 用旧账号，更新邮箱
2. 再通过 email 查 accounts 表 → 找到已有账号 → 建立 SSO 绑定
3. 都找不到 → 注册新账号
```

### 修改的文件

#### 文件 1：`api/services/sso_service.py`

**`authenticate_with_sso` 方法** — 重写账号查找逻辑：

- 新增 import：`AccountIntegrate`
- 第一步：通过 `(provider, open_id)` 查 `account_integrates` 表，找到已有 SSO 绑定对应的账号
- 第二步：通过 `email` 查 `accounts` 表
- 第三步：注册新账号（原有逻辑不变）
- `else` 分支（已有用户）新增：
  - 更新邮箱（`account.email = email`）
  - 调用 `link_account_integrate` 建立 SSO 绑定

#### 文件 2：`api/services/account_service.py`

**`link_account_integrate` 方法** — 添加 `(provider, open_id)` 冲突保护：

- 在插入前先检查 `(provider, open_id)` 是否已绑定到其他账号
- 如果是，先删除旧绑定再插入新绑定
- 防御性保护，避免 `UniqueViolation` 异常

### 修复后各场景行为

| 场景 | 修复前 | 修复后 |
|------|--------|--------|
| 新用户首次 SSO 登录 | 正常注册+绑定 | 不变 |
| 已有用户（邮箱匹配）SSO 登录 | 只更新 name，不建立绑定 | 更新 name + email + 建立绑定 |
| 用户改邮箱后 SSO 登录 | 注册新账号 → UniqueViolation 崩溃 | 找到旧账号 → 更新邮箱 → 成功，数据完整保留 |

---

## 10. 账户数据清理 SQL

当需要删除某个 SSO 账户及其所有关联数据时，按以下顺序执行 SQL。

### 10.1 查找账户及关联信息

```sql
-- 根据邮箱查找账户
SELECT id, name, email, status FROM accounts WHERE email = 'target@example.com';

-- 查看账户关联的 tenant（删除前确认 tenant 下是否还有其他用户）
SELECT t.id, t.name, taj.account_id, a.email, taj.role
FROM tenants t
JOIN tenant_account_joins taj ON t.id = taj.tenant_id
JOIN accounts a ON a.id = taj.account_id
WHERE taj.account_id = '目标账户ID';

-- 查看 tenant 下所有用户（确认是否可安全删除 tenant）
SELECT taj.account_id, a.email, taj.role
FROM tenant_account_joins taj
JOIN accounts a ON a.id = taj.account_id
WHERE taj.tenant_id = '目标tenantID';
```

### 10.2 删除账户及关联数据

将 `'ACCOUNT_ID'` 替换为实际的账户 ID，支持同时删除多个账户。

```sql
BEGIN;

-- 1. SSO 绑定
DELETE FROM account_integrates WHERE account_id IN ('ACCOUNT_ID');

-- 2. tenant 关联
DELETE FROM tenant_account_joins WHERE account_id IN ('ACCOUNT_ID');

-- 3. tenant（仅当 tenant 下只有该用户时才删除，否则跳过）
DELETE FROM tenants WHERE id IN (
    SELECT t.id FROM tenants t
    JOIN tenant_account_joins taj ON t.id = taj.tenant_id
    WHERE taj.account_id IN ('ACCOUNT_ID')
    GROUP BY t.id
    HAVING COUNT(*) = 1
);

-- 4. 直接关联 account_id 的表
DELETE FROM invitation_codes WHERE used_by_account_id IN ('ACCOUNT_ID');
DELETE FROM account_trial_app_records WHERE account_id IN ('ACCOUNT_ID');
DELETE FROM provider_orders WHERE account_id IN ('ACCOUNT_ID');
DELETE FROM dataset_permissions WHERE account_id IN ('ACCOUNT_ID');
DELETE FROM message_annotations WHERE account_id IN ('ACCOUNT_ID');
DELETE FROM app_annotation_hit_histories WHERE account_id IN ('ACCOUNT_ID');
DELETE FROM operation_logs WHERE account_id IN ('ACCOUNT_ID');

-- 5. from_account_id 关联的表
DELETE FROM conversations WHERE from_account_id IN ('ACCOUNT_ID');
DELETE FROM messages WHERE from_account_id IN ('ACCOUNT_ID');
DELETE FROM message_feedbacks WHERE from_account_id IN ('ACCOUNT_ID');

-- 6. created_by 直接关联 Account 的表（无 created_by_role 字段）
DELETE FROM apps WHERE created_by IN ('ACCOUNT_ID') OR updated_by IN ('ACCOUNT_ID');
DELETE FROM app_model_configs WHERE created_by IN ('ACCOUNT_ID') OR updated_by IN ('ACCOUNT_ID');
DELETE FROM app_annotation_settings WHERE created_user_id IN ('ACCOUNT_ID') OR updated_user_id IN ('ACCOUNT_ID');
DELETE FROM sites WHERE created_by IN ('ACCOUNT_ID') OR updated_by IN ('ACCOUNT_ID');
DELETE FROM sso_configs WHERE created_by IN ('ACCOUNT_ID') OR updated_by IN ('ACCOUNT_ID');
DELETE FROM workflows WHERE created_by IN ('ACCOUNT_ID') OR updated_by IN ('ACCOUNT_ID');
DELETE FROM tags WHERE created_by IN ('ACCOUNT_ID');
DELETE FROM tag_bindings WHERE created_by IN ('ACCOUNT_ID');
DELETE FROM workflow_webhook_triggers WHERE created_by IN ('ACCOUNT_ID');

-- 7. created_by 需结合 created_by_role 判断的表
DELETE FROM workflow_runs WHERE created_by IN ('ACCOUNT_ID') AND created_by_role = 'account';
DELETE FROM workflow_node_executions WHERE created_by IN ('ACCOUNT_ID') AND created_by_role = 'account';
DELETE FROM workflow_app_logs WHERE created_by IN ('ACCOUNT_ID') AND created_by_role = 'account';
DELETE FROM workflow_archive_logs WHERE created_by IN ('ACCOUNT_ID') AND created_by_role = 'account';
DELETE FROM upload_files WHERE created_by IN ('ACCOUNT_ID') AND created_by_role = 'account';
DELETE FROM message_files WHERE created_by IN ('ACCOUNT_ID') AND created_by_role = 'account';
DELETE FROM message_chains WHERE created_by IN ('ACCOUNT_ID') AND created_by_role = 'account';
DELETE FROM saved_messages WHERE created_by IN ('ACCOUNT_ID') AND created_by_role = 'account';
DELETE FROM pinned_conversations WHERE created_by IN ('ACCOUNT_ID') AND created_by_role = 'account';
DELETE FROM trigger_oauth_tenant_clients WHERE created_by IN ('ACCOUNT_ID') AND created_by_role = 'account';

-- 8. 最后删除账户本身
DELETE FROM accounts WHERE id IN ('ACCOUNT_ID');

COMMIT;
```

### 10.3 注意事项

- **执行顺序**：先删子表数据，最后删 `accounts` 表
- **tenant 删除需谨慎**：只有当 tenant 下仅剩该用户时才删除 tenant，否则只删 `tenant_account_joins` 中的关联记录
- **建议使用事务**：整个操作包裹在 `BEGIN ... COMMIT` 中，出错时自动回滚
- **生产环境**：执行前先运行 10.1 的查询确认影响范围

---

## 11. Gunicorn Worker 配置修复记录

### 问题描述

API 服务请求响应卡住（超时无返回），`curl http://192.168.31.214:9001/console/api/system-features` 等接口无响应。

**根本原因：** `docker/.env` 中 gunicorn worker 配置过低：

- `SERVER_WORKER_AMOUNT=1`：只有 1 个 worker 进程
- `SERVER_WORKER_CONNECTIONS=10`：每个 worker 最多 10 个并发连接

API 容器内堆积了大量 `CLOSE_WAIT` 状态的 TCP 连接（41 个），占满了 worker 的连接配额，导致新请求无法被处理。

### 修复内容

修改 `docker/.env` 中的以下参数：

| 参数 | 修改前 | 修改后 | 说明 |
|------|--------|--------|------|
| `SERVER_WORKER_AMOUNT` | 1 | 5 | worker 进程数，参考公式：`cpu cores * 2 + 1`（sync 模式），gevent 模式建议 1-5 |
| `SERVER_WORKER_CONNECTIONS` | 10 | 100 | 每个 worker 的最大并发连接数，gevent 模式下建议 100-1000 |

### 参考链接

- [Gunicorn Design - How Many Workers?](https://docs.gunicorn.org/en/stable/design.html#how-many-workers)

### 修复后验证

```bash
# 测试 API 响应
curl -s -m 10 http://192.168.31.214:9001/console/api/system-features

# 确认 gunicorn worker 配置
docker exec docker-api-1 sh -c "for pid in \$(ls /proc/ | grep -E '^[0-9]+$'); do cmd=\$(cat /proc/\$pid/cmdline 2>/dev/null | tr '\0' ' '); if echo \"\$cmd\" | grep -q gunicorn; then echo \"PID \$pid: \$cmd\"; fi; done"
# 输出应包含: --workers 5 --worker-connections 100
```
