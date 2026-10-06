"""最小可用的 Athena 查询：提交 SQL -> 等待完成 -> 拿回 DataFrame。"""
import os
import time

import boto3
import pandas as pd
from dotenv import find_dotenv, load_dotenv


def _athena_client():
    return boto3.client(
        "athena",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        aws_session_token=os.getenv("AWS_SESSION_TOKEN") or None,
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )


def query(sql: str, database: str | None = None, timeout: int = 600) -> pd.DataFrame:
    """执行一条 SQL，返回 pandas DataFrame（所有值为字符串，需要时自行转类型）。"""
    # 从“运行命令的目录”往上找 .env（usecwd=True 很关键，否则会去包的安装目录找）
    load_dotenv(find_dotenv(usecwd=True))
    athena = _athena_client()
    database = database or os.getenv("ATHENA_DATABASE")

    params = {
        "QueryString": sql,
        "QueryExecutionContext": {"Database": database},
        "WorkGroup": os.getenv("ATHENA_WORKGROUP", "primary"),
    }
    output = os.getenv("ATHENA_OUTPUT_LOCATION")
    if output:
        params["ResultConfiguration"] = {"OutputLocation": output}

    qid = athena.start_query_execution(**params)["QueryExecutionId"]

    # 等待查询结束
    start = time.time()
    while True:
        status = athena.get_query_execution(QueryExecutionId=qid)["QueryExecution"]["Status"]
        state = status["State"]
        if state == "SUCCEEDED":
            break
        if state in ("FAILED", "CANCELLED"):
            raise RuntimeError(f"Athena 查询{state}: {status.get('StateChangeReason')}")
        if time.time() - start > timeout:
            athena.stop_query_execution(QueryExecutionId=qid)
            raise TimeoutError(f"查询超过 {timeout}s，已取消 (id={qid})")
        time.sleep(1)

    # 分页取结果
    rows, columns = [], None
    for page in athena.get_paginator("get_query_results").paginate(QueryExecutionId=qid):
        page_rows = page["ResultSet"]["Rows"]
        if columns is None:
            columns = [c["Name"] for c in page["ResultSet"]["ResultSetMetadata"]["ColumnInfo"]]
            page_rows = page_rows[1:]  # 第一页第一行是表头
        for r in page_rows:
            rows.append([cell.get("VarCharValue") for cell in r["Data"]])

    return pd.DataFrame(rows, columns=columns)
