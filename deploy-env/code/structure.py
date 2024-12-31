from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pyspark.sql import SparkSession
from datetime import datetime, timedelta, date
import re

from llm.llm import chat
from logger.logger import logger
from model.note import NoteInfo
from model.route import LLMRoutes, LLMRoute
from persistent.clickhouse_client import ClickhouseClient
from persistent.hdfs_client import HDFSClient


class StructureApplication:
    def __init__(self, spark, hdfs_client, clickhouse_client):
        self.spark = spark
        self.hdfs_client = hdfs_client
        self.clickhouse_client = clickhouse_client

    def run(self):
        logger.info("Starting the Spark job to process unstructured articles.")

        query = """
        SELECT n.*
        FROM citywalk_aide.note_infos AS n
        LEFT JOIN citywalk_aide.routes AS r
        ON n.id = r.note_id
        WHERE n.id <> r.note_id
        """

        logger.info("Querying ClickHouse for unprocessed notes...")
        note_infos = self.clickhouse_client.select(query, model_class=NoteInfo)
        logger.info("Fetched {} notes for processing.".format(len(note_infos)))

        # Parallelize notes processing using Spark RDD
        note_rdd = self.spark.sparkContext.parallelize(note_infos)
        results = note_rdd.map(self.process_note).collect()

        # Handle batch insertion into ClickHouse
        for route_batch, location_batch in results:
            if route_batch:
                self.clickhouse_client.insert(route_batch)
            if location_batch:
                self.clickhouse_client.insert(location_batch)

        logger.info("Completed processing all notes.")

    def process_note(self, note):
        try:
            logger.info("Processing note ID: {}, City: {}".format(note.id, note.city))
            html = self.hdfs_client.read_file(note.page_hdfs_path)

            soup = BeautifulSoup(html, 'html.parser')

            note_text_span = soup.select_one('#detail-desc > span > span:nth-child(1)')
            if note_text_span is None:
                logger.warning("Note ID {} - No text found in the HTML structure.".format(note.id))
                return [], []
            note_text = note_text_span.get_text(strip=True)

            note_create_time_span = soup.select_one(
                '#noteContainer > div.interaction-container > div.note-scroller > div.note-content > div.bottom-container > span.date'
            )
            if note_create_time_span is None:
                logger.warning("Note ID {} - No creation date found in the HTML structure.".format(note.id))
                return [], []
            note_create_time = extract_date(note_create_time_span.text.strip())

            logger.info("Note ID {} - Extracted text and creation date successfully.".format(note.id))

            llm_structured_result = chat(
                content=note_text,
                system=STRUCTURED_PROMPT,
                json_schema=LLMRoutes
            )
            llm_routes = LLMRoutes.model_validate_json(llm_structured_result)
            logger.info("Note ID {} - Successfully structured data using LLM.".format(note.id))

            route_batch = []
            location_batch = []
            for llm_route in llm_routes.routes:
                route, locations = llm_route.to_route_model()
                route.city = note.city
                route.published_at = note_create_time
                route_batch.append(route)
                location_batch.extend(locations)

            return route_batch, location_batch

        except Exception as e:
            logger.error("Error processing note ID {}: {}".format(note.id, str(e)), exc_info=True)
            return [], []


def extract_date(data_string):
    today = date.today()

    absolute_date_pattern = re.compile(r"(\d{4}-\d{2}-\d{2})")
    match = absolute_date_pattern.search(data_string)
    if match:
        try:
            return datetime.strptime(match.group(1), "%Y-%m-%d").date()
        except ValueError:
            logger.warning("Failed to parse absolute date: {}".format(data_string))
            return None

    short_date_pattern = re.compile(r"(\d{1,2})[-](\d{1,2})")
    match = short_date_pattern.search(data_string)
    if match:
        try:
            return datetime.strptime(
                "{}-{}-{}".format(today.year, match.group(1), match.group(2)), "%Y-%m-%d"
            ).date()
        except ValueError:
            logger.warning("Failed to parse short date: {}".format(data_string))
            return None

    if "今天" in data_string:
        return today
    elif "昨天" in data_string:
        return today - timedelta(days=1)
    elif "前天" in data_string:
        return today - timedelta(days=2)
    elif "天前" in data_string:
        days_ago_match = re.search(r"(\d+) 天前", data_string)
        if days_ago_match:
            days_ago = int(days_ago_match.group(1))
            return today - timedelta(days=days_ago)

    logger.warning("Failed to extract date from string: {}".format(data_string))
    return None


STRUCTURED_PROMPT = """
Parse the articles shared by users into structured Citywalk route data. Each article may correspond to multiple routes:
1.	Route: Each route contains multiple locations and basic information about the route, such as name, summary, etc.;
2.	Location: Each location contains a lot of basic information and may also include the following data:
    a.	Activities: Activities at the location, explaining what should be done at the current location, such as visiting, playing games, eating, etc.;
    b.	Transportation: Instructions on how to get to the location.
Notes:
1.	The content should be in Chinese;
2.	Strict numerical information not mentioned in the article, such as latitude and longitude, ticket fees, etc., should not be generated;
3.	For non-strict information, such as location descriptions, approximate visiting times, etc., if available, must be generated; if not, it can be freely created.
"""

if __name__ == '__main__':
    load_dotenv()

    spark = SparkSession.builder \
        .appName("Citywalk-aide Structure Processing") \
        .getOrCreate()
    logger.info("Spark Session initialized successfully.")

    hdfs_client = HDFSClient('http://localhost:50070', 'root')
    clickhouse_client = ClickhouseClient('citywalk_aide')

    main_program = StructureApplication(spark, hdfs_client, clickhouse_client)
    main_program.run()

    spark.stop()
    logger.info("Spark Session stopped. Application terminated.")