from pyspark.sql import SparkSession
from pyspark.sql import SQLContext

import time

if __name__ == "__main__":
    spark = SparkSession.builder \
                .master("yarn-client") \
                .getOrCreate()

    sc = spark.sparkContext
    sqlContext = SQLContext(sc)
    print('Spark task')
    time.sleep(20)
    spark.stop()
