from db import connect, migrate

RACES=[("SaintéLyon relais","2026-11-28","trail"),("Marathon Aveiro","2027-04-25","running"),("Half Ironman Annecy","2027-06-20","triathlon"),("LéMan Full Distance","2027-09-12","triathlon")]
MATCHES=["2026-11-07","2026-11-15","2026-11-22","2026-12-06","2027-01-17","2027-01-31","2027-02-07","2027-03-07","2027-03-14","2027-03-21","2027-04-04","2027-04-18","2027-05-02","2027-05-16"]

def sync_confirmed_events():
    c=connect()
    try:
        migrate(c)
        for name,day,sport in RACES:
            row=c.execute("SELECT id FROM goals WHERE name=?",(name,)).fetchone()
            if row:
                c.execute("UPDATE goals SET event_date=?,sport=? WHERE id=?",(day,sport,row["id"]))
            else:
                c.execute("INSERT INTO goals(name,event_date,sport,kind,priority) VALUES(?,?,?,'competition','B')",(name,day,sport))
        for day in MATCHES:
            if not c.execute("SELECT 1 FROM constraints WHERE event_date=? AND event_type='rugby_match'",(day,)).fetchone():
                c.execute("INSERT INTO constraints(event_date,event_type,title,duration_min,intensity,fixed,notes) VALUES(?,'rugby_match','Match de rugby',120,'high',1,'Horaire à préciser')",(day,))
        for day,title in [("2026-10-18","Semi-marathon Porto-Vecchio"),("2026-11-28","SaintéLyon relais"),("2027-04-25","Marathon Aveiro"),("2027-06-20","Half Ironman Annecy"),("2027-09-12","LéMan Full Distance")]:
            if not c.execute("SELECT 1 FROM constraints WHERE event_date=? AND event_type='race'",(day,)).fetchone():
                c.execute("INSERT INTO constraints(event_date,event_type,title,duration_min,intensity,fixed,notes) VALUES(?,'race',?,1440,'high',1,'Journée de compétition bloquée')",(day,title))
        c.commit()
    finally:
        c.close()
