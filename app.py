import pandas as pd
import datetime as dt
from flask import Flask, render_template, jsonify, request, send_file
import threading 
import json
import io
import math

app = Flask(__name__)

DATA_FILE = 'data.csv'
file_lock = threading.Lock()

def calculate_stats(series):
    if series.empty:
        return { "max": None, "min": None, "avg": None, "median": None, "std_dev": None }
    
    max_val = round(series.max(), 2)
    min_val = round(series.min(), 2)
    avg_val = round(series.mean(), 2)
    median_val = round(series.median(), 2)
    std_dev_val = round(series.std(), 2)

    return {
        "max": max_val,
        "min": min_val,
        "avg": avg_val,
        "median": median_val,
        "std_dev": std_dev_val
    }

def get_processed_data(timeframe_hours='all', start_date=None, end_date=None, page=1, limit=100): 
    with file_lock:
        try:
            df = pd.read_csv(DATA_FILE) 
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
        except (FileNotFoundError, pd.errors.EmptyDataError):
            print("Arquivo data.csv não encontrado ou vazio.")
            empty_stats = calculate_stats(pd.Series(dtype=float))
            return { 
                "data": [], 
                "timeframe_hours": timeframe_hours, 
                "temperature_infos": empty_stats, 
                "humidity_infos": empty_stats,
                "pagination": { "page": 1, "limit": limit, "total_pages": 1, "total_records": 0 }
            }
        except Exception as e:
            print(f"Erro ao ler o CSV: {e}")
            empty_stats = calculate_stats(pd.Series(dtype=float))
            return { 
                "data": [], 
                "timeframe_hours": timeframe_hours, 
                "temperature_infos": empty_stats, 
                "humidity_infos": empty_stats,
                "pagination": { "page": 1, "limit": limit, "total_pages": 1, "total_records": 0 }
            }

    if start_date and end_date:
        try:
            s_date = pd.to_datetime(start_date)
            e_date = pd.to_datetime(end_date)
            filtered_df = df[(df['timestamp'] >= s_date) & (df['timestamp'] <= e_date)].copy()
        except Exception as e:
            print(f"Erro ao converter datas: {e}")
            filtered_df = df.copy()
    else:
        cutoff_time = dt.datetime.now() - dt.timedelta(hours=timeframe_hours) if timeframe_hours != 'all' else df['timestamp'].min()
        filtered_df = df[df['timestamp'] >= cutoff_time].copy()

    temperature_stats = calculate_stats(filtered_df['temperature'])
    humidity_stats = calculate_stats(filtered_df['humidity'])
    
    total_records = len(filtered_df)
    total_pages = math.ceil(total_records / limit)
    
    if page < 1: page = 1
    if page > total_pages and total_pages > 0: page = total_pages
    
    start_index = (page - 1) * limit
    end_index = start_index + limit
    
    paginated_df = filtered_df.iloc[start_index:end_index].copy()

    data_list = []
    if not paginated_df.empty:
        paginated_df['timestamp'] = paginated_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        data_list = paginated_df.to_dict('records')

    final_data = {
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
    
    return final_data

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

    timeframe_hours = 'all'
    
    if not start_date and not end_date:
        if filter_arg != 'all':
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

@app.route("/json/all")
def api_all_data():
    processed_data = get_processed_data(timeframe_hours='all', limit=1000000)
    return jsonify(processed_data)

@app.route("/json/export")
def api_export_data():
    processed_data = get_processed_data(timeframe_hours='all', limit=1000000)
    try:
        json_data = json.dumps(processed_data, indent=4)
        buffer = io.BytesIO()
        buffer.write(json_data.encode('utf-8'))
        buffer.seek(0) 
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name='export_data.json',
            mimetype='application/json'
        )
        
    except Exception as e:
        print(f"Erro ao exportar JSON: {e}")
        return jsonify({"status": "error", "message": "Falha ao exportar arquivo JSON"}), 500

if __name__ == '__main__':
    print("Iniciando o servidor Flask...")
    app.run(host='0.0.0.0')