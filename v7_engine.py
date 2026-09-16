from datetime import date,timedelta
from performance_engine import activity_load

def week_bounds(day=None):
 day=day or date.today(); start=day-timedelta(days=day.weekday()); return start,start+timedelta(days=6)

def week_summary(sessions,activities):
 planned=[s for s in sessions if s.get('status')!='cancelled']; done=[s for s in planned if s.get('status')=='completed' or s.get('completed_at')]
 pmin=sum(float(s.get('duration_min') or 0) for s in planned); amin=sum(float(s.get('actual_duration_min') or s.get('duration_min') or 0) for s in done)
 pdist=sum(float(s.get('distance_km') or 0) for s in planned); adist=sum(float(s.get('actual_distance_km') or 0) for s in done)
 activity_minutes=sum(float(a.get('duration_min') or 0) for a in activities)
 return {'planned_sessions':len(planned),'done_sessions':len(done),'session_pct':round(100*len(done)/len(planned)) if planned else 0,'planned_minutes':round(pmin),'done_minutes':round(amin),'minute_pct':round(100*amin/pmin) if pmin else 0,'planned_km':round(pdist,1),'done_km':round(adist,1),'activity_minutes':round(activity_minutes),'load':round(sum(activity_load(a) for a in activities))}

def roadmap():
 return [
 ('Spécifique semi','2026-09-01','2026-10-18','Course','Porto-Vecchio'),
 ('Transition trail','2026-10-19','2026-11-28','Trail / force','SaintéLyon'),
 ('Transition & technique','2026-11-29','2026-12-31','Récupération / natation','Reconstruction'),
 ('Base triathlon','2027-01-01','2027-02-28','Aérobie / technique / force','Base générale'),
 ('Spécifique marathon','2027-03-01','2027-04-30','Course longue / allure marathon','Marathon Aveiro'),
 ('Transition triathlon','2027-05-01','2027-05-16','Récupération / reprise vélo-natation','Transition'),
 ('Spécifique Half','2027-05-17','2027-06-30','Vélo / brick / eau libre','Half Annecy'),
 ('Construction Full','2027-07-01','2027-08-15','Volume / nutrition / longues sorties','LéMan Full'),
 ('Spécifique + taper','2027-08-16','2027-09-30','Spécifique course / fraîcheur','LéMan Full Distance')]

def seed_roadmap(execute,query):
 if query('SELECT id FROM training_blocks LIMIT 1'): return
 for name,start,end,focus,obj in roadmap(): execute('INSERT INTO training_blocks(name,start_date,end_date,focus,objective,status) VALUES(?,?,?,?,?,?)',(name,start,end,focus,obj,'planned'))

def test_catalog():
 return {'running':['5 km','10 km','VMA','Seuil','FC seuil','Allure critique','Terrain personnalisé'],'cycling':['FTP','20 min','FC seuil','Puissance critique','Test côte'],'swimming':['CSS','200 m','400 m','1000 m','1500 m'],'strength':['Tractions','Dips','Squat','Gainage','Personnalisé']}

def suggested_tests(existing):
 types={(x.get('sport'),x.get('test_type')) for x in existing}; out=[]
 if not any(s=='cycling' and t in ('FTP','20 min') for s,t in types):out.append('🚴 FTP vélo à établir')
 if not any(s=='swimming' and t=='CSS' for s,t in types):out.append('🏊 CSS natation à établir')
 if not any(s=='running' and t in ('5 km','Seuil','Allure critique') for s,t in types):out.append('🏃 Zones CAP à actualiser')
 return out
