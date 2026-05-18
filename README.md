# Temperature and Humidity Dashboard

### A Flask-based dashboard for monitoring and analyzing temperature and humidity data stored in a PostgreSQL database.
- Flask
- Jinja Templates
- PostgreSQL
- psycopg2
- Pandas
---

## ENV
- `PGUSER` - PostgreSQL User
- `PGPASS` - PostgreSQL Password
- `PGHOST` - PostgreSQL Host
- `PGDB` - PostgreSQL Database

## Project Structure
```
dashboard/
├── app.py
├── templates/
│   └── index.html
├── static/
│   └── styles.css
├── requirements.txt
├── .gitignore 
└── .env
```
---
This repository has a [monitor](https://github.com/CristianMB2255/esp32-monitor), acess to see the full data processing pipeline.