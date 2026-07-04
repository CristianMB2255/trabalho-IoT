import pandas as pd
import datetime as dt
from flask import Flask, render_template, request 
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import redis
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

def create_db_connection():
    """Create database connection with PostgreSQL."""
    return psycopg2.connect(
                user=pg_user,
                password=pg_pass,
                host=pg_host,
                database=pg_db,
                sslmode="require"
            ) 

def create_redis_connection():
    """Create connection with redis cache."""
    return redis.Redis(
        host=redis_host,
        port=redis_port,
        decode_responses=True,
        username=redis_user,
        password=redis_pass,
    )

def normalize_data(df):
    """Convert data to a standard format."""
    if df.empty:
        # Typed columns so .dt/.mean still work on empty data
        return pd.DataFrame({
            "timestamp": pd.Series(dtype="datetime64[ns]"),
            "temperature": pd.Series(dtype="float64"),
            "humidity": pd.Series(dtype="float64"),
        })

    df = df.copy()

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    df["temperature"] = pd.to_numeric(
        df["temperature"],
        errors="coerce"
    )

    df["humidity"] = pd.to_numeric(
        df["humidity"],
        errors="coerce"
    )

    return df

def dates_around(date, days_before=2, days_after=2):
    """Produce a list containing the surrounding dates."""
    return [
        date + dt.timedelta(days=i)
        for i in range(-days_before, days_after + 1)
    ]

def dates_boundaries(dates):
    """Produce the min and max dates from list."""

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
        key = date.strftime("%d-%m-%Y")
        cached = r.get(key)

        if cached is not None:
            rows.extend(json.loads(cached))
            found.append(date)

    return rows, found

def fetch_db(pending):
    """"Fetch all data in db."""
    if not pending:
        return []

    connection = create_db_connection()
    cursor = connection.cursor(cursor_factory=RealDictCursor)

    query = "SELECT timestamp, temperature, humidity FROM data  WHERE timestamp >= %s AND timestamp < %s ORDER BY timestamp DESC"
    
    min, max = dates_boundaries(pending)
    cursor.execute(query, [min, max])

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    return rows

def cache_db_data(db_df, pending_dates, r):
    try:
        cached_dates = set()

        if not db_df.empty:
            for date, group in db_df.groupby(db_df["timestamp"].dt.strftime("%d-%m-%Y")):
                r.setex(
                    date,
                    900,
                    group.to_json(date_format="iso", orient="records")
                )
                cached_dates.add(date)

        # Prevent fetching a non-existent date in db
        for date in pending_dates:
            key = date.strftime("%d-%m-%Y")
            if key not in cached_dates:
                r.setex(key, 900, "[]")

    except Exception as error:
        print(error)

def get_stats(df):
    """Get stats for the given dataframe."""
    if df.empty:
        return pd.DataFrame({"day": [None]})

    grouped = df.groupby(df["timestamp"].dt.date)
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

def calculate_stats(series):
    """Calculate stats for the given series."""
    series = series.dropna()
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

def get_day_stats(stats_df, date):
    """Return stats for a date, None if missing from stats_df."""
    row = stats_df[stats_df["day"] == date.date()]

    if row.empty:
        return {
            "date": date.strftime("%d-%m-%Y"),
            "temperature": None,
            "humidity": None,
            "loaded": False
        }

    row = row.iloc[0]
    return {
        "date": date.strftime("%d-%m-%Y"),
        "temperature": row["temp_mean"],
        "humidity": row["hum_mean"],
        "loaded": True
    }

def generate_chart(df):
    df = df.copy()

    grouped = df.groupby(df["timestamp"].dt.floor("h"), as_index=False).agg(
        temperature=("temperature", "mean"),
        humidity=("humidity", "mean")
    ).dropna()

    pts = []
    for _, row in grouped.iterrows():
        pts.append({
            "timestamp": row["timestamp"].strftime("%H:%M"),
            "temperature": round(row["temperature"], 1),
            "humidity": round(row["humidity"], 1)
        })

    return pts

@app.route("/")
def index():
    selected_date = request.args.get("date")

    if selected_date:
        selected_date = pd.to_datetime(selected_date, format="%d-%m-%Y")
    else:
        selected_date = pd.Timestamp.today().normalize()

    formatted_date = selected_date

    # Get important date informations
    all_dates = dates_around(formatted_date)
    pending_dates = all_dates

    r = create_redis_connection()
    dfs = []
    
    cache_data, found_dates = fetch_cache(pending_dates, r)

    if found_dates:
        pending_dates = [date for date in pending_dates if date not in found_dates]

        cache_df = normalize_data(pd.DataFrame(cache_data))
        dfs.append(cache_df)

    if pending_dates:
        db_data = fetch_db(pending_dates)

        if not db_data:
            db_data = pd.DataFrame(columns=["timestamp", "temperature", "humidity"])

        db_df = normalize_data(pd.DataFrame(db_data))
        dfs.append(db_df)

        cache_db_data(db_df, pending_dates, r)  

    r.close()

    if dfs:
        df = pd.concat(dfs, ignore_index=True)
        df = normalize_data(df)
    else:
        df = normalize_data(
            pd.DataFrame(columns=["timestamp", "temperature", "humidity"])
        )

    result = df[
        df["timestamp"].dt.date == selected_date.date()
    ]

    stats = get_stats(df)
    
    dtt = {
        # all_dates = [prev2, prev, current, next, next2]
        "current": get_day_stats(stats, all_dates[2]),
        "prev": get_day_stats(stats, all_dates[1]),
        "prev2": get_day_stats(stats, all_dates[0]),
        "next": get_day_stats(stats, all_dates[3]),
        "next2": get_day_stats(stats, all_dates[4]),
        "chart_data": generate_chart(result)
    }

    dtt.update({'selected_date_position': 'middle'})

    if not dtt['next']['loaded']:
        dtt.update({'selected_date_position': 'right'})

    elif not dtt['prev']['loaded']:
        dtt.update({'selected_date_position': 'left'})

    return render_template(
        "index.html",
        data=(dtt)
    )

if __name__ == '__main__':
    print("Iniciando o servidor Flask...")
    app.run(host='0.0.0.0')
