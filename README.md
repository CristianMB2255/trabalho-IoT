# Temperature and Humidity Dashboard

### A Flask-based dashboard for monitoring and analyzing temperature and humidity data stored in a PostgreSQL database.

This project uses PostgreSQL database connection to gather the stored information and caches it using Redis. The data is processed with pandas and sent to the front-end with Flask and rendered using Jinja templates.

### Technologies used:
- Flask
- Jinja Templates
- PostgreSQL
- psycopg2
- Pandas
- Redis
---

## ENV
- `PGUSER` - PostgreSQL User
- `PGPASS` - PostgreSQL Password
- `PGHOST` - PostgreSQL Host
- `PGDB` - PostgreSQL Database
- `RHOST` - Redis Host
- `RPORT` - Redis Port
- `RUSER` - Redis User
- `RPASS` - Redis Password

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