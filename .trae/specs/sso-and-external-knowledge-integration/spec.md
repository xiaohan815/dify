# SSO单点登录与外部知识库集成规范

## Why

当前Dify需要以下功能增强：

### 1. SSO单点登录
第三方系统无法通过安全的方式自动登录Dify用户。需要一种机制让外部系统验证用户身份并自动创建/登录用户，默认角色为"编辑"（editor）。

### 2. 外部知识库连接指南
Dify已有通用的外部知识库API框架（`ExternalKnowledgeApis` + `ExternalKnowledgeBindings`），支持任何实现了标准 `/retrieval` 接口的系统。需要：
- 明确外部知识库接入的API规范
- 提供RAGFlow等系统的适配指南
- 如有必要，扩展框架以支持更多认证方式

## What Changes

### 功能一：SSO单点登录
- 新增基于共享密钥的SSO认证端点
- 支持自动用户创建，默认角色为"编辑"（editor）
- 支持现有用户自动登录
- 支持用户属性同步（姓名、邮箱等）

### 功能二：外部知识库接入指南
- 文档化现有的外部知识库API规范
- 提供RAGFlow适配示例
- 评估是否需要扩展认证方式（当前仅支持Bearer Token）

## Impact

- Affected specs: 用户认证
- Affected code:
  - `api/controllers/console/auth/` - 新增SSO认证控制器
  - `api/services/account_service.py` - 扩展用户创建逻辑
  - 文档更新 - 外部知识库接入指南

---

## ADDED Requirements

### Requirement: SSO单点登录认证

系统应提供基于共享密钥的SSO单点登录功能，允许第三方系统安全地认证用户。

#### Scenario: 新用户自动创建并登录
- **WHEN** 第三方系统携带有效的SSO令牌请求登录
- **AND** 该用户在Dify中不存在
- **THEN** 系统应自动创建新用户账户
- **AND** 新用户默认角色为"编辑"（editor）
- **AND** 返回有效的访问令牌

#### Scenario: 现有用户自动登录
- **WHEN** 第三方系统携带有效的SSO令牌请求登录
- **AND** 该用户在Dify中已存在
- **THEN** 系统应返回有效的访问令牌
- **AND** 可选择同步用户属性信息

#### Scenario: 无效令牌拒绝
- **WHEN** 第三方系统携带无效或过期的SSO令牌请求登录
- **THEN** 系统应拒绝访问
- **AND** 返回401未授权错误

#### Scenario: SSO配置管理
- **WHEN** 管理员配置SSO设置
- **THEN** 系统应安全存储共享密钥
- **AND** 支持配置令牌有效期
- **AND** 支持配置默认用户角色

### Requirement: 外部知识库API规范文档

系统应提供清晰的外部知识库接入API规范。

#### Scenario: 查看API规范
- **WHEN** 开发者需要接入外部知识库
- **THEN** 系统应提供完整的API规范文档
- **AND** 包含认证方式说明
- **AND** 包含请求/响应格式说明

#### Scenario: RAGFlow适配示例
- **WHEN** 用户需要连接RAGFlow知识库
- **THEN** 系统应提供RAGFlow适配指南
- **AND** 包含配置步骤说明
- **AND** 包含必要的代码示例（如需适配层）

---

## MODIFIED Requirements

### Requirement: 用户注册流程扩展

原有用户注册流程需要扩展以支持SSO自动创建用户。

**修改内容**：
- 新增 `RegisterService.register_from_sso()` 方法
- 支持指定默认角色创建用户
- 支持SSO来源标记

---

## REMOVED Requirements

无移除的需求。

---

## 现有外部知识库框架说明

Dify已实现的外部知识库集成架构：

### 数据模型
- `ExternalKnowledgeApis`: 存储外部API配置
  - `endpoint`: 外部API基础URL
  - `api_key`: 认证密钥
  - `settings`: JSON格式的额外配置

- `ExternalKnowledgeBindings`: 数据集与外部知识库绑定
  - `external_knowledge_api_id`: 关联的API配置
  - `external_knowledge_id`: 外部系统的知识库ID
  - `dataset_id`: Dify数据集ID

### 检索接口规范
外部系统需实现以下接口：

```
POST {endpoint}/retrieval
Authorization: Bearer {api_key}
Content-Type: application/json

{
  "query": "查询文本",
  "knowledge_id": "外部知识库ID",
  "retrieval_setting": {
    "top_k": 2,
    "score_threshold": 0.0
  }
}
```

响应格式：
```json
{
  "records": [
    {
      "content": "知识片段内容",
      "title": "文档标题",
      "score": 0.85,
      "metadata": {}
    }
  ]
}
```

### 认证方式
当前支持：Bearer Token认证

如需支持其他认证方式（如Basic Auth、自定义Header等），需要扩展 `Authorization` 实体。
