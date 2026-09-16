import streamlit as st
import pandas as pd
from datetime import datetime,date,time,timedelta
from db import init,query,execute
from profile import ATHLETE,GOALS
from engine import decision
from calendar_engine import recurring_instances,all_shifts
from calendar_views import month_view,week_view
from workout_engine import detailed_workout
from performance_engine import load_summary
from coach_engine import coach_brief,adaptation_options
from v7_pages import week_page,roadmap_page,goals_page,tests_page,records_page,road_page,stats_page,rugby_matches_page
st.set_page_config(page_title='Endurance Coach V7',page_icon='⚡',layout='wide',initial_sidebar_state='collapsed');init()
if not query('SELECT id FROM goals LIMIT 1'):
 for g in GOALS:execute('INSERT INTO goals(name,event_date,sport,kind,priority,notes) VALUES(?,?,?,?,?,?)',g)
st.markdown('''<style>.block-container{max-width:1100px;padding-top:.65rem;padding-bottom:6rem}.hero{padding:1rem;border-radius:20px;background:linear-gradient(135deg,#14171c,#29323d);color:white}.card{padding:1rem;border:1px solid rgba(128,128,128,.22);border-radius:18px;margin:.5rem 0}.stButton button{min-height:46px;border-radius:14px;font-weight:650;white-space:normal}@media(max-width:700px){.block-container{padding-left:.6rem!important;padding-right:.6rem!important}.hero h2{font-size:1.3rem!important}div[data-testid="stHorizontalBlock"]{gap:.3rem}.stButton button{min-height:50px}}</style>''',unsafe_allow_html=True)
def one(sql,args=()):
 r=query(sql,args);return r[0] if r else None
def next_goal():return one("SELECT * FROM goals WHERE COALESCE(event_date,'')!='' AND event_date>=? ORDER BY event_date LIMIT 1",(date.today().isoformat(),))
def checkin():return one('SELECT * FROM checkins WHERE date(created_at)=? ORDER BY created_at DESC LIMIT 1',(date.today().isoformat(),))
def today_session():return one("SELECT * FROM sessions WHERE date(start_at)=? AND status='planned' ORDER BY start_at LIMIT 1",(date.today().isoformat(),))
def ico(s):return {'running':'🏃','trail':'⛰️','cycling':'🚴','swimming':'🏊','rugby':'🏉','rugby_training':'🏉','rugby_match':'🏉','dance':'💃','strength':'💪'}.get(str(s or '').lower(),'📌')
def shifts_between(start,end):
 manual=query('SELECT * FROM shifts WHERE date(start_at)<=? AND date(end_at)>=?',(end.isoformat(),(start-timedelta(days=1)).isoformat()));return all_shifts(manual,query('SELECT * FROM work_cycles WHERE active=1'),start,end,query('SELECT * FROM work_cycle_exceptions'))
def last_shift():
 past=[]
 for x in shifts_between(date.today()-timedelta(days=3),date.today()):
  try:
   e=datetime.fromisoformat(x['end_at']);
   if e<=datetime.now():past.append((e,x))
  except:pass
 if not past:return None
 e,x=max(past,key=lambda z:z[0]);x=dict(x);x['hours_since']=(datetime.now()-e).total_seconds()/3600;return x
def rugby_recent():return bool(query("SELECT id FROM activities WHERE sport='rugby' AND start_at>=? LIMIT 1",((datetime.now()-timedelta(hours=36)).isoformat(timespec='minutes'),)))
def events_between(start,end):
 events=[];ss=shifts_between(start,end);rec,_=recurring_instances(query('SELECT * FROM recurring_rules WHERE active=1'),ss,start,end);rex={(x['rule_id'],x['original_date']):x for x in query('SELECT * FROM recurring_exceptions')}
 labels={'24h':'Garde 24 h','12h_jour':'Garde 12 h jour','12h_nuit':'Garde 12 h nuit','formation':'Formation','sst':'SST'}
 for x in ss:events.append({'date':date.fromisoformat(x['start_at'][:10]),'time':x['start_at'][11:16],'icon':'🚑','title':labels.get(x['shift_type'],x['shift_type']),'meta':'travail','kind':'shift','id':x.get('id'),'uid':'w'+str(x.get('id') or x.get('original_date'))})
 for x in rec:
  original=x['date'].isoformat();ex=rex.get((x['rule_id'],original))
  if ex and ex['action']=='delete':continue
  events.append({'date':x['date'],'time':x['start_at'].strftime('%H:%M'),'icon':ico(x['event_type']),'title':x['title'],'meta':'récurrent','kind':'recurring','rule_id':x['rule_id'],'original_date':original,'uid':f"r{x['rule_id']}_{original}"})
 for x in query("SELECT * FROM sessions WHERE date(start_at)>=? AND date(start_at)<=? AND status!='cancelled'",(start.isoformat(),end.isoformat())):events.append({'date':date.fromisoformat(x['start_at'][:10]),'time':x['start_at'][11:16],'icon':ico(x['sport']),'title':x['title'],'meta':f"{x['duration_min'] or '?'} min",'kind':'session','id':x['id'],'sport':x['sport'],'duration_min':x['duration_min'],'intensity':x['intensity'],'objective':x['objective'],'start_at':x['start_at'],'uid':'s'+str(x['id'])})
 for x in query("SELECT * FROM constraints WHERE event_date>=? AND event_date<=?",(start.isoformat(),end.isoformat())):events.append({'date':date.fromisoformat(x['event_date']),'icon':ico(x['event_type']),'title':x['title'],'meta':'contrainte','kind':'constraint','id':x['id'],'uid':'c'+str(x['id'])})
 for x in query("SELECT * FROM goals WHERE event_date>=? AND event_date<=?",(start.isoformat(),end.isoformat())):events.append({'date':date.fromisoformat(x['event_date']),'icon':'🏁','title':x['name'],'meta':'objectif','kind':'goal','id':x['id'],'uid':'g'+str(x['id'])})
 return events
def session_detail(e):
 st.subheader(f"{e.get('icon','')} {e['title']}");st.caption(f"{e['date'].strftime('%d/%m/%Y')} · {e.get('time','')}")
 if e['kind']=='session':
  w=detailed_workout(e.get('sport'),e.get('intensity'),e.get('duration_min'),e.get('objective'));st.write('**Échauffement** — '+w['warmup']);st.write('**Bloc principal** — '+w['main']);st.write('**Retour au calme** — '+w['cooldown']);st.write('**Cible** — '+w['intensity_target'])
  with st.expander('Marquer réalisée / modifier'):
   dur=st.number_input('Durée réelle',1,1000,int(e.get('duration_min') or 60));dist=st.number_input('Distance réelle km',0.,500.,0.,.1);elev=st.number_input('D+ réel',0,10000,0);rpe=st.slider('RPE',1,10,4);pain=st.slider('Douleur',0,10,0);feel=st.text_input('Ressenti')
   if st.button('✓ Séance réalisée',use_container_width=True):execute("UPDATE sessions SET status='completed',actual_duration_min=?,actual_distance_km=?,actual_elevation_m=?,actual_rpe=?,actual_pain=?,actual_feeling=?,completed_at=? WHERE id=?",(dur,dist,elev,rpe,pain,feel,datetime.now().isoformat(),e['id']));execute('INSERT INTO activities(start_at,sport,title,duration_min,distance_km,elevation_m,rpe,pain,notes) VALUES(?,?,?,?,?,?,?,?,?)',(datetime.now().isoformat(),e['sport'],e['title'],dur,dist,elev,rpe,pain,feel));st.rerun()
g=next_goal();days=(date.fromisoformat(g['event_date'])-date.today()).days if g else None
st.markdown(f"<div class='hero'><small>ENDURANCE COACH · V7</small><h2>{g['name'] if g else 'Road to Full Distance'}</h2><b>{'J-'+str(days) if days is not None else ''}</b><br><small>Planifier · réaliser · mesurer · adapter</small></div>",unsafe_allow_html=True)
nav=st.segmented_control('Navigation',['🏠 Aujourd’hui','📊 Semaine','📅 Planning','📈 Progression','••• Plus'],default='🏠 Aujourd’hui',label_visibility='collapsed') or '🏠 Aujourd’hui'
if nav=='🏠 Aujourd’hui':
 ci=checkin();ps=today_session();dec,score,status,why,action=decision(ci,ps,last_shift(),rugby_recent());loads=load_summary(query('SELECT * FROM activities WHERE start_at>=?',((date.today()-timedelta(days=28)).isoformat(),)));a,b,c=st.columns(3);a.metric('Forme',score);b.metric('Charge 7 j',loads['load7']);c.metric('Objectif',f'J-{days}' if days is not None else '—');st.markdown(f"### {status.replace('_',' ')} · {dec.replace('_',' ').title()}");st.write(why)
 if ps:
  w=detailed_workout(ps['sport'],ps['intensity'],ps['duration_min'],ps['objective']);st.markdown(f"<div class='card'><small>SÉANCE DU JOUR</small><h2>{ico(ps['sport'])} {ps['title']}</h2><b>{ps['duration_min']} min · {ps['intensity']}</b><p>{w['summary']}</p></div>",unsafe_allow_html=True)
  e={'kind':'session','id':ps['id'],'sport':ps['sport'],'title':ps['title'],'date':date.today(),'time':ps['start_at'][11:16],'duration_min':ps['duration_min'],'intensity':ps['intensity'],'objective':ps['objective'],'icon':ico(ps['sport'])};session_detail(e)
 for msg in coach_brief(score,status,ps,g,last_shift(),loads):st.write('• '+msg)
 if not ci:
  with st.expander('☀️ Check-in du jour'):
   with st.form('check'):
    sleep=st.number_input('Sommeil',0.,14.,7.,.5);fatigue=st.slider('Fatigue',1,5,3);quality=st.slider('Qualité',1,5,3);motivation=st.slider('Motivation',1,5,3);soreness=st.slider('Courbatures',1,5,3);stress=st.slider('Stress',1,5,3);pain=st.slider('Douleur',0,10,0)
    if st.form_submit_button('Enregistrer'):execute('INSERT INTO checkins(created_at,sleep_hours,sleep_quality,fatigue,motivation,soreness,stress,pain_score) VALUES(?,?,?,?,?,?,?,?)',(datetime.now().isoformat(),sleep,quality,fatigue,motivation,soreness,stress,pain));st.rerun()
elif nav=='📊 Semaine':week_page()
elif nav=='📅 Planning':
 st.header('Planning');view=st.segmented_control('Vue',['Jour / Mois','Semaine'],default='Jour / Mois')
 if view=='Jour / Mois':
  d=st.date_input('Mois',date.today());start=date(d.year,d.month,1);end=(date(d.year+1,1,1)-timedelta(days=1)) if d.month==12 else date(d.year,d.month+1,1)-timedelta(days=1);selected=month_view(d.year,d.month,events_between(start,end))
 else:
  d=st.date_input('Semaine',date.today());start=d-timedelta(days=d.weekday());selected=week_view(start,events_between(start,start+timedelta(days=6)))
 if selected:session_detail(selected)
elif nav=='📈 Progression':stats_page()
else:
 choice=st.selectbox('Espace',['🗺️ Plan prévisionnel','🏁 Objectifs','🏉 Matchs rugby','🧪 Tests physiques','🏅 Records','🎯 Road to LéMan','🤖 Coach','👤 Profil'])
 if choice=='🗺️ Plan prévisionnel':roadmap_page()
 elif choice=='🏁 Objectifs':goals_page()
 elif choice=='🏉 Matchs rugby':rugby_matches_page()
 elif choice=='🧪 Tests physiques':tests_page()
 elif choice=='🏅 Records':records_page()
 elif choice=='🎯 Road to LéMan':road_page()
 elif choice=='🤖 Coach':
  ci=checkin();ps=today_session();dec,score,status,why,action=decision(ci,ps,last_shift(),rugby_recent());st.header('Coach adaptatif');st.success(action);st.write(why)
  if ps:
   for x in adaptation_options(ps,why):st.write('→ '+x)
 else:
  st.header('Profil athlète')
  for sec,data in ATHLETE.items():
   with st.expander(sec):
    for k,v in data.items():st.write(f'**{k} :** {v}')
st.caption('Endurance Coach V7 · centre de pilotage sportif personnel')