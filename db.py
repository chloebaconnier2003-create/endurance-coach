import sqlite3
from pathlib import Path
DB=Path(__file__).with_name('coach_v2.db')
SCHEMA="""
CREATE TABLE IF NOT EXISTS goals (id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,event_date TEXT,sport TEXT,kind TEXT,priority TEXT,status TEXT DEFAULT 'planned',notes TEXT);
CREATE TABLE IF NOT EXISTS shifts (id INTEGER PRIMARY KEY AUTOINCREMENT,start_at TEXT NOT NULL,end_at TEXT NOT NULL,shift_type TEXT NOT NULL,notes TEXT);
CREATE TABLE IF NOT EXISTS sessions (id INTEGER PRIMARY KEY AUTOINCREMENT,start_at TEXT NOT NULL,sport TEXT NOT NULL,title TEXT NOT NULL,duration_min INTEGER,priority TEXT,intensity TEXT,objective TEXT,status TEXT DEFAULT 'planned',source TEXT DEFAULT 'manual');
CREATE TABLE IF NOT EXISTS activities (id INTEGER PRIMARY KEY AUTOINCREMENT,start_at TEXT NOT NULL,sport TEXT NOT NULL,title TEXT,duration_min INTEGER,distance_km REAL,elevation_m REAL,rpe REAL,pain REAL,notes TEXT);
CREATE TABLE IF NOT EXISTS checkins (id INTEGER PRIMARY KEY AUTOINCREMENT,created_at TEXT NOT NULL,sleep_hours REAL,sleep_quality INTEGER,fatigue INTEGER,motivation INTEGER,soreness INTEGER,stress INTEGER,pain_location TEXT,pain_score REAL,pain_trend TEXT,notes TEXT);
CREATE TABLE IF NOT EXISTS constraints (id INTEGER PRIMARY KEY AUTOINCREMENT,event_date TEXT NOT NULL,event_type TEXT NOT NULL,title TEXT NOT NULL,duration_min INTEGER DEFAULT 60,intensity TEXT DEFAULT 'moderate',fixed INTEGER DEFAULT 1,notes TEXT);
CREATE TABLE IF NOT EXISTS recurring_rules (id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT NOT NULL,event_type TEXT NOT NULL,weekday INTEGER NOT NULL,start_time TEXT NOT NULL,duration_min INTEGER DEFAULT 90,intensity TEXT DEFAULT 'moderate',start_date TEXT NOT NULL,end_date TEXT,active INTEGER DEFAULT 1,notes TEXT);
CREATE TABLE IF NOT EXISTS recurring_exceptions (id INTEGER PRIMARY KEY AUTOINCREMENT,rule_id INTEGER NOT NULL,original_date TEXT NOT NULL,action TEXT NOT NULL,new_start_at TEXT,new_end_at TEXT,UNIQUE(rule_id,original_date));
CREATE TABLE IF NOT EXISTS work_cycles (id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT NOT NULL,anchor_date TEXT NOT NULL,cycle_days INTEGER DEFAULT 4,active INTEGER DEFAULT 1,notes TEXT);
CREATE TABLE IF NOT EXISTS work_cycle_exceptions (id INTEGER PRIMARY KEY AUTOINCREMENT,cycle_id INTEGER NOT NULL,original_date TEXT NOT NULL,action TEXT NOT NULL,new_start_at TEXT,new_end_at TEXT,notes TEXT,UNIQUE(cycle_id,original_date));
CREATE TABLE IF NOT EXISTS plan_log (id INTEGER PRIMARY KEY AUTOINCREMENT,created_at TEXT NOT NULL,goal_name TEXT,summary TEXT);
"""
def connect():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def _columns(c,t):
 try:return {r[1] for r in c.execute(f'PRAGMA table_info({t})').fetchall()}
 except sqlite3.Error:return set()
def _add(c,t,n,d):
 if n not in _columns(c,t): c.execute(f'ALTER TABLE {t} ADD COLUMN {n} {d}')
def migrate(c):
 c.executescript(SCHEMA)
 for n,d in [('title',"TEXT NOT NULL DEFAULT 'Cycle 24/72'"),('anchor_date',"TEXT NOT NULL DEFAULT '2026-01-01'"),('cycle_days','INTEGER DEFAULT 4'),('active','INTEGER DEFAULT 1'),('notes','TEXT')]:_add(c,'work_cycles',n,d)
 for n,d in [('cycle_id','INTEGER'),('original_date','TEXT'),('action',"TEXT DEFAULT 'delete'"),('new_start_at','TEXT'),('new_end_at','TEXT'),('notes','TEXT')]:_add(c,'work_cycle_exceptions',n,d)
 for n,d in [('title',"TEXT NOT NULL DEFAULT 'Récurrence'"),('event_type',"TEXT NOT NULL DEFAULT 'other'"),('weekday','INTEGER DEFAULT 0'),('start_time',"TEXT DEFAULT '19:00'"),('duration_min','INTEGER DEFAULT 90'),('intensity',"TEXT DEFAULT 'moderate'"),('start_date',"TEXT DEFAULT '2026-01-01'"),('end_date','TEXT'),('active','INTEGER DEFAULT 1'),('notes','TEXT')]:_add(c,'recurring_rules',n,d)
 # V5: persistent databases can already contain an older recurring_exceptions table.
 # CREATE TABLE IF NOT EXISTS does not upgrade it, so add every V5 field explicitly.
 for n,d in [('rule_id','INTEGER'),('original_date','TEXT'),('action',"TEXT DEFAULT 'delete'"),('new_start_at','TEXT'),('new_end_at','TEXT')]:_add(c,'recurring_exceptions',n,d)
 c.commit()
def init():
 c=connect(); migrate(c); c.close()
def query(sql,args=()):
 c=connect(); migrate(c); out=[dict(x) for x in c.execute(sql,args).fetchall()]; c.close(); return out
def execute(sql,args=()):
 c=connect(); migrate(c); c.execute(sql,args); c.commit(); c.close()
