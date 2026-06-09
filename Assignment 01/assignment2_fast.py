import os
os.environ["JAVA_HOME"] = "/Library/Java/JavaVirtualMachines/jdk-21.jdk/Contents/Home"

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, md5, concat_ws, coalesce, lit, to_date, year, month
import matplotlib.pyplot as plt

spark = SparkSession.builder.appName("Assignment2").getOrCreate()

df = spark.read.csv("lightcast_job_postings.csv", header=True, inferSchema=True, multiLine=True, escape='"')
df.createOrReplaceTempView("raw_jobs")

industries_df = df.select(
    md5(concat_ws("||", coalesce(col("NAICS_2022_6").cast("string"), lit("")), coalesce(col("SOC_5"), lit("")), coalesce(col("LOT_SPECIALIZED_OCCUPATION_NAME"), lit("")))).alias("industry_id"),
    col("NAICS_2022_6"),
    col("NAICS_2022_6_NAME"),
    col("SOC_5").alias("soc_code"),
    col("SOC_5_NAME").alias("soc_name"),
    col("LOT_SPECIALIZED_OCCUPATION_NAME").alias("specialized_occupation"),
    col("LOT_OCCUPATION_GROUP").alias("occupation_group")
).distinct()
industries_df.createOrReplaceTempView("industries")

companies_df = df.select(
    col("COMPANY").alias("company_id"),
    col("COMPANY"),
    col("COMPANY_NAME"),
    col("COMPANY_RAW"),
    col("COMPANY_IS_STAFFING")
).distinct()
companies_df.createOrReplaceTempView("companies")

locations_df = df.select(
    md5(concat_ws("||", coalesce(col("LOCATION"), lit("")), coalesce(col("CITY_NAME"), lit("")), coalesce(col("STATE_NAME"), lit("")), coalesce(col("MSA").cast("string"), lit("")))).alias("location_id"),
    col("LOCATION"),
    col("CITY_NAME"),
    col("STATE_NAME"),
    col("COUNTY_NAME"),
    col("MSA"),
    col("MSA_NAME")
).distinct()
locations_df.createOrReplaceTempView("locations")

job_postings_df = df.select(
    col("ID"),
    col("TITLE_CLEAN"),
    col("COMPANY").alias("company_id"),
    md5(concat_ws("||", coalesce(col("NAICS_2022_6").cast("string"), lit("")), coalesce(col("SOC_5"), lit("")), coalesce(col("LOT_SPECIALIZED_OCCUPATION_NAME"), lit("")))).alias("industry_id"),
    col("EMPLOYMENT_TYPE_NAME"),
    col("REMOTE_TYPE_NAME"),
    col("BODY"),
    col("MIN_YEARS_EXPERIENCE"),
    col("MAX_YEARS_EXPERIENCE"),
    col("SALARY"),
    col("SALARY_FROM"),
    col("SALARY_TO"),
    md5(concat_ws("||", coalesce(col("LOCATION"), lit("")), coalesce(col("CITY_NAME"), lit("")), coalesce(col("STATE_NAME"), lit("")), coalesce(col("MSA").cast("string"), lit("")))).alias("location_id"),
    col("POSTED"),
    col("EXPIRED"),
    col("DURATION")
)
job_postings_df.createOrReplaceTempView("job_postings")

q1 = spark.sql("""
SELECT i.NAICS_2022_6_NAME AS industry_name,
       i.specialized_occupation,
       percentile_approx(try_cast(j.SALARY as double), 0.5) AS median_salary
FROM job_postings j
JOIN industries i ON j.industry_id = i.industry_id
WHERE try_cast(i.NAICS_2022_6 as int) = 518210
  AND try_cast(j.SALARY as double) IS NOT NULL AND try_cast(j.SALARY as double) > 0
GROUP BY i.NAICS_2022_6_NAME, i.specialized_occupation
ORDER BY median_salary DESC
LIMIT 15
""")
q1p = q1.toPandas()
q1p.to_csv("query1_salary_trends.csv", index=False)
plt.figure(figsize=(10,6))
plt.barh(q1p["specialized_occupation"], q1p["median_salary"])
plt.gca().invert_yaxis()
plt.title("Median Salary by Specialized Occupation")
plt.xlabel("Median Salary")
plt.tight_layout()
plt.savefig("query1_salary_trends.png")

q2 = spark.sql("""
SELECT c.COMPANY_NAME AS company_name,
       COUNT(*) AS remote_jobs
FROM job_postings j
JOIN companies c ON j.company_id = c.company_id
JOIN locations l ON j.location_id = l.location_id
WHERE j.REMOTE_TYPE_NAME = 'Remote'
  AND l.STATE_NAME = 'California'
GROUP BY c.COMPANY_NAME
ORDER BY remote_jobs DESC
LIMIT 5
""")
q2p = q2.toPandas()
q2p.to_csv("query2_remote_ca_companies.csv", index=False)
plt.figure(figsize=(10,6))
plt.bar(q2p["company_name"], q2p["remote_jobs"])
plt.xticks(rotation=30, ha="right")
plt.title("Top 5 Companies with Remote Jobs in California")
plt.ylabel("Remote Jobs")
plt.tight_layout()
plt.savefig("query2_remote_ca_companies.png")

q3 = spark.sql("""
SELECT YEAR(to_date(j.POSTED, 'M/d/yyyy')) AS year,
       MONTH(to_date(j.POSTED, 'M/d/yyyy')) AS month,
       COUNT(*) AS job_count
FROM job_postings j
JOIN locations l ON j.location_id = l.location_id
WHERE l.STATE_NAME = 'California'
  AND to_date(j.POSTED, 'M/d/yyyy') IS NOT NULL
GROUP BY YEAR(to_date(j.POSTED, 'M/d/yyyy')), MONTH(to_date(j.POSTED, 'M/d/yyyy'))
ORDER BY year DESC, month DESC
""")
q3p = q3.toPandas()
q3p.to_csv("query3_monthly_ca_trends.csv", index=False)
plt.figure(figsize=(10,6))
for y in sorted(q3p["year"].dropna().unique()):
    temp = q3p[q3p["year"] == y].sort_values("month")
    plt.plot(temp["month"], temp["job_count"], marker="o", label=str(int(y)))
plt.title("Monthly Job Posting Trends in California")
plt.xlabel("Month")
plt.ylabel("Job Count")
plt.legend()
plt.tight_layout()
plt.savefig("query3_monthly_ca_trends.png")

q4 = spark.sql("""
SELECT CASE
    WHEN l.MSA = 14460 THEN 'Boston'
    WHEN l.MSA = 47900 THEN 'Washington DC'
    WHEN l.MSA = 35620 THEN 'New York'
    WHEN l.MSA = 41860 THEN 'San Francisco'
    WHEN l.MSA = 42660 THEN 'Seattle'
    WHEN l.MSA = 31080 THEN 'Los Angeles'
    WHEN l.MSA = 19100 THEN 'Dallas'
    WHEN l.MSA = 26420 THEN 'Houston'
    WHEN l.MSA = 12420 THEN 'Austin'
    WHEN l.MSA = 34980 THEN 'Nashville'
    WHEN l.MSA = 28140 THEN 'Kansas City'
    WHEN l.MSA = 19740 THEN 'Denver'
END AS metro_area,
ROUND(AVG(try_cast(j.SALARY as double)), 2) AS average_salary,
COUNT(*) AS job_count
FROM job_postings j
JOIN locations l ON j.location_id = l.location_id
WHERE try_cast(j.SALARY as double) IS NOT NULL AND try_cast(j.SALARY as double) > 0
  AND l.MSA IN (14460,47900,35620,41860,42660,31080,19100,26420,12420,34980,28140,19740)
GROUP BY l.MSA
ORDER BY average_salary DESC
""")
q4p = q4.toPandas()
q4p.to_csv("query4_city_salary_comparison.csv", index=False)
plt.figure(figsize=(11,6))
plt.bar(q4p["metro_area"], q4p["average_salary"])
plt.xticks(rotation=35, ha="right")
plt.title("Average Salary Across Major US Metro Areas")
plt.ylabel("Average Salary")
plt.tight_layout()
plt.savefig("query4_city_salary_comparison.png")

with open("assignment2_report.md", "w") as f:
    f.write("# Module 2 Assignment: Spark SQL and DataFrames\n\n")
    f.write("GitHub Repository URL: https://github.com/wenlutong199-oss/wenlutong199.github.io\n\n")
    f.write("This assignment uses Spark SQL to create relational tables from the Lightcast job postings dataset and analyze job roles, salaries, remote work, and location trends.\n\n")
    f.write("## Relational Tables\nThe analysis created four relational tables: job_postings, companies, industries, and locations. The job_postings table uses foreign keys to connect postings with company, industry, and location information.\n\n")
    f.write("## Query 1: Industry-Specific Salary Trends\nThe first query focuses on the technology industry and calculates median salaries by specialized occupation. Higher median salaries suggest stronger compensation for certain specialized roles.\n\n![](query1_salary_trends.png)\n\n")
    f.write("## Query 2: Top Remote Companies in California\nThe second query identifies the top five companies with the most remote job postings in California.\n\n![](query2_remote_ca_companies.png)\n\n")
    f.write("## Query 3: Monthly Job Posting Trends in California\nThe third query shows how job postings in California change by month and year.\n\n![](query3_monthly_ca_trends.png)\n\n")
    f.write("## Query 4: Salary Comparisons Across Major US Cities\nThe fourth query compares average salaries across selected major metropolitan areas.\n\n![](query4_city_salary_comparison.png)\n\n")

print("DONE. Files created:")
print("assignment2_report.md")
print("query1_salary_trends.png")
print("query2_remote_ca_companies.png")
print("query3_monthly_ca_trends.png")
print("query4_city_salary_comparison.png")
spark.stop()
