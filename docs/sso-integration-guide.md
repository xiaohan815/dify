# Dify SSO 集成指南

本文档介绍如何配置和使用Dify的SSO（单点登录）功能，允许第三方系统实现用户自动登录。

## 环境配置

在 `docker/.env` 中添加以下配置：

```bash
# SSO (Single Sign-On) Configuration
SSO_ENABLED=true
SSO_ALLOW_REGISTER=true
SSO_DEFAULT_ROLE=editor
```

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `SSO_ENABLED` | 是否启用SSO功能 | `false` |
| `SSO_ALLOW_REGISTER` | 是否允许通过SSO自动创建新用户 | `true` |
| `SSO_DEFAULT_ROLE` | 新用户的默认角色 | `editor` |

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
