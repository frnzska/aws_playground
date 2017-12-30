from pyspark.sql import SparkSession
from pyspark.sql import SQLContext

if __name__ == "__main__":
    spark = SparkSession.builder \
                .master("yarn-client") \
                .getOrCreate()

    sc = spark.sparkContext
    sqlContext = SQLContext(sc)
    print('Spark task')
    spark.stop()
