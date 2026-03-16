# Tasks

## 功能一：SSO单点登录

- [x] Task 1: 创建SSO配置模型和数据库迁移
  - [x] SubTask 1.1: 创建 `SsoConfig` 模型，存储SSO配置（密钥、有效期、默认角色等）
  - [x] SubTask 1.2: 创建数据库迁移脚本
  - [x] SubTask 1.3: 添加SSO配置管理API端点

- [x] Task 2: 实现SSO认证服务
  - [x] SubTask 2.1: 创建 `SsoService` 服务类
  - [x] SubTask 2.2: 实现JWT令牌生成和验证逻辑
  - [x] SubTask 2.3: 实现用户自动创建逻辑，默认角色为editor
  - [x] SubTask 2.4: 实现现有用户登录逻辑

- [x] Task 3: 创建SSO认证API端点
  - [x] SubTask 3.1: 创建 `/console/api/sso/login` 端点
  - [x] SubTask 3.2: 创建 `/console/api/sso/token` 端点（用于令牌交换）
  - [x] SubTask 3.3: 添加请求验证和错误处理

- [x] Task 4: 扩展用户服务支持SSO
  - [x] SubTask 4.1: 在 `RegisterService` 中添加 `register_from_sso()` 方法
  - [x] SubTask 4.2: 在 `AccountService` 中添加SSO相关方法
  - [x] SubTask 4.3: 支持SSO来源标记和追踪

- [x] Task 5: 编写SSO功能单元测试
  - [x] SubTask 5.1: 测试新用户自动创建
  - [x] SubTask 5.2: 测试现有用户登录
  - [x] SubTask 5.3: 测试无效令牌处理
  - [x] SubTask 5.4: 测试配置管理API

## 功能二：外部知识库接入指南

- [x] Task 6: 研究RAGFlow API兼容性
  - [x] SubTask 6.1: 调研RAGFlow的检索API接口
  - [x] SubTask 6.2: 对比Dify外部知识库API规范
  - [x] SubTask 6.3: 确定是否需要适配层

- [ ] Task 7: 实现RAGFlow适配（如需要）
  - [ ] SubTask 7.1: 创建RAGFlow适配服务（如果RAGFlow不兼容Dify规范）
  - [ ] SubTask 7.2: 实现RAGFlow到Dify格式的转换
  - [ ] SubTask 7.3: 添加RAGFlow配置模板

- [ ] Task 8: 扩展认证方式（可选）
  - [ ] SubTask 8.1: 评估是否需要支持Basic Auth
  - [ ] SubTask 8.2: 评估是否需要支持自定义Header认证
  - [ ] SubTask 8.3: 实现必要的认证扩展

## 文档和配置

- [x] Task 9: 更新配置文件和环境变量
  - [x] SubTask 9.1: 添加SSO相关环境变量
  - [x] SubTask 9.2: 更新配置文档

- [x] Task 10: 编写集成文档
  - [x] SubTask 10.1: 编写SSO集成指南
  - [x] SubTask 10.2: 编写外部知识库API规范文档
  - [x] SubTask 10.3: 编写RAGFlow集成示例（如需要）

# Task Dependencies

- Task 2 依赖 Task 1（SSO服务需要配置模型）
- Task 3 依赖 Task 2（API端点需要服务层）
- Task 4 依赖 Task 2（用户服务扩展需要SSO服务）
- Task 5 依赖 Task 1-4（测试需要完整功能）
- Task 7 依赖 Task 6（适配实现需要兼容性分析）
- Task 8 可独立进行（认证扩展）
- Task 9-10 可以与开发任务并行进行
