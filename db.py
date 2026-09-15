import sqlite3
from pathlib import Path

DB = Path(__file__).with_name("coach_v2.db")
SCHEMA = """
CREATE TABLE IF NOT EXISTS goals (id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,event_date TEXT,sport TEXT,kind TEXT,priority TEXT,status TEXT DEFAULT 'planned',notes TEXT);
CREATE TABLE IF NOT EXISTS shifts (id INTEGER PRIMARY KEY AUTOINCREMENT,start_at TEXT NOT NULL,end_at TEXT NOT NULL,shift_type TEXT NOT NULL,notes TEXT);
CREATE TABLE IF NOT EXISTS sessions (id INTEGER PRIMARY KEY AUTOINCREMENT,start_at TEXT NOT NULL,sport TEXT NOT NULL,title TEXT NOT NULL,duration_min INTEGER,priority TEXT,intensity TEXT,objective TEXT,status TEXT DEFAULT 'planned',source TEXT DEFAULT 'manual');
CREATE TABLE IF NOT EXISTS activities (id INTEGER PRIMARY KEY AUTOINCREMENT,start_at TEXT NOT NULL,sport TEXT NOT NULL,title TEXT,duration_min INTEGER,distance_km REAL,elevation_m REAL,rpe REAL,pain REAL,notes TEXT);
CREATE TABLE IF NOT EXISTS checkins (id INTEGER PRIMARY KEY AUTOINCREMENT,created_at TEXT NOT NULL,sleep_hours REAL,sleep_quality INTEGER,fatigue INTEGER,motivation INTEGER,soreness INTEGER,stress INTEGER,pain_location TEXT,pain_score REAL,pain_trend TEXT,notes TEXT);
CREATE TABLE IF NOT EXISTS constraints (id INTEGER PRIMARY KEY AUTOINCREMENT,event_date TEXT NOT NULL,event_type TEXT NOT NULL,title TEXT NOT NULL,duration_min INTEGER DEFAULT 60,intensity TEXT DEFAULT 'moderate',fixed INTEGER DEFAULT 1,notes TEXT);
CREATE TABLE IF NOT EXISTS recurring_rules (id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT NOT NULL,event_type TEXT NOT NULL,weekday INTEGER NOT NULL,start_time TEXT NOT NULL,duration_min INTEGER DEFAULT 90,intensity TEXT DEFAULT 'moderate',start_date TEXT NOT NULL,end_date TEXT,active INTEGER DEFAULT 1,notes TEXT);
CREATE TABLE IF NOT EXISTS work_cycles (id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT NOT NULL,anchor_date TEXT NOT NULL,cycle_days INTEGER DEFAULT 4,active INTEGER DEFAULT 1,notes TEXT);
CREATE TABLE IF NOT EXISTS work_cycle_exceptions (id INTEGER PRIMARY KEY AUTOINCREMENT,cycle_id INTEGER NOT NULL,original_date TEXT NOT NULL,action TEXT NOT NULL,new_start_at TEXT,new_end_at TEXT,notes TEXT,UNIQUE(cycle_id,original_date));
CREATE TABLE IF NOT EXISTS plan_log (id INTEGER PRIMARY KEY AUTOINCREMENT,created_at TEXT NOT NULL,goal_name TEXT,summary TEXT);
"""
def connect():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def init():
    c=connect(); c.executescript(SCHEMA); c.commit(); c.close()
def query(sql,args=()):
    c=connect(); out=[dict(x) for x in c.execute(sql,args).fetchall()]; c.close(); return out
def execute(sql,args=()):
    c=connect(); c.execute(sql,args); c.commit(); c.close()
