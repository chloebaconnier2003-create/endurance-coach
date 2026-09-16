from datetime import date,datetime,timedelta,time
from db import query,execute
from calendar_engine import recurring_instances,all_shifts

# Conservative evidence-informed scheduler: low intensity dominates; hard/easy spacing;
# running exposure progresses by phase and availability, while rugby counts as hard load.
PHASES=[
 ('2026-09-16','2026-10-18','semi',3,4),('2026-10-19','2026-11-28','trail',3,3),
 ('2026-11-29','2027-01-03','reset',3,4),('2027-01-04','2027-02-28','base_run',4,4),
 ('2027-03-01','2027-04-25','marathon',4,4),('2027-04-26','2027-05-23','ventoux',2,3),
 ('2027-05-24','2027-06-27','half',3,3),('2027-06-28','2027-07-25','cinglée',2,3),
 ('2027-07-26','2027-08-15','colombier',2,3),('2027-08-16','2027-09-05','full',3,3),
 ('2027-09-06','2027-09-30','taper',3,3)]

def phase_for(d):
 s=d.isoformat()
 for a,b,p,r,_ in PHASES:
  if a<=s<=b:return p,r
 return 'base_run',3

def _shifts(start,end):
 manual=query('SELECT * FROM shifts WHERE date(start_at)<=? AND date(end_at)>=?',(end.isoformat(),(start-timedelta(days=1)).isoformat()))
 return all_shifts(manual,query('SELECT * FROM work_cycles WHERE active=1'),start,end,query('SELECT * FROM work_cycle_exceptions'))

def _fixed(start,end):
 shifts=_shifts(start,end); rec,_=recurring_instances(query('SELECT * FROM recurring_rules WHERE active=1'),shifts,start,end)
 out=[]
 for x in shifts:out.append((datetime.fromisoformat(x['start_at']),datetime.fromisoformat(x['end_at']),x['shift_type']))
 for x in rec:out.append((x['start_at'],x['end_at'],x['event_type']))
 for x in query('SELECT * FROM constraints WHERE event_date>=? AND event_date<=?',(start.isoformat(),end.isoformat())):
  t=datetime.combine(date.fromisoformat(x['event_date']),time(18));out.append((t,t+timedelta(minutes=x.get('duration_min') or 90),x['event_type']))
 return out

def _day_flags(start,end):
 fixed=_fixed(start,end);flags={start+timedelta(days=i):{'blocked':False,'hard':False,'rugby':False,'night':False,'shift24':False} for i in range((end-start).days+1)}
 for a,b,k in fixed:
  d=a.date()
  if d not in flags:continue
  if k in ('24h','12h_jour','12h_nuit'):flags[d]['blocked']=True
  if k=='24h':flags[d]['shift24']=True
  if k=='12h_nuit':flags[d]['night']=True
  if k in ('rugby','rugby_training','rugby_match'):
   flags[d]['hard']=True;flags[d]['rugby']=True
  if k=='rugby_match':flags[d]['hard']=True
 # mandatory post-shift protection: 24 h after 24 h; 12 h after 12 h.
 for a,b,k in fixed:
  if k=='24h':
   d=b.date();
   if d in flags:flags[d]['blocked']=True
  elif k in ('12h_jour','12h_nuit'):
   d=b.date();
   if d in flags and b.hour>=8:flags[d]['blocked']=True
 return flags

def _week_index(d,phase):
 starts={'semi':'2026-09-16','trail':'2026-10-19','reset':'2026-11-29','base_run':'2027-01-04','marathon':'2027-03-01','ventoux':'2027-04-26','half':'2027-05-24','cinglée':'2027-06-28','colombier':'2027-07-26','full':'2027-08-16','taper':'2027-09-06'}
 return max(0,(d-date.fromisoformat(starts[phase])).days//7)

def prescription(phase,w):
 # durations are targets; generator adapts placement, not physiology after the fact.
 if phase=='reset':
  long=min(80,60+5*w);return [('running','Footing facile',45,'easy','Endurance fondamentale'),('running','Footing + lignes droites',45,'easy','Économie de course'),('running','Sortie longue facile',long,'easy','Tolérance mécanique'),('swimming','Natation technique',45,'easy','Technique'),('swimming','Natation endurance',50,'easy','Aérobie sans impact'),('cycling','Vélo Z2',75,'easy','Base aérobie'),('strength','Renforcement',40,'moderate','Force générale')]
 if phase=='base_run':
  long=min(120,80+5*w);q='Tempo contrôlé 3×8 min' if w<4 else 'Allure marathon 3×10 min';return [('running','Footing facile',45,'easy','Endurance fondamentale'),('running',q,60,'moderate','Seuil bas / économie'),('running','Footing facile + strides',45,'easy','Fréquence CAP'),('running','Sortie longue',long,'easy','Durabilité CAP'),('swimming','Natation technique',50,'easy','Technique'),('swimming','Natation endurance',55,'easy','Aérobie'),('cycling','Vélo Z2',90,'easy','Entretien vélo'),('strength','Renforcement coureur',40,'moderate','Force')]
 if phase=='marathon':
  longs=[100,115,130,95,145,160,120,45];long=longs[min(w,len(longs)-1)];q=['3×10 min allure marathon','2×15 min allure marathon','3×12 min allure marathon','6×3 min tempo','2×20 min allure marathon','3×15 min allure marathon','2×12 min allure marathon','Activation marathon'][min(w,7)];return [('running','Footing récupération',40,'easy','Récupération active'),('running',q,60,'moderate','Spécifique marathon'),('running','Footing facile + strides',45,'easy','Économie'),('running','Sortie longue',long,'easy','Durabilité / nutrition'),('swimming','Natation récupération',45,'easy','Aérobie sans impact'),('cycling','Vélo facile',60,'easy','Entretien aérobie'),('strength','Renforcement entretien',30,'moderate','Force')]
 if phase in ('ventoux','cinglée','colombier'):
  long={'ventoux':180,'cinglée':300,'colombier':300}[phase];return [('cycling','Vélo endurance montagne',long,'easy','Endurance / D+ / nutrition'),('cycling','Vélo force-endurance',90,'moderate','Montées contrôlées'),('running','Footing facile',45,'easy','Maintien CAP'),('running','Course facile + strides',45,'easy','Économie'),('swimming','Natation technique',50,'easy','Technique/récupération'),('swimming','Natation endurance',55,'easy','Aérobie'),('strength','Renforcement entretien',30,'moderate','Force')]
 if phase in ('half','full'):
  long=210 if phase=='half' else 300;runlong=85 if phase=='half' else 100;return [('cycling','Vélo long Z2 + nutrition',long,'easy','Durabilité'),('running','Brick facile',30 if phase=='half' else 45,'easy','Transition vélo-course'),('running','Sortie longue facile',runlong,'easy','Durabilité CAP'),('running','Tempo contrôlé',55,'moderate','Seuil bas'),('swimming','Natation technique',50,'easy','Technique'),('swimming','Natation endurance/CSS',65,'moderate','Endurance spécifique'),('cycling','Vélo endurance',90,'easy','Volume'),('strength','Renforcement entretien',30,'moderate','Force')]
 if phase=='taper':return [('swimming','Natation technique',45,'easy','Fraîcheur'),('cycling','Vélo Z2 + rappels',90,'moderate','Spécificité'),('running','Footing + rappels',45,'moderate','Spécificité'),('running','Course facile',35,'easy','Fréquence')]
 if phase=='trail':return [('trail','Trail vallonné facile',60,'easy','Technique'),('trail','Côtes contrôlées',55,'moderate','Force-endurance'),('trail','Sortie trail longue',105,'easy','Durabilité'),('strength','Renforcement trail',40,'moderate','Excentrique'),('swimming','Natation récupération',45,'easy','Récupération')]
 return [('running','Footing facile',45,'easy','Endurance'),('running','Séance spécifique',60,'moderate','Spécifique'),('running','Sortie longue',100,'easy','Durabilité'),('swimming','Natation récupération',45,'easy','Technique'),('strength','Renforcement',35,'moderate','Force')]

def _score_day(d,flags,intensity,sport,last_hard):
 f=flags[d];score=0
 if f['blocked']:score-=100
 if intensity!='easy' and f['hard']:score-=100
 if intensity!='easy' and last_hard and abs((d-last_hard).days)<2:score-=60
 # prefer quality on rested midweek days, long sessions on weekends when possible
 if sport in ('cycling','trail') and d.weekday()>=5:score+=12
 if 'running'==sport and d.weekday() in (1,3,6):score+=6
 if f['rugby']:score-=30
 return score

def generate_week(start,replace=False):
 start=start-timedelta(days=start.weekday());end=start+timedelta(days=6);phase,_=phase_for(start);w=_week_index(start,phase);flags=_day_flags(start,end)
 if replace:execute("DELETE FROM sessions WHERE date(start_at)>=? AND date(start_at)<=? AND source='weekly_generator'",(start.isoformat(),end.isoformat()))
 elif query("SELECT id FROM sessions WHERE date(start_at)>=? AND date(start_at)<=? AND source='weekly_generator' LIMIT 1",(start.isoformat(),end.isoformat())):return {'created':0,'phase':phase,'message':'Semaine déjà générée'}
 plan=prescription(phase,w);created=[];last_hard=None;used={}
 for sport,title,dur,intensity,obj in sorted(plan,key=lambda x:(x[3]=='easy',-x[2])):
  candidates=[]
  for i in range(7):
   d=start+timedelta(days=i)
   if used.get(d,0)>=2:continue
   sc=_score_day(d,flags,intensity,sport,last_hard)
   if dur>120 and flags[d]['blocked']:sc-=100
   candidates.append((sc,d))
  if not candidates:continue
  sc,d=max(candidates,key=lambda x:x[0])
  if sc<=-90:continue
  # default training slot; later UI can allow drag/drop. Two-a-days separated.
  hour=10 if used.get(d,0)==0 else 17
  start_at=datetime.combine(d,time(hour,0)).isoformat(timespec='minutes')
  execute('INSERT INTO sessions(start_at,sport,title,duration_min,priority,intensity,objective,status,source) VALUES(?,?,?,?,?,?,?,?,?)',(start_at,sport,title,dur,'A' if dur>=90 or intensity!='easy' else 'B',intensity,obj,'planned','weekly_generator'))
  used[d]=used.get(d,0)+1;created.append((d,title))
  if intensity!='easy':last_hard=d
 return {'created':len(created),'phase':phase,'message':f'{len(created)} séances générées'}

def generate_until(end_date=date(2027,9,30),replace=False):
 d=date.today()-timedelta(days=date.today().weekday());total=0;weeks=0
 while d<=end_date:
  r=generate_week(d,replace=replace);total+=r['created'];weeks+=1;d+=timedelta(days=7)
 return {'weeks':weeks,'created':total}
