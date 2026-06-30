# Agent Shopping - 电商平台 + 多智能体客服

电商平台（shop-service）完整实现，包含用户、商品、交易、物流、售后六大业务域，配套 B 端管理后台和 C 端用户界面。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.12 + FastAPI + SQLAlchemy 2.0 (异步) |
| 数据库 | PostgreSQL 16 + Redis 7 |
| 认证 | JWT (python-jose) + bcrypt 密码哈希 |
| 缓存 | Redis Cache-Aside 模式，支持降级 |
| 定时任务 | APScheduler（超时订单自动取消） |
| 前端 | Vue 3 CDN + Tailwind CSS CDN（单文件 SPA） |
| 反向代理 | Nginx |
| 部署 | Docker Compose 一键启动 |

## 项目结构

```
agent_shopping/
├── docker-compose.yml          # 容器编排
├── nginx/nginx.conf            # Nginx 反向代理
├── 综合需求大纲.md
└── shop-service/
    ├── Dockerfile
    ├── requirements.txt
    ├── .env.example             # 环境变量模板
    ├── scripts/init_data.py     # 演示数据初始化
    └── app/
        ├── main.py              # FastAPI 入口 + 路由 + 定时任务
        ├── core/                # 配置、安全、依赖注入、异常、中间件
        ├── db/                  # 数据库会话 + Redis 缓存
        ├── models/              # 7 张数据表
        ├── schemas/             # Pydantic 请求/响应模型
        ├── services/            # 业务逻辑层
        ├── api/                 # API 路由层
        └── static/templates/    # 前端页面
            ├── index.html       # C 端用户界面
            └── admin.html       # B 端管理后台
```

## 快速开始

### 方式一：Docker Compose（推荐）

**前置条件：** 已安装 Docker Desktop 并处于运行状态。

```bash
# 克隆项目
git clone git@github.com:Eurekaaaaaa21/agent_shopping.git
cd agent_shopping

# 启动所有服务
docker-compose up --build

# 初始化演示数据（首次运行）
docker exec shop-service python scripts/init_data.py
```

启动完成后访问：

| 页面 | 地址 |
|------|------|
| C 端首页 | http://localhost:8080 |
| 管理后台 | http://localhost:8080/admin |
| API 文档 | http://localhost:8080/api/shop/docs |
| 健康检查 | http://localhost:8080/health |

**默认账号：**

| 角色 | 邮箱 | 密码 |
|------|------|------|
| 管理员 | admin@shop.com | admin123 |
| 测试用户 | test@shop.com | test123 |

### 方式二：本地运行

**前置条件：** Python 3.12+、PostgreSQL 16、Redis 7

```bash
cd shop-service

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（复制模板并修改）
cp .env.example .env

# 初始化数据库表和演示数据
python scripts/init_data.py

# 启动服务
python -m app.main
```

服务启动在 http://localhost:8001

## 环境变量说明

变量在 `.env` 文件中配置（参考 `.env.example`）：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | PostgreSQL 连接地址 | `postgresql://shop:shop123@localhost:5432/shop_db` |
| `REDIS_URL` | Redis 连接地址 | `redis://localhost:6379/0` |
| `JWT_SECRET_KEY` | JWT 签名密钥（生产环境务必修改） | `dev-secret-key-12345` |
| `DEBUG` | 调试模式 | `true` |
| `ORDER_TIMEOUT_MINUTES` | 订单超时时间（分钟） | `30` |
| `CACHE_TTL_HOT_PRODUCTS` | 热门商品缓存 TTL（秒） | `600` |
| `CACHE_TTL_PRODUCT_DETAIL` | 商品详情缓存 TTL（秒） | `600` |
| `CACHE_TTL_CATEGORY_TREE` | 分类树缓存 TTL（秒） | `3600` |

## API 概览

所有 API 前缀为 `/api/shop`，响应格式统一：

```json
{
  "code": 200,
  "message": "success",
  "data": { ... },
  "request_id": "xxx"
}
```

需认证的接口在请求头中携带 `Authorization: Bearer <token>`。

### C 端接口

| 端点 | 方法 | 说明 | 认证 |
|------|------|------|------|
| `/users/register` | POST | 注册（返回 Token） | 否 |
| `/users/login` | POST | 登录（返回 Token） | 否 |
| `/users/me` | GET/PUT | 获取/更新个人信息 | 是 |
| `/users/me/password` | PUT | 修改密码 | 是 |
| `/products/hot` | GET | 热门商品 | 否 |
| `/products/search` | GET | 搜索商品（支持关键词、分类、分页） | 否 |
| `/products/categories` | GET | 分类树 | 否 |
| `/products/{id}` | GET | 商品详情 | 否 |
| `/cart` | GET/POST | 获取/添加购物车 | 是 |
| `/cart/{item_id}` | PUT/DELETE | 修改数量/删除购物车项 | 是 |
| `/orders` | POST/GET | 创建/查询订单 | 是 |
| `/orders/{id}` | GET | 订单详情 | 是 |
| `/orders/{id}/pay` | POST | 模拟支付（幂等） | 是 |
| `/orders/{id}/cancel` | POST | 取消订单（回滚库存） | 是 |
| `/logistics/{order_id}` | GET | 物流追踪 | 是 |
| `/after-sales` | POST/GET | 申请/查询售后 | 是 |

### B 端管理接口（需管理员权限）

| 端点 | 方法 | 说明 |
|------|------|------|
| `/categories/admin` | POST/GET | 创建/列表 |
| `/categories/admin/{id}` | PUT/DELETE | 编辑/删除 |
| `/products/admin` | POST/GET | 发布/列表 |
| `/products/admin/{id}` | PUT | 编辑商品 |
| `/products/admin/{id}/toggle-status` | PUT | 上下架切换 |
| `/admin/orders` | GET | 全部订单 |
| `/admin/after-sales` | GET | 售后列表 |
| `/admin/after-sales/{id}/review` | POST | 审核售后 |
| `/admin/logistics/{order_id}/advance` | POST | 推进物流状态 |
| `/users/list` | GET | 用户列表 |

### 内部接口（供 ai-service 调用）

| 端点 | 说明 |
|------|------|
| `/internal/orders` | 查询当前用户订单（含明细） |
| `/internal/logistics?order_id=` | 查询指定订单物流 |
| `/internal/after-sales` | 查询当前用户售后 |
| `/internal/products/search?keyword=` | 搜索商品 |

内部接口透传用户 JWT，由 shop-service 自行解析 `user_id`，保证数据隔离。

## 业务规则速查

### 状态机

| 实体 | 状态流转 |
|------|----------|
| 订单 | `pending` → `paid` / `cancelled`（不可逆） |
| 商品 | `on_sale` ↔ `off_sale`（双向切换） |
| 物流 | `picked_up` → `in_transit` → `out_for_delivery` → `delivered` |
| 售后 | `pending` → `approved` / `rejected` → `completed` |

### 关键约束

- 仅 `pending` 状态的订单可支付/取消
- 仅 `paid` 状态的订单可申请售后
- 支付采用幂等校验（FOR UPDATE + status + 支付记录双重检查）
- 下单采用行级锁（FOR UPDATE）防止超卖
- 超时订单（默认 30 分钟）由定时任务自动取消，逐条独立事务
- Redis 缓存不可用时自动降级为数据库查询
- 订单明细保存商品名和价格快照，后续商品变更不影响历史订单
- 删除分类前校验是否有商品引用或子分类

## 注意事项

1. **生产环境安全**：务必修改 `JWT_SECRET_KEY`，不要使用默认值。建议使用至少 32 位随机字符串。

2. **首次启动**：Docker Compose 启动后需要手动执行 `init_data.py` 初始化演示数据，或通过注册接口创建用户。

3. **数据持久化**：PostgreSQL 数据存储在 Docker volume `pgdata` 中。执行 `docker-compose down` 不会删除数据，如需清除数据需加 `-volumes` 参数。

4. **端口冲突**：默认 Nginx 映射到 `8080` 端口。如果 8080 端口被占用，修改 `docker-compose.yml` 中 nginx 服务的 `ports` 映射。

5. **缓存一致性**：管理后台的写操作（发布/编辑/上下架商品、管理分类）会自动清除对应的 Redis 缓存。缓存有 TTL 过期机制作为兜底。

6. **前端页面**：C 端和管理后台均为单文件 SPA，无需构建工具，浏览器直接运行。修改 HTML 后需重启 shop-service 容器使更改生效。

7. **ai-service 集成**：`/internal/*` 接口已就绪，可供 ai-service 调用。ai-service 需要将前端用户的 JWT 透传给这些接口。nginx.conf 中预留了 `/api/ai/` 路由配置。

8. **日志**：通过 `X-Request-ID` 响应头可追踪请求链路，在日志中搜索对应 ID 查看完整处理过程。

## 许可证

本项目仅供学习和演示用途。
