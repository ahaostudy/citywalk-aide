from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum, max

spark = SparkSession.builder \
    .appName("SalesAnalysis") \
    .getOrCreate()

file_path = "hdfs://namenode:8020/user/example/sales_data.csv"
sales_df = spark.read.csv(file_path, header=True, inferSchema=True)

print("Raw sales data:")
sales_df.show()

product_sales = sales_df.groupBy("product") \
    .agg(
    sum(col("quantity")).alias("total_quantity"),
    sum(col("quantity") * col("price")).alias("total_sales")
) \
    .orderBy(col("total_sales").desc())

print("Total sales and total quantity of each product:")
product_sales.show()

customer_purchases = sales_df.groupBy("customer_id") \
    .agg(
    sum(col("quantity")).alias("total_quantity"),
    sum(col("quantity") * col("price")).alias("total_spent")
) \
    .orderBy(col("total_quantity").desc())

print("Customers who buy the most items:")
customer_purchases.show()

output_path = "hdfs://namenode:8020/output/"
product_sales.write.csv(output_path + "product_sales", header=True, mode="overwrite")
customer_purchases.write.csv(output_path + "customer_purchases", header=True, mode="overwrite")

print("Results saved to HDFS directory:" + output_path)

spark.stop()
