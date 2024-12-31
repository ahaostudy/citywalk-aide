import time
import schedule
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import datetime, timedelta, date
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from llm.llm import chat
from logger.logger import logger
from model.note import NoteInfo
from model.route import LLMRoutes, LLMRoute
from persistent.clickhouse_client import ClickhouseClient
from persistent.hdfs_client import HDFSClient


class StructureApplication:
    def __init__(self, hdfs_client: HDFSClient, clickhouse_client: ClickhouseClient):
        self.hdfs_client = hdfs_client
        self.clickhouse_client = clickhouse_client

    def process_note(self, note: NoteInfo):
        logger.info(f"Processing note ID: {note.id}")

        try:
            html = self.hdfs_client.read_file(note.page_hdfs_path)
            logger.info(f"Read HTML for note ID: {note.id} from HDFS.")
        except Exception as e:
            logger.error(f"Error reading file for note ID {note.id}: {e}")
            return

        soup = BeautifulSoup(html, 'html.parser')

        note_text_span = soup.select_one('#detail-desc > span > span:nth-child(1)')
        if note_text_span is None:
            logger.warning(f"No note text found for note ID {note.id}. Skipping this note.")
            return
        note_text = note_text_span.get_text(strip=True)

        note_create_time_span = soup.select_one(
            '#noteContainer > div.interaction-container > div.note-scroller > div.note-content > div.bottom-container > span.date'
        )
        if note_create_time_span is None:
            logger.warning(f"No creation time found for note ID {note.id}. Skipping this note.")
            return
        note_create_time = extract_date(note_create_time_span.text.strip())

        llm_structured_result = chat(
            content=note_text,
            system=STRUCTURED_PROMPT,
            json_schema=LLMRoutes
        )
        llm_routes = LLMRoutes.model_validate_json(llm_structured_result)

        for llm_route in llm_routes.routes:
            logger.info(f"Processing route for note ID {note.id}...")
            route, locations = llm_route.to_route_model()
            route.note_id = note.id
            route.city = note.city
            route.liked_count = note.liked_count
            route.published_at = note_create_time

            try:
                self.clickhouse_client.insert(locations)
                self.clickhouse_client.insert([route])
                logger.info(f"Inserted route and locations for note ID {note.id} into Clickhouse.")
            except Exception as e:
                logger.error(f"Error inserting data for note ID {note.id}: {e}")

    def run(self):
        logger.info("Starting the application...")

        query = """
        SELECT n.*
        FROM citywalk_aide.note_infos AS n
        LEFT JOIN citywalk_aide.routes AS r
        ON n.id = r.note_id
        WHERE n.id <> r.note_id
        ORDER BY n.created_at
        """

        try:
            note_infos = self.clickhouse_client.select(query, model_class=NoteInfo)
        except Exception as e:
            logger.error(f"Error retrieving note infos: {e}")
            return

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(self.process_note, note) for note in note_infos]

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Error in processing note: {e}")


def extract_date(data_string):
    today = date.today()

    absolute_date_pattern = re.compile(r"(\d{4}-\d{2}-\d{2})")
    match = absolute_date_pattern.search(data_string)
    if match:
        try:
            return datetime.strptime(match.group(1), "%Y-%m-%d").date()
        except ValueError:
            return None

    short_date_pattern = re.compile(r"(\d{1,2})[-](\d{1,2})")
    match = short_date_pattern.search(data_string)
    if match:
        try:
            return datetime.strptime(f"{today.year}-{match.group(1)}-{match.group(2)}", "%Y-%m-%d").date()
        except ValueError:
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
4.  If there is no valid route content in the article, {"routes": []} should be returned, and the list of locations for each route should be greater than 1
"""

if __name__ == '__main__':
    load_dotenv()

    hdfs_client = HDFSClient('http://localhost:50070', 'root')
    clickhouse_client = ClickhouseClient('citywalk_aide')
    main_program = StructureApplication(hdfs_client, clickhouse_client)

    print("Scheduler started. Waiting for the job to run...")

    main_program.run()
    schedule.every().day.at("10:00").do(main_program.run)

    while True:
        schedule.run_pending()
        time.sleep(600)
