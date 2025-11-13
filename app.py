import pandas as pd
import datetime as dt
from flask import Flask, render_template, jsonify, request, send_file
import threading 
import json
import io

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

def get_processed_data(timeframe_hours): 
    with file_lock:
        try:
            df = pd.read_csv(DATA_FILE) 
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
        except (FileNotFoundError, pd.errors.EmptyDataError):
            print("Arquivo data.csv não encontrado ou vazio. Aguardando dados...")
            empty_stats = calculate_stats(pd.Series(dtype=float))
            return { "data": [], "timeframe_hours": timeframe_hours, "temperature_infos": empty_stats, "humidity_infos": empty_stats }
        except Exception as e:
            print(f"Erro ao ler o CSV: {e}")
            empty_stats = calculate_stats(pd.Series(dtype=float))
            return { "data": [], "timeframe_hours": timeframe_hours, "temperature_infos": empty_stats, "humidity_infos": empty_stats }

    cutoff_time = dt.datetime.now() - dt.timedelta(hours=timeframe_hours) if timeframe_hours != 'all' else df['timestamp'].min()
    filtered_df = df[df['timestamp'] >= cutoff_time].copy()

    temperature_stats = calculate_stats(filtered_df['temperature'])
    humidity_stats = calculate_stats(filtered_df['humidity'])
    
    data_list = []
    if not filtered_df.empty:
        filtered_df['timestamp'] = filtered_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        data_list = filtered_df.to_dict('records')

    final_data = {
        "data": data_list,
        "timeframe_hours": timeframe_hours,
        "temperature_infos": temperature_stats,
        "humidity_infos": humidity_stats
    }
    
    return final_data

@app.route("/")
def index():
    filter_arg = request.args.get('filter', 'all')
    timeframe_hours = 'all'
    if filter_arg != 'all':
        try:
            timeframe_hours = float(filter_arg[:-1])
        except:
            timeframe_hours = 'all'
        
    data_to_render = get_processed_data(timeframe_hours=timeframe_hours)
    return render_template("index.html", data=data_to_render)

@app.route("/json/all")
def api_all_data():
    processed_data = get_processed_data(timeframe_hours='all')
    return jsonify(processed_data)

@app.route("/json/export")
def api_export_data():
    processed_data = processed_data = get_processed_data(timeframe_hours='all')
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