# Dify 外部知识库集成指南

本文档介绍如何将外部知识库（如RAGFlow）连接到Dify，实现统一的知识检索服务。

## 概述

Dify支持通过标准API接口连接外部知识库系统。外部知识库需要实现Dify定义的检索接口规范，Dify会自动调用并返回检索结果。

## 外部知识库API规范

外部知识库系统需要实现以下检索接口：

### 请求格式

```http
POST {endpoint}/retrieval
Authorization: Bearer {api_key}
Content-Type: application/json

{
  "query": "用户查询文本",
  "knowledge_id": "外部系统的知识库ID",
  "retrieval_setting": {
    "top_k": 3,
    "score_threshold": 0.5
  }
}
```

### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `query` | string | 是 | 用户查询文本 |
| `knowledge_id` | string | 是 | 外部知识库的唯一标识 |
| `retrieval_setting` | object | 否 | 检索设置 |
| `retrieval_setting.top_k` | int | 否 | 返回的最大结果数，默认3 |
| `retrieval_setting.score_threshold` | float | 否 | 相似度阈值，默认0.0 |

### 响应格式

```json
{
  "records": [
    {
      "content": "知识片段内容...",
      "title": "文档标题",
      "score": 0.85,
      "metadata": {
        "source": "document.pdf",
        "page": 1
      }
    }
  ]
}
```

### 响应字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `records` | array | 是 | 检索结果列表 |
| `records[].content` | string | 是 | 知识片段内容 |
| `records[].title` | string | 否 | 文档标题 |
| `records[].score` | float | 否 | 相似度分数（0-1） |
| `records[].metadata` | object | 否 | 额外元数据 |

---

## 配置步骤

### 1. 创建外部知识库API配置

在Dify控制台中，进入 **知识库 → 外部知识库API** 页面，创建新的API配置。

**API请求：**

```http
POST /console/api/datasets/external-knowledge-api
Authorization: Bearer {admin_access_token}
Content-Type: application/json

{
  "name": "RAGFlow Knowledge API",
  "settings": {
    "endpoint": "https://your-ragflow-server/api/v1",
    "api_key": "your-api-key"
  }
}
```

**响应：**

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "RAGFlow Knowledge API",
  "settings": {
    "endpoint": "https://your-ragflow-server/api/v1",
    "api_key": "your-api-key"
  },
  "created_at": "2026-03-16T12:00:00"
}
```

### 2. 创建外部知识库数据集

使用创建的API配置，绑定外部知识库：

```http
POST /console/api/datasets/external
Authorization: Bearer {admin_access_token}
Content-Type: application/json

{
  "external_knowledge_api_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "external_knowledge_id": "ragflow-kb-001",
  "name": "产品文档知识库",
  "description": "来自RAGFlow的产品文档知识库"
}
```

**参数说明：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `external_knowledge_api_id` | string | 是 | 外部知识库API配置ID |
| `external_knowledge_id` | string | 是 | 外部系统的知识库ID |
| `name` | string | 是 | 数据集名称 |
| `description` | string | 否 | 数据集描述 |

### 3. 测试检索

```http
POST /console/api/datasets/{dataset_id}/external-hit-testing
Authorization: Bearer {admin_access_token}
Content-Type: application/json

{
  "query": "如何使用API？",
  "external_retrieval_model": {
    "top_k": 3,
    "score_threshold": 0.5
  }
}
```

---

## Java/Spring Boot适配示例

第三方Java系统需要实现Dify定义的 `/retrieval` 接口，供Dify调用。

### Controller实现

```java
package com.example.knowledge.controller;

import com.example.knowledge.dto.RetrievalRequest;
import com.example.knowledge.dto.RetrievalResponse;
import com.example.knowledge.service.KnowledgeService;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api")
public class KnowledgeRetrievalController {

    private final KnowledgeService knowledgeService;
    private static final String VALID_API_KEY = "your-api-key";

    public KnowledgeRetrievalController(KnowledgeService knowledgeService) {
        this.knowledgeService = knowledgeService;
    }

    @PostMapping("/retrieval")
    public RetrievalResponse retrieval(
            @RequestHeader(value = "Authorization", required = false) String authorization,
            @RequestBody RetrievalRequest request) {
        
        // 验证API Key
        if (authorization == null || !authorization.startsWith("Bearer ")) {
            throw new UnauthorizedException("Missing or invalid Authorization header");
        }
        String token = authorization.substring(7);
        if (!VALID_API_KEY.equals(token)) {
            throw new UnauthorizedException("Invalid API key");
        }

        // 调用知识库检索服务
        return knowledgeService.retrieve(request);
    }
}
```

### 请求/响应DTO

```java
package com.example.knowledge.dto;

import java.util.List;
import java.util.Map;

public class RetrievalRequest {
    private String query;
    private String knowledgeId;
    private RetrievalSetting retrievalSetting;

    // Getters and Setters
    public String getQuery() { return query; }
    public void setQuery(String query) { this.query = query; }
    public String getKnowledgeId() { return knowledgeId; }
    public void setKnowledgeId(String knowledgeId) { this.knowledgeId = knowledgeId; }
    public RetrievalSetting getRetrievalSetting() { return retrievalSetting; }
    public void setRetrievalSetting(RetrievalSetting retrievalSetting) { this.retrievalSetting = retrievalSetting; }

    public int getTopK() {
        return retrievalSetting != null ? retrievalSetting.getTopK() : 3;
    }

    public double getScoreThreshold() {
        return retrievalSetting != null ? retrievalSetting.getScoreThreshold() : 0.0;
    }

    public static class RetrievalSetting {
        private int topK = 3;
        private double scoreThreshold = 0.0;

        public int getTopK() { return topK; }
        public void setTopK(int topK) { this.topK = topK; }
        public double getScoreThreshold() { return scoreThreshold; }
        public void setScoreThreshold(double scoreThreshold) { this.scoreThreshold = scoreThreshold; }
    }
}

public class RetrievalResponse {
    private List<Record> records;

    public List<Record> getRecords() { return records; }
    public void setRecords(List<Record> records) { this.records = records; }

    public static class Record {
        private String content;
        private String title;
        private double score;
        private Map<String, Object> metadata;

        // Getters and Setters
        public String getContent() { return content; }
        public void setContent(String content) { this.content = content; }
        public String getTitle() { return title; }
        public void setTitle(String title) { this.title = title; }
        public double getScore() { return score; }
        public void setScore(double score) { this.score = score; }
        public Map<String, Object> getMetadata() { return metadata; }
        public void setMetadata(Map<String, Object> metadata) { this.metadata = metadata; }
    }
}
```

### Service实现（基于向量数据库）

```java
package com.example.knowledge.service;

import com.example.knowledge.dto.RetrievalRequest;
import com.example.knowledge.dto.RetrievalResponse;
import com.example.knowledge.dto.RetrievalResponse.Record;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
public class KnowledgeService {

    private final VectorStoreClient vectorStoreClient;

    public KnowledgeService(VectorStoreClient vectorStoreClient) {
        this.vectorStoreClient = vectorStoreClient;
    }

    public RetrievalResponse retrieve(RetrievalRequest request) {
        // 1. 根据knowledgeId获取对应的知识库配置
        String collectionName = getCollectionName(request.getKnowledgeId());

        // 2. 调用向量数据库进行相似度检索
        List<VectorSearchResult> results = vectorStoreClient.search(
            collectionName,
            request.getQuery(),
            request.getTopK(),
            request.getScoreThreshold()
        );

        // 3. 转换为Dify格式
        RetrievalResponse response = new RetrievalResponse();
        List<Record> records = results.stream()
            .map(this::convertToRecord)
            .collect(Collectors.toList());
        response.setRecords(records);

        return response;
    }

    private Record convertToRecord(VectorSearchResult result) {
        Record record = new Record();
        record.setContent(result.getContent());
        record.setTitle(result.getMetadata().getOrDefault("title", "").toString());
        record.setScore(result.getScore());
        
        Map<String, Object> metadata = new HashMap<>();
        metadata.put("source", result.getMetadata().getOrDefault("source", ""));
        metadata.put("docId", result.getMetadata().getOrDefault("docId", ""));
        record.setMetadata(metadata);
        
        return record;
    }

    private String getCollectionName(String knowledgeId) {
        // 根据knowledgeId映射到实际的向量库collection
        // 例如：kb-001 -> product_docs
        Map<String, String> mapping = Map.of(
            "kb-001", "product_docs",
            "kb-002", "tech_manuals"
        );
        return mapping.getOrDefault(knowledgeId, knowledgeId);
    }
}
```

### 配置Dify连接

在Dify中配置外部知识库API：

```http
POST /console/api/datasets/external-knowledge-api
Authorization: Bearer {admin_access_token}
Content-Type: application/json

{
  "name": "Java Knowledge Service",
  "settings": {
    "endpoint": "http://your-java-service:8080/api",
    "api_key": "your-api-key"
  }
}
```

### 完整项目结构

```
src/main/java/com/example/knowledge/
├── controller/
│   └── KnowledgeRetrievalController.java
├── dto/
│   ├── RetrievalRequest.java
│   └── RetrievalResponse.java
├── service/
│   └── KnowledgeService.java
├── config/
│   └── VectorStoreConfig.java
└── Application.java

src/main/resources/
└── application.yml
```

### application.yml配置

```yaml
server:
  port: 8080

knowledge:
  api-key: ${KNOWLEDGE_API_KEY:your-api-key}
  
vector-store:
  type: milvus  # 或 pgvector, elasticsearch 等
  host: ${VECTOR_STORE_HOST:localhost}
  port: ${VECTOR_STORE_PORT:19530}
```

---

## RAGFlow适配示例（可选）

如果使用RAGFlow作为底层知识库，需要创建适配层转换API格式。

**Python Flask适配示例：**

```python
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

RAGFLOW_BASE_URL = "https://your-ragflow-server/api/v1"
RAGFLOW_API_KEY = "your-ragflow-api-key"

# 知识库ID映射
KNOWLEDGE_MAPPING = {
    "kb-001": "产品文档",
    "kb-002": "技术手册",
}

@app.route("/retrieval", methods=["POST"])
def retrieval():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return {"error": "Unauthorized"}, 401
    
    token = auth_header[7:]
    # 验证token（可选）
    
    data = request.json
    query = data.get("query")
    knowledge_id = data.get("knowledge_id")
    retrieval_setting = data.get("retrieval_setting", {})
    top_k = retrieval_setting.get("top_k", 3)
    score_threshold = retrieval_setting.get("score_threshold", 0.0)
    
    # 调用RAGFlow API
    response = requests.post(
        f"{RAGFLOW_BASE_URL}/retrieval",
        headers={
            "Authorization": f"Bearer {RAGFLOW_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "question": query,
            "kb_ids": [knowledge_id],
            "top_k": top_k,
            "score_threshold": score_threshold
        }
    )
    
    if response.status_code != 200:
        return {"error": "RAGFlow API error"}, 500
    
    ragflow_result = response.json()
    
    # 转换为Dify格式
    records = []
    for chunk in ragflow_result.get("chunks", []):
        if chunk.get("similarity", 1.0) >= score_threshold:
            records.append({
                "content": chunk.get("content", ""),
                "title": chunk.get("document_name", ""),
                "score": chunk.get("similarity", 0.0),
                "metadata": {
                    "source": chunk.get("document_name", ""),
                    "page": chunk.get("page_number"),
                    "kb_name": KNOWLEDGE_MAPPING.get(knowledge_id, "")
                }
            })
    
    return {"records": records}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
```

**Docker部署适配层：**

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY adapter.py .
RUN pip install flask requests

EXPOSE 5002
CMD ["python", "adapter.py"]
```

### 配置Dify连接适配层

```http
POST /console/api/datasets/external-knowledge-api
Authorization: Bearer {admin_access_token}
Content-Type: application/json

{
  "name": "RAGFlow via Adapter",
  "settings": {
    "endpoint": "http://adapter-host:5002",
    "api_key": "your-adapter-api-key"
  }
}
```

---

## API参考

### 外部知识库API管理

| 端点 | 方法 | 说明 |
|------|------|------|
| `/console/api/datasets/external-knowledge-api` | GET | 获取外部知识库API列表 |
| `/console/api/datasets/external-knowledge-api` | POST | 创建外部知识库API配置 |
| `/console/api/datasets/external-knowledge-api/{id}` | GET | 获取单个API配置 |
| `/console/api/datasets/external-knowledge-api/{id}` | PATCH | 更新API配置 |
| `/console/api/datasets/external-knowledge-api/{id}` | DELETE | 删除API配置 |
| `/console/api/datasets/external-knowledge-api/{id}/use-check` | GET | 检查API使用状态 |

### 外部数据集管理

| 端点 | 方法 | 说明 |
|------|------|------|
| `/console/api/datasets/external` | POST | 创建外部知识库数据集 |
| `/console/api/datasets/{id}/external-hit-testing` | POST | 测试外部知识库检索 |

---

## 常见问题

### Q: 支持哪些认证方式？

当前仅支持Bearer Token认证。如需其他认证方式（如Basic Auth、API Key Header等），需要扩展适配层。

### Q: 如何处理大量检索结果？

通过 `top_k` 参数限制返回结果数量，建议设置为3-10。

### Q: 检索超时怎么办？

外部知识库API调用有默认超时时间。如果知识库响应较慢，可以在适配层设置更长的超时时间。

### Q: 如何实现多知识库联合检索？

在适配层中，可以将单个 `knowledge_id` 映射到多个外部知识库，合并检索结果后返回。

---

## 最佳实践

1. **适配层部署**：建议将适配层部署在与Dify相同的网络环境中，减少网络延迟
2. **缓存机制**：对于高频查询，可在适配层添加缓存
3. **错误处理**：适配层应处理外部API的错误，返回友好的错误信息
4. **监控告警**：监控适配层的请求量和响应时间
5. **安全加固**：验证来自Dify的请求Token，防止未授权访问
