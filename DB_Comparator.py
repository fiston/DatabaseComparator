from sqlalchemy import create_engine
import pandas as pd

def collect_schema_info(conn_str, output_prefix):
    engine = create_engine(conn_str)
    queries = {
        'table_schema_info': """
            SELECT table_schema, table_name, column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
            ORDER BY table_schema, table_name, column_name
        """,
        'view_schema_info': """
            SELECT table_schema, table_name, view_definition
            FROM information_schema.views
            WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
            ORDER BY table_schema, table_name
        """,
        'index_schema_info': """
            SELECT
                n.nspname AS schema_name,
                t.relname AS table_name,
                i.relname AS index_name,
                pg_get_indexdef(i.oid) AS index_def
            FROM
                pg_class t,
                pg_class i,
                pg_index ix,
                pg_namespace n
            WHERE
                t.oid = ix.indrelid
                AND i.oid = ix.indexrelid
                AND n.oid = t.relnamespace
                AND n.nspname NOT IN ('information_schema', 'pg_catalog')
            ORDER BY
                schema_name, table_name, index_name
        """
    }

    for name, query in queries.items():
        df = pd.read_sql_query(query, engine)
        df.to_csv(f'/tmp/{output_prefix}_{name}.csv', index=True)

def compare_csv(file1, file2, key_columns):
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)

    df1.set_index(key_columns, inplace=True)
    df2.set_index(key_columns, inplace=True)

    # Align DataFrames to have the same columns and indexes
    df1, df2 = df1.align(df2, join='outer', axis=1)
    
    # Ensure the DataFrames are compared correctly by filling NaNs with a placeholder value
    df1.fillna('', inplace=True)
    df2.fillna('', inplace=True)

    diff = df1.sort_index().compare(df2.sort_index(), align_axis=1)
    return diff

def generate_sync_sql(table_diff, view_diff, index_diff):
    sql_statements = []

    for index, row in table_diff.iterrows():
        schema, table, column = index
        if 'data_type' in row and pd.isna(row['data_type']):
            sql_statements.append(f"ALTER TABLE {schema}.{table} ADD COLUMN {column} {row['data_type']};")

    for index, row in view_diff.iterrows():
        schema, view = index
        sql_statements.append(f"CREATE OR REPLACE VIEW {schema}.{view} AS {row['view_definition']};")

    for index, row in index_diff.iterrows():
        schema, table, index_name = index
        sql_statements.append(f"CREATE INDEX {index_name} ON {schema}.{table} {row['index_def']};")

    return sql_statements

def main():
    conn_str1 = 'postgresql://postgres:postgres@10.102.33.140:5432/loans'
    conn_str2 = 'postgresql://postgres:postgres@10.102.33.140:5432/loan'

    collect_schema_info(conn_str1, 'db1')
    collect_schema_info(conn_str2, 'db2')

    table_diff = compare_csv('/tmp/db1_table_schema_info.csv', '/tmp/db2_table_schema_info.csv', ['table_schema', 'table_name', 'column_name'])
    view_diff = compare_csv('/tmp/db1_view_schema_info.csv', '/tmp/db2_view_schema_info.csv', ['table_schema', 'table_name'])
    index_diff = compare_csv('/tmp/db1_index_schema_info.csv', '/tmp/db2_index_schema_info.csv', ['schema_name', 'table_name', 'index_name'])

    sync_sql = generate_sync_sql(table_diff, view_diff, index_diff)
    
    with open('/tmp/sync_schema.sql', 'w') as file:
        for sql in sync_sql:
            file.write(sql + '\n')

if __name__ == "__main__":
    main()
