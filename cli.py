"""命令行入口：athena-query "SELECT ..."  [--out result.csv]"""
import argparse

from .client import query


def main():
    parser = argparse.ArgumentParser(description="在 AWS Athena 上执行 SQL")
    parser.add_argument("sql", help="SQL 语句，或 .sql 文件路径")
    parser.add_argument("--db", help="数据库名（默认读 .env 的 ATHENA_DATABASE）")
    parser.add_argument("--out", help="把结果保存为 CSV")
    args = parser.parse_args()

    sql = args.sql
    if sql.endswith(".sql"):
        with open(sql, encoding="utf-8") as f:
            sql = f.read()

    df = query(sql, database=args.db)
    print(df.head(20).to_string(index=False))
    print(f"\n共 {len(df)} 行")

    if args.out:
        df.to_csv(args.out, index=False)
        print(f"已保存到 {args.out}")


if __name__ == "__main__":
    main()
