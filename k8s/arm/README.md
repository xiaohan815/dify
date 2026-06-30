# Dify ARM K8s 部署命令

## 1. 复制 YAML 到 master

如果在 167 上执行，先把本目录传到 master：

```bash
ssh root@10.160.53.101 'mkdir -p /tmp/xcloud-dify-arm'
scp -r dify/k8s/arm/* root@10.160.53.101:/tmp/xcloud-dify-arm/
```

也可以直接从 Mac 或 Windows 上传到 master 的 `/tmp/xcloud-dify-arm`。

## 2. 在 Mac 上停止旧 Dify 并打包 volumes

先停本地 Dify，避免数据库和文件卷一边写一边打包：

```bash
cd /Users/xhm5/work/xcloud501/dify/docker
docker compose stop
```

打包旧 volumes：

```bash
cd /Users/xhm5/work/xcloud501/dify/docker

tar -C volumes/db/data -czf /tmp/dify-postgres.tgz .
tar -C volumes/redis/data -czf /tmp/dify-redis.tgz .
tar -C volumes/weaviate -czf /tmp/dify-weaviate.tgz .
tar -C volumes/app/storage -czf /tmp/dify-app-storage.tgz .
tar -C volumes/plugin_daemon -czf /tmp/dify-plugin-daemon.tgz .
```

如果某个目录不存在，说明旧环境没有用到那块，可以跳过对应 tar。

同时记录旧环境的 `SECRET_KEY`：

```bash
grep '^SECRET_KEY=' /Users/xhm5/work/xcloud501/dify/docker/.env
```

迁移旧数据库时，K8s Secret 里的 `secret-key` 必须用这个旧值。

## 3. 上传 volumes 包到 master

```bash
scp /tmp/dify-*.tgz root@10.160.53.101:/tmp/
```

## 4. 在 master 上准备 NFS 目录并解压旧 volumes

```bash
mkdir -p /mnt/xcloud-nfs/xcloud-deepdoc/dify/{postgres,redis,weaviate,app-storage,plugin-daemon}

tar --no-same-owner -xzf /tmp/dify-postgres.tgz \
  -C /mnt/xcloud-nfs/xcloud-deepdoc/dify/postgres

tar --no-same-owner -xzf /tmp/dify-redis.tgz \
  -C /mnt/xcloud-nfs/xcloud-deepdoc/dify/redis

tar --no-same-owner -xzf /tmp/dify-weaviate.tgz \
  -C /mnt/xcloud-nfs/xcloud-deepdoc/dify/weaviate

tar --no-same-owner -xzf /tmp/dify-app-storage.tgz \
  -C /mnt/xcloud-nfs/xcloud-deepdoc/dify/app-storage

tar --no-same-owner -xzf /tmp/dify-plugin-daemon.tgz \
  -C /mnt/xcloud-nfs/xcloud-deepdoc/dify/plugin-daemon

chmod -R u+rwX,go+rwX /mnt/xcloud-nfs/xcloud-deepdoc/dify
```

确认 Postgres 目录结构：

```bash
ls -lah /mnt/xcloud-nfs/xcloud-deepdoc/dify/postgres
ls -lah /mnt/xcloud-nfs/xcloud-deepdoc/dify/postgres/pgdata | head
stat -c '%u:%g %a %n' /mnt/xcloud-nfs/xcloud-deepdoc/dify/postgres/pgdata
```

如果 `stat` 显示 owner 是 `1024:100` 或类似 `1024:users`，当前 YAML 已按这个 UID 跑 Postgres。

## 5. 创建 Secret

推荐使用独立部署目录里的统一模板创建：

```bash
cd /tmp/k8s-arm-deploy
cp secrets/create-secrets.template.sh secrets/create-secrets.local.sh
vi secrets/create-secrets.local.sh
bash secrets/create-secrets.local.sh
```

注意：

- `DIFY_SECRET_KEY` 必须使用旧 `dify/docker/.env` 里的 `SECRET_KEY`。
- `DIFY_RESEND_API_KEY` 必须有值，否则当前 Dify API / Worker / Beat 会启动失败。
- `secrets/create-secrets.local.sh` 只在服务器本地保存，不提交 Git。

## 6. 部署

```bash
kubectl apply -k /tmp/xcloud-dify-arm
kubectl -n xcloud get pvc | grep dify
kubectl -n xcloud get pod,svc -o wide | grep dify
```

## 7. 查看启动日志

```bash
kubectl -n xcloud logs -f deploy/xcloud-dify-postgres --tail=100
kubectl -n xcloud logs -f deploy/xcloud-dify-api --tail=200
kubectl -n xcloud logs -f deploy/xcloud-dify-worker --tail=100
kubectl -n xcloud logs -f deploy/xcloud-dify-web --tail=100
```

## 8. 验证访问

```bash
curl -I http://10.160.53.101:30092
curl -s http://10.160.53.101:30092/console/api/setup
```

地址：

```text
外部入口: http://10.160.53.101:30092
内部入口: http://xcloud-dify-nginx.xcloud.svc.cluster.local
内部 API: http://xcloud-dify-nginx.xcloud.svc.cluster.local/v1
```
