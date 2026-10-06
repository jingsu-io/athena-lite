from athena_lite import query

df = query("SELECT 1 AS hello, current_date AS today")
print(df)
