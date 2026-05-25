import pandas as pd
import datetime as dt
from flask import Flask, render_template, request
import math
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import redis
import random
import json

app = Flask(__name__)

pg_user    = os.getenv("PGUSER")
pg_pass    = os.getenv("PGPASS")
pg_host    = os.getenv("PGHOST")
pg_db      = os.getenv("PGDB")
redis_host = os.getenv("RHOST")
redis_port = os.getenv("RPORT")
redis_user = os.getenv("RUSER")
redis_pass = os.getenv("RPASS")

# Data stored every 10 minutes, takes X steps to a complete hour
HOUR_STEPS = 6 
 
def get_db_connection():
    """Create database connection with PostgreSQL."""
    return psycopg2.connect(
                user=pg_user,
                password=pg_pass,
                host=pg_host,
                database=pg_db,
                sslmode="require"
            ) 

def calculate_stats(series):
    """Calculate data metricas and return as object."""
    if series.empty:
        return {
            "max": None,
            "min": None,
            "avg": None,
            "median": None,
            "std_dev": None
        }

    return {
        "max": round(series.max(), 2),
        "min": round(series.min(), 2),
        "avg": round(series.mean(), 2),
        "median": round(series.median(), 2),
        "std_dev": round(series.std(), 2)
    }

def get_data_db():
    """Fetch all data in db."""
    try:
        connection = get_db_connection()

        # Faz as consultas retornarem dicts
        cursor = connection.cursor(cursor_factory=RealDictCursor)

        query = "SELECT timestamp, temperature, humidity FROM data ORDER BY timestamp DESC"

        cursor.execute(query)

        rows = cursor.fetchall()

        cursor.close()
        connection.close()

        return rows
    
    except Exception as e:
        print(f"Erro ao buscar dados do PostgreSQL: {e}")

        return None 

def get_data():
    """Fetch all data."""
    r = redis.Redis(
        host=redis_host,
        port=redis_port,
        decode_responses=True,
        username=redis_user,
        password=redis_pass,
    )

    key = "data"

    # Fetch cache
    data = r.get(key)

    if data:
        return json.loads(data)
    
    #Fetch db
    data = get_data_db()

    if data:
        r.setex("data", 900, json.dumps(data, default=str))

    return data    

def get_processed_data(timeframe_hours='all', start_date=None, end_date=None, page=1, limit=50): 
    """Get stored data, return as object."""

    rows = get_data()

    if not rows:
        empty_stats = calculate_stats(pd.Series(dtype=float))

        return {
            "data": [],
            "timeframe_hours": timeframe_hours,
            "temperature_infos": empty_stats,
            "humidity_infos": empty_stats,
            "pagination": {
                "page": 1,
                "limit": limit,
                "total_pages": 1,
                "total_records": 0
            }
        }

    df = pd.DataFrame(rows)

    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Postgres Decimal -> float
    df['temperature'] = pd.to_numeric(df['temperature'])
    df['humidity'] = pd.to_numeric(df['humidity'])

    # Time filter
    if start_date and end_date:
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        df = df.query("@start_date < timestamp < @end_date")

    # Timeframe filter
    elif timeframe_hours != 'all':
        cutoff_time = dt.datetime.now() - dt.timedelta(hours=float(timeframe_hours))

        df = df.query("timestamp > @cutoff_time")

    total_records = len(df)
    total_pages = math.ceil(total_records / limit)

    if page < 1:
        page = 1

    if page > total_pages and total_pages > 1:
        page = total_pages

    start_index = (page - 1) * (limit * HOUR_STEPS)
    end_index = start_index + (limit * HOUR_STEPS)

    # Cut data to be rendered
    paginated_df = df.iloc[end_index - 1:start_index:-HOUR_STEPS].copy()

    paginated_df['timestamp'] = paginated_df['timestamp'].dt.strftime(
        #'%Y-%m-%d %H:%M'
        '%H:00'
    )

    temperature_stats = calculate_stats(paginated_df['temperature'])
    humidity_stats = calculate_stats(paginated_df['humidity'])

    data_list = paginated_df.to_dict('records')

    return {
        "data": data_list,
        "timeframe_hours": timeframe_hours,
        "temperature_infos": temperature_stats,
        "humidity_infos": humidity_stats,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "total_records": total_records
        }
    }

@app.route("/")
def index():

    IS_LATEST = True

    def generate_chart():
        pts = []
        base = dt.datetime.fromisoformat("2024-05-20T00:00:00")

        for i in range(24):
            t = base + dt.timedelta(hours=i)

            pts.append({
                "timestamp": t.strftime("%H:%M"),
                "temperature": round(
                    17.8
                    + math.sin(i / 6) * 1.2
                    + i * 0.04
                    + (random.random() - 0.5) * 0.3,
                    1
                ),
                "humidity": round(
                    55
                    + math.cos(i / 5) * 4
                    + (random.random() - 0.5) * 2,
                    1
                )
            })

        return pts

    if IS_LATEST:
        dtt = {
            "is_latest": True,
            "current": {
                "date": "20/05",
                "temperature": 19,
                "humidity": 55,
                "mean_temperature": 19.5
            },
            "prev": {
                "date": "19/05",
                "temperature": 19,
                "humidity": 55
            },
            "next": None,
            "prev2": {
                "date": "18/05",
                "temperature": 18,
                "humidity": 60
            },
            "chart_data": generate_chart()
        }

    else:
        dtt = {
            "is_latest": False,
            "current": {
                "date": "20/05",
                "temperature": 19,
                "humidity": 55,
                "mean_temperature": 19.5
            },
            "prev": {
                "date": "19/05",
                "temperature": 19,
                "humidity": 55
            },
            "next": {
                "date": "21/05",
                "temperature": 20,
                "humidity": 52
            },
            "prev2": None,
            "chart_data": generate_chart()
        }
    
    return render_template(
        "index.html",
        data=dtt
    )
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    filter_arg = request.args.get('filter', 'all')
    
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1

    try:
        limit = int(request.args.get('limit', 50))
    except ValueError:
        limit = 50

    try:
        timeframe_hours = float(filter_arg[:-1])   
    except:
        timeframe_hours = 'all'
    
    data_to_render = get_processed_data(
        timeframe_hours=timeframe_hours,
        start_date=start_date,
        end_date=end_date,
        page=page,
        limit=limit
    )
    
    return render_template(
        "index.html",
        data=data_to_render,
        start_date=start_date,
        end_date=end_date,
        current_filter=filter_arg
    )

if __name__ == '__main__':
    print("Iniciando o servidor Flask...")
    app.run(host='0.0.0.0')