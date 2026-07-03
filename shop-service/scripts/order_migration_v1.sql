-- 订单模块数据模型迁移 v1
-- 用途：为已有库添加阶段2新增的字段和索引
-- 执行：docker exec shop-postgres psql -U shop -d shop_db -f scripts/order_migration_v1.sql
--      或直接连接 PostgreSQL 执行

ALTER TABLE orders ADD COLUMN IF NOT EXISTS paid_at TIMESTAMPTZ;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMPTZ;
ALTER TABLE order_items ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_pending_time ON orders(created_at) WHERE status = 'pending';