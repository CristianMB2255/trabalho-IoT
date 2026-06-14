import pandas as pd
import datetime as dt
from flask import Flask, render_template, request, jsonify
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

# Data stored every 10 minutes, takes X steps to a complete an hour
HOUR_STEPS = 6 
 
def create_db_connection():
    """Create database connection with PostgreSQL."""
    return psycopg2.connect(
                user=pg_user,
                password=pg_pass,
                host=pg_host,
                database=pg_db,
                sslmode="require"
            ) 

def create_cache_connection():
    """Create connection with redis cache."""
    return redis.Redis(
        host=redis_host,
        port=redis_port,
        decode_responses=True,
        username=redis_user,
        password=redis_pass,
    )

def dates_around(date, days_before=2, days_after=2):
    """Produce a list containing the surrounding dates."""
    return [
        (date + dt.timedelta(days=i)).strftime("%d-%m-%Y")
        for i in range(-days_before, days_after + 1)
    ]

def dates_boundaries(dates):
    """Produce the min and max datas from list."""

    if not dates: 
        return None, None
    
    return dates[0], dates[-1] + dt.timedelta(days=1)

def fetch_cache(pending, r):
    """Get cache data, returns rows and list of found datas."""
    if not pending:
        return [], []

    rows = []
    found = []

    for date in pending:
        key = pd.to_datetime(date, dayfirst=True).strftime("%d-%m-%Y")
        cached = r.get(key)

        if cached is not None:
            print("Cache hit") # !!!
            rows.extend(json.loads(cached))
            found.append(date)

    return rows, found

def fetch_db(pending, min, max):
    """"Fetch all data in db."""
    if not pending:
        return []

    connection = create_db_connection()
    cursor = connection.cursor(cursor_factory=RealDictCursor)

    query = "SELECT timestamp, temperature, humidity FROM data  WHERE timestamp > %s AND timestamp < %s ORDER BY timestamp DESC"
    
    cursor.execute(query, [min, max])

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    return rows

def cache_db_data(db_df, pending_dates, r):
    try:
        cached_dates = set()

        for date, group in db_df.groupby(db_df["timestamp"].dt.strftime("%d-%m-%Y")):
            r.setex(
                date,
                900,
                group.to_json(date_format="iso", orient="records")
            )
            cached_dates.add(date)

        for date in pending_dates:
            key = date.strftime("%d-%m-%Y")
            if key not in cached_dates:
                r.setex(key, 900, "[]")

    except Exception as error:
        print(error)

def calculate_stats(series):
    """Calculate stats for the given series."""
    if series.empty:
        return {
            "min": None,
            "max": None,
            "mean": None
        }
    
    return {
        "min": round(series.min(), 1),
        "max": round(series.max(), 1),
        "mean": round(series.mean(), 1)
    }

def get_stats(df):
    """Get stats for the given dataframe."""
    if df.empty:
        return None

    df["temperature"] = pd.to_numeric(df["temperature"])
    df["humidity"] = pd.to_numeric(df["humidity"])

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        format="%d-%m-%Y %H"
    )

    grouped = df.groupby(df["timestamp"].dt.strftime("%d-%m-%Y"))
    stats_df = pd.DataFrame()

    rows = []

    for day, group in grouped:
        temperature_stats = calculate_stats(group["temperature"])
        humidity_stats = calculate_stats(group["humidity"])

        rows.append({
            "day": day,

            "temp_min": temperature_stats["min"],
            "temp_max": temperature_stats["max"],
            "temp_mean": temperature_stats["mean"],

            "hum_min": humidity_stats["min"],
            "hum_max": humidity_stats["max"],
            "hum_mean": humidity_stats["mean"]
        })

    stats_df = pd.DataFrame(rows)

    return stats_df

@app.route("/")
def index():
    selected_date = request.args.get('date')

    if selected_date:

        # Get dates around the selected one
        formatted_date = pd.to_datetime(selected_date, format="%d-%m-%Y")
        pending_dates = dates_around(formatted_date)

        r = create_cache_connection()
        dfs = []

        # Get cache data
        cache_data, found_dates = fetch_cache(pending_dates, r)

        pending_dates = [pd.to_datetime(date, format="%d-%m-%Y")
                         for date in pending_dates if date not in found_dates]

        if cache_data:
            dfs.append(pd.DataFrame(cache_data))

        min_bound, max_bound = dates_boundaries(pending_dates)

        if pending_dates:
            db_data = fetch_db(pending_dates, min_bound, max_bound)

            if db_data:
                db_df = pd.DataFrame(db_data)
                dfs.append(db_df)
            else:
                db_df = pd.DataFrame(columns=["timestamp", "temperature", "humidity"])

            db_df["timestamp"] = pd.to_datetime(db_df["timestamp"])
            cache_db_data(db_df, pending_dates, r)

        r.close()

        if not dfs:
            return jsonify([])

        df = pd.concat(dfs, ignore_index=True)

        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df['timestamp'] = df['timestamp'].dt.strftime('%d-%m-%Y %H')

        stats = get_stats(df)

        print(stats) # !!!

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
    
    dtt = {
            # "is_latest": True,
            "current": {
                "date": "20-05-2026",
                "temperature": 19,
                "humidity": 55,
                "mean_temperature": 19.5
            },
            "prev": {
                "date": stats.iloc[1]["day"],
                "temperature": stats.iloc[1]["temp_mean"],
                "humidity": stats.iloc[1]["hum_mean"]
            },
            "prev2": {
                "date": stats.iloc[0]["day"],
                "temperature": stats.iloc[0]["temp_mean"],
                "humidity": stats.iloc[0]["hum_mean"]
            },
            "next": {
                "date": stats.iloc[3]["day"],
                "temperature": stats.iloc[3]["temp_mean"],
                "humidity": stats.iloc[3]["hum_mean"]
            },
            "next2": {
                "date": stats.iloc[4]["day"],
                "temperature": stats.iloc[4]["temp_mean"],
                "humidity": stats.iloc[4]["hum_mean"]
            },
            
            "chart_data": generate_chart()
        }
        
    date_pos = 'right'
    
    if date_pos == 'left':
        dtt.update({'selected_date_position': 'left'})
    elif date_pos == 'middle':
        dtt.update({'selected_date_position': 'middle'})
    elif date_pos == 'right':
        dtt.update({'selected_date_position': 'right'})

    return render_template(
        "index.html",
        data=(dtt)
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
