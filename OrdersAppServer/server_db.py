import psycopg2 as pgdb
import time
from datetime import datetime, timedelta
import threading
import pytz

conn = pgdb.connect(dbname="orders_app", host="localhost", user="postgres", password="88f5XX7", port="5432")

def check_and_update_sessions():
    while True:
        try:
            cursor = conn.cursor()
            query = """
                SELECT id, login_date 
                FROM sessions 
                WHERE out_date IS NULL
            """
            cursor.execute(query)
            sessions = cursor.fetchall()
            cursor.close()

            for session_id, login_date_str in sessions:
                if (datetime.now(pytz.utc) - login_date_str) > timedelta(days=14):
                    try:
                        cursor = conn.cursor()
                        update_query = """
                            UPDATE sessions
                            SET out_date = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """
                        cursor.execute(update_query, (session_id,))
                        conn.commit()
                        cursor.close()
                    except Exception as e:
                        print(f"Error updating session {session_id}: {e}")

        except Exception as e:
            print(f"Error fetching sessions: {e}")

        time.sleep(3600)

# Запускаем проверку в отдельном потоке
thread = threading.Thread(target=check_and_update_sessions)
thread.start()