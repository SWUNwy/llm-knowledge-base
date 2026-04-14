# Docker 部署指南

## 快速开始

### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API Keys
```

### 2. 启动服务

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 3. 访问应用

- 前端: http://localhost:3000
- 后端健康检查: http://localhost:3000/api/v1/status

## 服务说明

| 服务 | 容器名 | 端口 | 说明 |
|------|--------|------|------|
| Backend | llm-kb-backend | 8000 (内部) | FastAPI 服务 |
| Frontend | llm-kb-frontend | 3000 | Nginx + React 构建 |

## 数据持久化

所有数据存储在 Docker volume `wiki-data` 中：

```bash
# 查看 volume
docker volume ls

# 备份数据
docker run --rm -v llm-kb-knowledge-base_wiki-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/wiki-backup.tar.gz -C /data .

# 恢复数据
docker run --rm -v llm-kb-knowledge-base_wiki-data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/wiki-backup.tar.gz -C /data
```

## 常用命令

```bash
# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看服务状态
docker-compose ps

# 进入后端容器
docker-compose exec backend bash

# 查看后端日志
docker-compose logs backend

# 重新构建镜像
docker-compose build
```

## 生产环境部署

1. 修改 `APP_SECRET_KEY` 为强随机字符串
2. 配置反向代理 (如 Traefik、Nginx)
3. 启用 HTTPS
4. 配置定期备份
