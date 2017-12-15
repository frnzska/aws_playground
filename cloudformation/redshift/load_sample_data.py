import psycopg2
import os


HOST = os.environ['REDSHIFT_ENDPOINT']
PORT = 5439
USER = os.environ['REDSHIFT_USER']
PASSWORD = os.environ['REDSHIFT_PASSWORD']
DATABASE = 'dwh'


def db_connection():
    conn = psycopg2.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
        database=DATABASE,
    )
    return conn


def query(*,query, conn):
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall() # careful, the results could be huge, chunk then or hand out head
    conn.commit()
    return results



def create_table(*,schema_path, conn):
    with open(schema_path) as f:
        query = f.read()
        print(query)
    f.closed
    cursor = conn.cursor()
    cursor.execute(query)



def copy_from_s3(*, table_name, s3_manifest, conn):
    query = f"copy {table_name} from '{s3_manifest}' iam_role 'arn:aws:iam::369667221252:role/RedshiftIAMRole' delimiter ',' csv manifest;"
    cursor = conn.cursor()
    cursor.execute(query)



conn = db_connection()
#create_table(schema_path='cloudformation/redshift/my_table_schema.sql', conn=conn)
#copy_from_s3(table_name='my_test_data',
#             s3_manifest='s3://franziska-adler-deployments/production/aws_playground/cloudformation/redshift/mydata.manifest',
#             conn=conn)
#
example_query = "select * from information_schema.tables"
res = query(query=example_query,conn=conn)
print(res)

conn.close()
