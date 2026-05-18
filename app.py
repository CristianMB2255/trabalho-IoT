import pandas as pd
import datetime as dt
from flask import Flask, render_template, request
import math
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = Flask(__name__)

pg_user = os.getenv("PGUSER")
pg_password = os.getenv("PGPASS")
pg_host = os.getenv("PGHOST")
pg_db = os.getenv("PGDB")

def get_db_connection():
    """Create database connection with PostgreSQL."""
    return psycopg2.connect(
                user=pg_user,
                password=pg_password,
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

def get_processed_data(timeframe_hours='all', start_date=None, end_date=None, page=1, limit=50): 
    """Get data and important infos, return as object."""
    try:
        connection = get_db_connection()

        # Faz as consultas retornarem dicts
        cursor = connection.cursor(cursor_factory=RealDictCursor)

        # Consulta base sem parâmetros
        params = []
        query = "SELECT timestamp, temperature, humidity FROM data"

        if start_date and end_date:
            query += " WHERE timestamp BETWEEN %s AND %s"
            params.extend([start_date, end_date])

        elif timeframe_hours != 'all':
            cutoff_time = dt.datetime.now() - dt.timedelta(hours=float(timeframe_hours))

            query += " WHERE timestamp >= %s"
            params.append(cutoff_time)

        query += " ORDER BY timestamp DESC"

        cursor.execute(query, params)

        rows = cursor.fetchall()

        cursor.close()
        connection.close()

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

        temperature_stats = calculate_stats(df['temperature'])
        humidity_stats = calculate_stats(df['humidity'])

        # TODO: cache total length for query optimization 
        total_records = len(df)
        total_pages = math.ceil(total_records / limit)

        if page < 1:
            page = 1

        if page > total_pages and total_pages > 1:
            page = total_pages

        start_index = (page - 1) * limit
        end_index = start_index + limit

        paginated_df = df.iloc[end_index:start_index:-1].copy()

        paginated_df['timestamp'] = paginated_df['timestamp'].dt.strftime(
            '%Y-%m-%d %H:%M'
        )

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

    except Exception as e:
        print(f"Erro ao buscar dados do PostgreSQL: {e}")

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

@app.route("/")
def index():
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