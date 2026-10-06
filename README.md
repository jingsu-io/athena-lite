# athena-lite

一个轻量的 AWS Athena 查询工具：写一条 SQL，拿回一个 pandas DataFrame。AWS 凭证从 `.env` 读取。

## 1. 安装

需要 Python 3.10+。

```bash
cd athena-lite
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e .
```

conda 环境下跳过 venv 两行，直接 `pip install -e .`。

## 2. 配置 `.env`

```bash
cp .env.example .env
```

打开 `.env` 填写：

| 变量 | 必填 | 说明 |
|---|---|---|
| `AWS_ACCESS_KEY_ID` | 是 | IAM Access Key |
| `AWS_SECRET_ACCESS_KEY` | 是 | IAM Secret Key |
| `AWS_SESSION_TOKEN` | 否 | 只有临时凭证才需要 |
| `AWS_REGION` | 是 | Athena 所在区域，例如 `us-east-1` |
| `ATHENA_DATABASE` | 是 | 默认数据库 |
| `ATHENA_OUTPUT_LOCATION` | 视情况 | 查询结果写入的 S3 路径。workgroup 已设置结果位置时可留空 |
| `ATHENA_WORKGROUP` | 否 | 默认 `primary` |

`.env` 要放在**你运行命令的目录**（或其上层目录）。`.env` 已在 `.gitignore` 里，不会被提交。

## 3. 测试连接

```bash
athena-query "SELECT 1 AS hello"
```

看到下面的输出就说明连通了：

```
hello
    1

共 1 行
```

## 4. 使用

### 命令行

```bash
# 直接写 SQL
athena-query "SELECT * FROM my_table LIMIT 10"

# 从 .sql 文件读取
athena-query query.sql

# 临时换数据库
athena-query "SELECT * FROM orders LIMIT 10" --db other_db

# 保存为 CSV
athena-query "SELECT * FROM my_table" --out result.csv
```

### Python 代码

```python
from athena_lite import query

df = query("SELECT * FROM my_table LIMIT 100")
print(df.head())

# 指定其他数据库、超时时间（秒）
df = query("SELECT * FROM orders", database="other_db", timeout=1200)
```

完整示例见 `examples/example.py`。

## 5. 注意事项

- **返回值全是字符串**。需要数字或日期时自己转：
  ```python
  df["qty"] = pd.to_numeric(df["qty"])
  df["order_date"] = pd.to_datetime(df["order_date"])
  ```
- **数据库名带连字符**（如 `io-datamart-v2`）：`.env` 里直接写；SQL 里引用时要加双引号：`SELECT * FROM "io-datamart-v2"."my_table"`。
- **大结果集**：结果按每页 1000 行分页拉取，几十万行以上会比较慢，建议在 SQL 里先聚合或加 `LIMIT`。
- 查询超过 `timeout`（默认 600 秒）会自动取消，避免继续扫描计费。

## 6. 常见错误

| 报错 | 原因 / 解决 |
|---|---|
| `NoCredentialsError` / `UnrecognizedClientException` | `.env` 没被读到（不在当前目录），或 key 填错 |
| `AccessDeniedException` | IAM 用户缺少 Athena / Glue / S3 权限 |
| `InvalidRequestException ... output location` | 没填 `ATHENA_OUTPUT_LOCATION`，且 workgroup 也没设置结果位置 |
| `Athena 查询FAILED: SYNTAX_ERROR ...` | SQL 语法问题，报错信息里有具体行列 |
| `TABLE_NOT_FOUND` / `SCHEMA_NOT_FOUND` | 数据库名或表名不对，检查 `ATHENA_DATABASE` 和区域 |

所需 IAM 权限（最少）：`athena:StartQueryExecution`、`athena:GetQueryExecution`、`athena:GetQueryResults`、`athena:StopQueryExecution`、`glue:GetTable`、`glue:GetDatabase`，以及对数据所在 bucket 的 `s3:GetObject`/`s3:ListBucket`、对结果 bucket 的 `s3:PutObject`/`s3:GetBucketLocation`。

## 项目结构

```
athena-lite/
├── athena_lite/
│   ├── __init__.py
│   ├── client.py      # query() 核心逻辑
│   └── cli.py         # athena-query 命令
├── examples/
│   └── example.py
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```
