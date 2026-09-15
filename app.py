import streamlit as st
import pandas as pd
from datetime import datetime,date,timedelta
from db import init,query,execute
from profile import ATHLETE,GOALS
from engine import decision,srpe
from scheduler import build_plan
st.set_page_config(page_title='Endurance Coach',page_icon='⚡',layout='wide',initial_sidebar_state='collapsed'); init()
if not query('SELECT id FROM goals LIMIT 1'):
    for g in GOALS: execute('INSERT INTO goals(name,event_date,sport,kind,priority,notes) VALUES(?,?,?,?,?,?)',g)
st.markdown('''<style>.block-container{max-width:980px;padding-top:1rem;padding-bottom:5rem}.hero{padding:1.1rem 1.2rem;border-radius:22px;background:linear-gradient(135deg,#15171c,#252a33);color:white;margin-bottom:1rem}.eyebrow{font-size:.78rem;opacity:.7;text-transform:uppercase;letter-spacing:.08em}.card,.session{padding:1rem 1.1rem;border:1px solid rgba(128,128,128,.22);border-radius:20px;margin:.65rem 0}.bigscore{font-size:2.3rem;font-weight:750}.pill{display:inline-block;padding:.25rem .6rem;border-radius:999px;background:rgba(128,128,128,.15);font-size:.82rem;margin-right:.3rem}.stButton button{border-radius:14px;min-height:44px;font-weight:600}@media(max-width:640px){.block-container{padding-left:.75rem;padding-right:.75rem}}</style>''',unsafe_allow_html=True)
def checkin():
 r=query('SELECT * FROM checkins WHERE date(created_at)=? ORDER BY created_at DESC LIMIT 1',(date.today().isoformat(),)); return r[0] if r else None
def today_session():
 r=query("SELECT * FROM sessions WHERE date(start_at)=? AND status='planned' ORDER BY start_at LIMIT 1",(date.today().isoformat(),)); return r[0] if r else None
def last_shift():
 r=query('SELECT * FROM shifts WHERE end_at<=? ORDER BY end_at DESC LIMIT 1',(datetime.now().isoformat(timespec='minutes'),))
 if not r:return None
 x=r[0]; x['hours_since']=(datetime.now()-datetime.fromisoformat(x['end_at'])).total_seconds()/3600; return x
def rugby_recent():
 return bool(query("SELECT id FROM activities WHERE sport='rugby' AND start_at>=? LIMIT 1",((datetime.now()-timedelta(hours=36)).isoformat(timespec='minutes'),)))
def next_goal():
 r=query("SELECT * FROM goals WHERE event_date!='' AND event_date>=? ORDER BY event_date LIMIT 1",(date.today().isoformat(),)); return r[0] if r else None
def icon(s): return {'running':'🏃','trail':'⛰️','cycling':'🚴','swimming':'🏊','rugby':'🏉','dance':'💃','strength':'💪'}.get((s or '').lower(),'⚡')
def dlabel(x): return {'EXECUTE':'Séance maintenue','ADJUST':'Séance adaptée','MOVE':'Séance déplacée','REPLACE':'Séance remplacée','RECOVERY':'Récupération','MEDICAL_FLAG':'Vigilance douleur'}.get(x,x)
g=next_goal(); days=(date.fromisoformat(g['event_date'])-date.today()).days if g else None
st.markdown(f'''<div class="hero"><div class="eyebrow">ENDURANCE COACH V4 · {date.today().strftime('%d/%m/%Y')}</div><h2>{'Objectif : '+g['name'] if g else 'Construis ta prochaine étape'}</h2><div>{'J-'+str(days) if days is not None else 'Date objectif à définir'}</div></div>''',unsafe_allow_html=True)
nav=st.segmented_control('Navigation',['Aujourd’hui','Planning','Progression','Coach','Plus'],default='Aujourd’hui',label_visibility='collapsed') or 'Aujourd’hui'
if nav=='Aujourd’hui':
 ci=checkin(); ps=today_session(); dec,score,status,why,action=decision(ci,ps,last_shift(),rugby_recent()); a,b=st.columns([1,2]); a.metric('État du jour',status,help='Readiness '+str(score)+'/100'); b.info('**'+dlabel(dec)+'** — '+why)
 if ps: st.markdown(f'<div class="session"><div class="eyebrow">{icon(ps["sport"])} SÉANCE DU JOUR</div><h2>{ps["title"]}</h2><span class="pill">{ps["duration_min"]} min</span><span class="pill">{ps["sport"].title()}</span><p>{ps["objective"] or ""}</p><b>{action}</b></div>',unsafe_allow_html=True)
 else: st.info('Pas de séance planifiée aujourd’hui.')
 st.subheader('Les prochains jours'); items=[]
 for x in query("SELECT * FROM sessions WHERE date(start_at)>? AND date(start_at)<=? AND status='planned' ORDER BY start_at LIMIT 5",(date.today().isoformat(),(date.today()+timedelta(days=7)).isoformat())): items.append((x['start_at'][:10],icon(x['sport']),x['title'],f"{x['duration_min']} min"))
 for x in query('SELECT * FROM shifts WHERE date(start_at)>=? AND date(start_at)<=?',(date.today().isoformat(),(date.today()+timedelta(days=7)).isoformat())): items.append((x['start_at'][:10],'🚑','Garde '+x['shift_type'],'Travail'))
 for x in query('SELECT * FROM constraints WHERE event_date>=? AND event_date<=?',(date.today().isoformat(),(date.today()+timedelta(days=7)).isoformat())): items.append((x['event_date'],'📌',x['title'],'Fixe'))
 for d,ic,t,m in sorted(items)[:6]: st.write(f'**{d[8:10]}/{d[5:7]}** · {ic} {t} · {m}')
 if not ci:
  st.subheader('Check-in · 30 secondes')
  with st.form('daily'):
   c1,c2=st.columns(2); sleep=c1.number_input('Sommeil (h)',0.0,14.0,7.0,.5); quality=c2.slider('Qualité sommeil',1,5,3); fatigue=c1.slider('Fatigue',1,5,3); motivation=c2.slider('Motivation',1,5,3); soreness=c1.slider('Courbatures',1,5,3); stress=c2.slider('Stress',1,5,3); painloc=c1.text_input('Douleur — zone'); pain=c2.slider('Douleur',0,10,0); trend=st.selectbox('Évolution',['stable','amélioration','aggravation'])
   if st.form_submit_button('Valider',use_container_width=True): execute('INSERT INTO checkins(created_at,sleep_hours,sleep_quality,fatigue,motivation,soreness,stress,pain_location,pain_score,pain_trend) VALUES(?,?,?,?,?,?,?,?,?,?)',(datetime.now().isoformat(timespec='seconds'),sleep,quality,fatigue,motivation,soreness,stress,painloc,pain,trend)); st.rerun()
elif nav=='Planning':
 st.header('Planning adaptatif V4'); future=next_goal()
 if future:
  st.write(f"Prochain objectif : **{future['name']}** · {future['event_date']}"); st.caption('Les séances sont placées autour des gardes, du rugby, de la danse et des autres contraintes fixes.')
  if st.button('⚡ Construire mon planning intelligent — 14 jours',use_container_width=True):
   end=(date.today()+timedelta(days=14)).isoformat(); shifts=query('SELECT * FROM shifts WHERE date(start_at)<=? AND date(end_at)>=?',(end,(date.today()-timedelta(days=1)).isoformat())); cons=query('SELECT * FROM constraints WHERE event_date>=? AND event_date<=?',(date.today().isoformat(),end)); result=build_plan(future,shifts,cons); execute("DELETE FROM sessions WHERE source='auto_v4' AND date(start_at)>=?",(date.today().isoformat(),))
   for s in result['sessions']: execute("INSERT INTO sessions(start_at,sport,title,duration_min,priority,intensity,objective,source) VALUES(?,?,?,?,?,?,?,'auto_v4')",(s['date'].isoformat()+'T18:00',s['sport'],s['title'],s['duration'],s['priority'],s['intensity'],s['objective']))
   execute('INSERT INTO plan_log(created_at,goal_name,summary) VALUES(?,?,?)',(datetime.now().isoformat(timespec='seconds'),future['name'],f"Phase {result['phase']} · {len(result['sessions'])} séances · {len(result['unscheduled'])} non placées")); st.success(f"Phase {result['phase']} : {len(result['sessions'])} séances placées."); st.rerun()
 start=date.today(); end=start+timedelta(days=30); ev=[]
 for x in query('SELECT * FROM shifts WHERE date(start_at)>=? AND date(start_at)<=?',(start.isoformat(),end.isoformat())): ev.append([x['start_at'][:10],'🚑','Garde '+x['shift_type'],'Travail'])
 for x in query('SELECT * FROM constraints WHERE event_date>=? AND event_date<=?',(start.isoformat(),end.isoformat())): ev.append([x['event_date'],'📌',x['title'],'Fixe'])
 for x in query('SELECT * FROM sessions WHERE date(start_at)>=? AND date(start_at)<=?',(start.isoformat(),end.isoformat())): ev.append([x['start_at'][:10],icon(x['sport']),x['title'],f"{x['duration_min']} min"])
 if ev: st.dataframe(pd.DataFrame(sorted(ev),columns=['Date','','Événement','Info']),hide_index=True,use_container_width=True)
elif nav=='Progression':
 st.header('Progression'); acts=query('SELECT * FROM activities ORDER BY start_at')
 if acts:
  df=pd.DataFrame(acts); df['Charge']=df.apply(lambda r:srpe(r['duration_min'],r['rpe']),axis=1); df['Jour']=pd.to_datetime(df['start_at']).dt.date; recent=df[pd.to_datetime(df['start_at'])>=pd.Timestamp.now()-pd.Timedelta(days=7)]; a,b,c=st.columns(3); a.metric('Charge 7 j',round(recent['Charge'].sum())); b.metric('Temps 7 j',f"{recent['duration_min'].sum()/60:.1f} h"); c.metric('Séances 7 j',len(recent)); st.line_chart(df.groupby('Jour')['Charge'].sum()); st.bar_chart(df.groupby('sport')['duration_min'].sum()/60)
 else: st.info('Ajoute tes premières activités pour démarrer le suivi.')
elif nav=='Coach':
 ci=checkin(); ps=today_session(); dec,score,status,why,action=decision(ci,ps,last_shift(),rugby_recent()); st.header('Coach'); st.markdown('### '+dlabel(dec)); st.write(why); st.success(action); st.text_area('Parle à ton coach',placeholder='On vient de me rajouter une garde de nuit jeudi…'); st.caption('La compréhension conversationnelle sera la prochaine couche. Le moteur V4 de planification est actif.')
elif nav=='Plus':
 tab1,tab2,tab3=st.tabs(['Ajouter','Objectifs','Profil'])
 with tab1:
  choice=st.radio('Ajouter',['Activité','Garde','Sport / contrainte fixe','Objectif'],horizontal=True)
  if choice=='Activité':
   with st.form('act'):
    dt=st.text_input('Date/heure',datetime.now().isoformat(timespec='minutes')); sport=st.selectbox('Sport',['running','trail','cycling','swimming','rugby','dance','strength','other']); title=st.text_input('Titre'); duration=st.number_input('Durée (min)',1,1000,60); distance=st.number_input('Distance (km)',0.0,500.0,0.0,.1); elev=st.number_input('D+ (m)',0,10000,0,10); rpe=st.slider('RPE',1,10,4); pain=st.slider('Douleur après',0,10,0)
    if st.form_submit_button('Enregistrer'): execute('INSERT INTO activities(start_at,sport,title,duration_min,distance_km,elevation_m,rpe,pain) VALUES(?,?,?,?,?,?,?,?)',(dt,sport,title,duration,distance,elev,rpe,pain)); st.success('Enregistré.')
  elif choice=='Garde':
   with st.form('shift'):
    typ=st.selectbox('Type',['24h','12h_jour','12h_nuit']); start=st.text_input('Début',datetime.now().replace(hour=8,minute=0).isoformat(timespec='minutes')); end=st.text_input('Fin',(datetime.now()+timedelta(days=1)).replace(hour=8,minute=0).isoformat(timespec='minutes'))
    if st.form_submit_button('Ajouter'): execute('INSERT INTO shifts(start_at,end_at,shift_type) VALUES(?,?,?)',(start,end,typ)); st.success('Garde ajoutée.')
  elif choice=='Sport / contrainte fixe':
   with st.form('constraint'):
    d=st.date_input('Date',date.today()); typ=st.selectbox('Type',['rugby_training','rugby_match','dance','personal','other']); title=st.text_input('Nom','Rugby'); duration=st.number_input('Durée (min)',15,360,90,15); intensity=st.selectbox('Charge',['easy','moderate','hard'],index=1); notes=st.text_area('Notes')
    if st.form_submit_button('Ajouter au calendrier'): execute('INSERT INTO constraints(event_date,event_type,title,duration_min,intensity,fixed,notes) VALUES(?,?,?,?,?,1,?)',(d.isoformat(),typ,title,duration,intensity,notes)); st.success('Contrainte enregistrée.')
  else:
   with st.form('goal'):
    name=st.text_input('Objectif / mission'); d=st.text_input('Date YYYY-MM-DD'); sport=st.text_input('Sport','cycling'); kind=st.selectbox('Type',['competition','mission','test','training_goal']); priority=st.selectbox('Priorité',['A','A/B','B','C','D']); notes=st.text_area('Détails')
    if st.form_submit_button('Créer'): execute('INSERT INTO goals(name,event_date,sport,kind,priority,notes) VALUES(?,?,?,?,?,?)',(name,d,sport,kind,priority,notes)); st.success('Objectif ajouté.')
 with tab2:
  for goal in query("SELECT * FROM goals ORDER BY CASE WHEN event_date='' THEN 1 ELSE 0 END,event_date"):
   with st.container(border=True): st.markdown(f"**{goal['name']}** · {goal['priority']}"); st.write(goal['event_date'] or 'Date à définir'); st.caption(goal['notes'] or '')
 with tab3:
  for sec,data in ATHLETE.items():
   with st.expander(sec):
    for k,v in data.items(): st.write(f'**{k} :** {v}')
st.caption('Endurance Coach V4 · moteur de planification sous contraintes · ne remplace pas un avis médical.')