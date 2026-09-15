import streamlit as st
import pandas as pd
from datetime import datetime,date,time,timedelta
from db import init,query,execute
from profile import ATHLETE,GOALS
from engine import decision,srpe
from scheduler import build_plan
from calendar_engine import recurring_instances,combined_constraints,all_shifts
from calendar_views import month_view,week_view
st.set_page_config(page_title='Endurance Coach',page_icon='⚡',layout='wide',initial_sidebar_state='collapsed'); init()
if not query('SELECT id FROM goals LIMIT 1'):
    for g in GOALS: execute('INSERT INTO goals(name,event_date,sport,kind,priority,notes) VALUES(?,?,?,?,?,?)',g)
st.markdown("""<style>.block-container{max-width:1100px;padding-top:1rem;padding-bottom:5rem}.hero,.card{padding:1rem;border-radius:20px}.hero{background:linear-gradient(135deg,#15171c,#252a33);color:white}.card{border:1px solid rgba(128,128,128,.22);margin:.6rem 0}.big{font-size:2.2rem;font-weight:750}.stButton button{border-radius:14px;min-height:44px;font-weight:600}</style>""",unsafe_allow_html=True)
def one(sql,args=()):
 r=query(sql,args); return r[0] if r else None
def next_goal(): return one("SELECT * FROM goals WHERE COALESCE(event_date,'')!='' AND event_date>=? ORDER BY event_date LIMIT 1",(date.today().isoformat(),))
def checkin(): return one('SELECT * FROM checkins WHERE date(created_at)=? ORDER BY created_at DESC LIMIT 1',(date.today().isoformat(),))
def today_session(): return one("SELECT * FROM sessions WHERE date(start_at)=? AND status='planned' ORDER BY start_at LIMIT 1",(date.today().isoformat(),))
def ico(s): return {'running':'🏃','trail':'⛰️','cycling':'🚴','swimming':'🏊','rugby':'🏉','rugby_training':'🏉','rugby_match':'🏉','dance':'💃','strength':'💪'}.get(str(s or '').lower(),'📌')
def dtiso(d,t): return datetime.combine(d,t).isoformat(timespec='minutes')
def shifts_between(start,end):
 manual=query('SELECT * FROM shifts WHERE date(start_at)<=? AND date(end_at)>=?',(end.isoformat(),(start-timedelta(days=1)).isoformat())); return all_shifts(manual,query('SELECT * FROM work_cycles WHERE active=1'),start,end,query('SELECT * FROM work_cycle_exceptions'))
def recurring_between(start,end): return recurring_instances(query('SELECT * FROM recurring_rules WHERE active=1'),shifts_between(start,end),start,end)
def last_shift():
 past=[]
 for x in shifts_between(date.today()-timedelta(days=3),date.today()):
  try:
   e=datetime.fromisoformat(x['end_at'])
   if e<=datetime.now(): past.append((e,x))
  except: pass
 if not past:return None
 e,x=max(past,key=lambda z:z[0]); x=dict(x); x['hours_since']=(datetime.now()-e).total_seconds()/3600; return x
def rugby_recent(): return bool(query("SELECT id FROM activities WHERE sport='rugby' AND start_at>=? LIMIT 1",((datetime.now()-timedelta(hours=36)).isoformat(timespec='minutes'),)))
def events_between(start,end):
 events=[]; ss=shifts_between(start,end); rec,cancel=recurring_instances(query('SELECT * FROM recurring_rules WHERE active=1'),ss,start,end)
 for x in ss:
  d=datetime.fromisoformat(x['start_at']).date(); events.append({'date':d,'time':x['start_at'][11:16],'icon':'🚑','title':'Garde 24 h' if x['shift_type']=='24h' else 'Garde '+x['shift_type'],'meta':'déplacée' if x.get('moved') else ('cycle' if x.get('virtual') else 'exceptionnelle')})
 for x in rec: events.append({'date':x['date'],'time':x['start_at'].strftime('%H:%M'),'icon':ico(x['event_type']),'title':x['title'],'meta':'récurrent'})
 for x in query('SELECT * FROM constraints WHERE event_date>=? AND event_date<=?',(start.isoformat(),end.isoformat())): events.append({'date':date.fromisoformat(x['event_date']),'icon':'📌','title':x['title'],'meta':'fixe'})
 for x in query("SELECT * FROM sessions WHERE date(start_at)>=? AND date(start_at)<=? AND status='planned'",(start.isoformat(),end.isoformat())): events.append({'date':date.fromisoformat(x['start_at'][:10]),'time':x['start_at'][11:16],'icon':ico(x['sport']),'title':x['title'],'meta':f"{x['duration_min'] or '?'} min"})
 for x in query("SELECT * FROM goals WHERE event_date!='' AND event_date>=? AND event_date<=?",(start.isoformat(),end.isoformat())): events.append({'date':date.fromisoformat(x['event_date']),'icon':'🏁','title':x['name'],'meta':'objectif'})
 return events,cancel
g=next_goal(); countdown=(date.fromisoformat(g['event_date'])-date.today()).days if g else None
st.markdown(f"<div class='hero'><small>ENDURANCE COACH V4.4</small><h2>{'Objectif : '+g['name'] if g else 'Ton coach adaptatif'}</h2><div>{'J-'+str(countdown) if countdown is not None else ''}</div></div>",unsafe_allow_html=True)
nav=st.segmented_control('Navigation',['Aujourd’hui','Planning','Progression','Coach','Ajouter','Plus'],default='Aujourd’hui',label_visibility='collapsed') or 'Aujourd’hui'
if nav=='Aujourd’hui':
 ci=checkin(); ps=today_session(); dec,score,status,why,action=decision(ci,ps,last_shift(),rugby_recent()); a,b=st.columns([1,2]); a.metric('État du jour',status,score); b.markdown(f"### {dec.replace('_',' ').title()}\n{why}")
 if ps: st.markdown(f"<div class='card'><h2>{ico(ps['sport'])} {ps['title']}</h2><b>{ps['duration_min'] or '?'} min</b><p>{ps['objective'] or ''}</p><b>{action}</b></div>",unsafe_allow_html=True)
 else: st.info('Pas de séance planifiée aujourd’hui.')
 ev,cancel=events_between(date.today(),date.today()+timedelta(days=7)); st.subheader('Prochains jours')
 for e in sorted(ev,key=lambda x:(x['date'],x.get('time','')))[:8]: st.write(f"**{e['date'].strftime('%d/%m')}** · {e['icon']} {e['title']} · {e.get('meta','')}")
 if not ci:
  with st.expander('☀️ Check-in du jour',expanded=True):
   with st.form('check'):
    c1,c2=st.columns(2); sleep=c1.number_input('Sommeil (h)',0.,14.,7.,.5); fatigue=c2.slider('Fatigue',1,5,3); quality=c1.slider('Qualité sommeil',1,5,3); motivation=c2.slider('Motivation',1,5,3); soreness=c1.slider('Courbatures',1,5,3); stress=c2.slider('Stress',1,5,3); painloc=c1.text_input('Zone douloureuse'); pain=c2.slider('Douleur',0,10,0); trend=st.selectbox('Évolution',['stable','amélioration','aggravation'])
    if st.form_submit_button('Enregistrer',use_container_width=True): execute('INSERT INTO checkins(created_at,sleep_hours,sleep_quality,fatigue,motivation,soreness,stress,pain_location,pain_score,pain_trend) VALUES(?,?,?,?,?,?,?,?,?,?)',(datetime.now().isoformat(timespec='seconds'),sleep,quality,fatigue,motivation,soreness,stress,painloc,pain,trend)); st.rerun()
elif nav=='Planning':
 st.header('Planning'); view=st.segmented_control('Vue',['Mois','Semaine'],default='Mois')
 if view=='Mois':
  c1,c2=st.columns(2); y=c1.selectbox('Année',range(date.today().year,date.today().year+3)); m=c2.selectbox('Mois',range(1,13),index=date.today().month-1,format_func=lambda x:['Janvier','Février','Mars','Avril','Mai','Juin','Juillet','Août','Septembre','Octobre','Novembre','Décembre'][x-1]); start=date(y,m,1); end=(date(y+1,1,1)-timedelta(days=1)) if m==12 else date(y,m+1,1)-timedelta(days=1); ev,cancel=events_between(start,end); month_view(y,m,ev)
 else:
  chosen=st.date_input('Une date de la semaine',date.today()); start=chosen-timedelta(days=chosen.weekday()); end=start+timedelta(days=6); ev,cancel=events_between(start,end); week_view(start,ev)
 st.divider(); future=next_goal()
 if future and st.button('⚡ Recalculer les 14 prochains jours',use_container_width=True):
  s=date.today(); h=s+timedelta(days=14); ss=shifts_between(s,h); fixed=query('SELECT * FROM constraints WHERE event_date>=? AND event_date<=?',(s.isoformat(),h.isoformat())); rec,_=recurring_instances(query('SELECT * FROM recurring_rules WHERE active=1'),ss,s,h); result=build_plan(future,ss,combined_constraints(fixed,rec)); execute("DELETE FROM sessions WHERE source='auto_v4' AND date(start_at)>=?",(s.isoformat(),))
  for x in result['sessions']: execute("INSERT INTO sessions(start_at,sport,title,duration_min,priority,intensity,objective,source) VALUES(?,?,?,?,?,?,?,'auto_v4')",(x['date'].isoformat()+'T18:00',x['sport'],x['title'],x['duration'],x['priority'],x['intensity'],x['objective']))
  st.success(f"{len(result['sessions'])} séances placées."); st.rerun()
 if cancel:
  with st.expander('Annulations automatiques'):
   for x in cancel: st.warning(f"{x['date'].strftime('%d/%m')} · {x['title']} — {x['reason']}")
elif nav=='Progression':
 st.header('Progression'); acts=query('SELECT * FROM activities ORDER BY start_at')
 if acts:
  df=pd.DataFrame(acts); df['Charge']=df.apply(lambda r:srpe(r.get('duration_min'),r.get('rpe')),axis=1); df['Jour']=pd.to_datetime(df['start_at']).dt.date; st.line_chart(df.groupby('Jour')['Charge'].sum()); st.bar_chart(df.groupby('sport')['duration_min'].sum()/60)
 else: st.info('Les graphiques apparaîtront avec tes activités.')
elif nav=='Coach':
 ci=checkin(); ps=today_session(); dec,score,status,why,action=decision(ci,ps,last_shift(),rugby_recent()); st.header('Coach'); st.markdown(f"### {dec.replace('_',' ').title()}"); st.write(why); st.success(action); st.text_area('Message au coach',placeholder='Ex. J’ai une garde jeudi, adapte ma semaine…')
elif nav=='Ajouter':
 st.header('Ajouter'); kind=st.selectbox('Type',['🏋️ Séance','🚑 Garde exceptionnelle','🔁 Récurrence','🗓️ Cycle travail','📌 Événement','🏁 Objectif','✅ Activité'])
 if kind=='🏋️ Séance':
  with st.form('session'):
   sport=st.selectbox('Sport',['running','cycling','swimming','trail','strength']); c1,c2=st.columns(2); d=c1.date_input('Jour',date.today()); t=c2.time_input('Heure',time(18)); title=st.text_input('Nom'); duration=st.number_input('Durée',10,600,60,5); intensity=st.selectbox('Intensité',['easy','moderate','threshold','hard']); objective=st.text_area('Consignes'); priority=st.select_slider('Importance',['P3','P2','P1','P0'],value='P2')
   if st.form_submit_button('Ajouter',use_container_width=True): execute('INSERT INTO sessions(start_at,sport,title,duration_min,priority,intensity,objective) VALUES(?,?,?,?,?,?,?)',(dtiso(d,t),sport,title or 'Séance '+sport,duration,priority,intensity,objective)); st.success('Séance ajoutée.')
 elif kind=='🚑 Garde exceptionnelle':
  with st.form('guard'):
   typ=st.selectbox('Type',['24h','12h_jour','12h_nuit']); d=st.date_input('Jour',date.today()); defaults={'24h':(time(8),time(8),1),'12h_jour':(time(7),time(20),0),'12h_nuit':(time(19),time(8),1)}; sh,eh,plus=defaults[typ]; stt=st.time_input('Début',sh); ed=st.date_input('Fin — jour',d+timedelta(days=plus)); et=st.time_input('Fin — heure',eh)
   if st.form_submit_button('Ajouter',use_container_width=True): execute('INSERT INTO shifts(start_at,end_at,shift_type) VALUES(?,?,?)',(dtiso(d,stt),dtiso(ed,et),typ)); st.success('Garde ajoutée.'); st.rerun()
 elif kind=='🔁 Récurrence':
  with st.form('rec'):
   typ=st.selectbox('Activité',['rugby_training','rugby_match','dance','other']); title=st.text_input('Nom','Rugby'); wd=st.selectbox('Chaque',['Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi','Dimanche']); tt=st.time_input('Heure',time(19)); dur=st.number_input('Durée',15,360,120,15); intensity=st.selectbox('Charge',['easy','moderate','hard']); sd=st.date_input('À partir du',date.today()); has_end=st.checkbox('Date de fin'); ed=st.date_input('Jusqu’au',date.today()+timedelta(days=180)) if has_end else None
   if st.form_submit_button('Créer',use_container_width=True): execute('INSERT INTO recurring_rules(title,event_type,weekday,start_time,duration_min,intensity,start_date,end_date,active) VALUES(?,?,?,?,?,?,?,?,1)',(title,typ,['Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi','Dimanche'].index(wd),tt.strftime('%H:%M'),dur,intensity,sd.isoformat(),ed.isoformat() if ed else None)); st.success('Récurrence créée.'); st.rerun()
 elif kind=='🗓️ Cycle travail':
  st.caption('24 h de garde puis 72 h de repos. Une garde de référence suffit.')
  with st.form('cycle'):
   title=st.text_input('Nom','Cycle 24/72'); anchor=st.date_input('Date d’une garde de référence',date.today())
   if st.form_submit_button('Activer',use_container_width=True): execute('UPDATE work_cycles SET active=0'); execute('INSERT INTO work_cycles(title,anchor_date,cycle_days,active) VALUES(?,?,4,1)',(title,anchor.isoformat())); st.success('Cycle activé.'); st.rerun()
 elif kind=='📌 Événement':
  with st.form('event'):
   d=st.date_input('Jour',date.today()); title=st.text_input('Nom'); typ=st.selectbox('Type',['personal','rugby_training','rugby_match','dance','other']); dur=st.number_input('Durée',15,600,60,15); intensity=st.selectbox('Charge',['easy','moderate','hard'])
   if st.form_submit_button('Ajouter',use_container_width=True): execute('INSERT INTO constraints(event_date,event_type,title,duration_min,intensity,fixed) VALUES(?,?,?,?,?,1)',(d.isoformat(),typ,title,dur,intensity)); st.success('Événement ajouté.')
 elif kind=='🏁 Objectif':
  with st.form('goal'):
   name=st.text_input('Objectif'); d=st.date_input('Date',date.today()+timedelta(days=30)); sport=st.selectbox('Sport',['running','trail','cycling','triathlon','other']); priority=st.selectbox('Priorité',['A','A/B','B','C']); notes=st.text_area('Détails')
   if st.form_submit_button('Créer',use_container_width=True): execute('INSERT INTO goals(name,event_date,sport,kind,priority,notes) VALUES(?,?,?,?,?,?)',(name,d.isoformat(),sport,'competition',priority,notes)); st.success('Objectif créé.')
 else:
  with st.form('activity'):
   d=st.date_input('Jour',date.today()); t=st.time_input('Heure',time(18)); sport=st.selectbox('Sport',['running','trail','cycling','swimming','rugby','dance','strength','other']); title=st.text_input('Titre'); dur=st.number_input('Durée',1,1000,60); dist=st.number_input('Distance km',0.,500.,0.,.1); elev=st.number_input('D+',0,10000,0,10); rpe=st.slider('RPE',1,10,4); pain=st.slider('Douleur après',0,10,0)
  if st.form_submit_button('Enregistrer',use_container_width=True): execute('INSERT INTO activities(start_at,sport,title,duration_min,distance_km,elevation_m,rpe,pain) VALUES(?,?,?,?,?,?,?,?)',(dtiso(d,t),sport,title,dur,dist,elev,rpe,pain)); st.success('Activité enregistrée.')
else:
 tab1,tab2,tab3=st.tabs(['Gérer cycle travail','Objectifs','Profil'])
 with tab1:
  cycles=query('SELECT * FROM work_cycles WHERE active=1')
  if not cycles: st.info('Active le cycle dans Ajouter → Cycle travail.')
  else:
   auto=[x for x in shifts_between(date.today()-timedelta(days=7),date.today()+timedelta(days=90)) if x.get('virtual')]; st.caption('Une exception ne décale jamais les gardes suivantes.')
   labels={f"{datetime.fromisoformat(x['start_at']).strftime('%d/%m/%Y')}"+(' · déplacée' if x.get('moved') else ''):x for x in auto}
   if labels:
    x=labels[st.selectbox('Garde du cycle',list(labels))]; action=st.radio('Action',['Déplacer cette garde uniquement','Supprimer cette garde uniquement','Rétablir la garde théorique'])
    if action.startswith('Déplacer'):
     nd=st.date_input('Nouvelle date',datetime.fromisoformat(x['start_at']).date()); nt=st.time_input('Nouvelle heure',time(8))
     if st.button('Confirmer le déplacement',use_container_width=True):
      ns=datetime.combine(nd,nt); ne=ns+timedelta(hours=24); execute("INSERT INTO work_cycle_exceptions(cycle_id,original_date,action,new_start_at,new_end_at) VALUES(?,?,?,?,?) ON CONFLICT(cycle_id,original_date) DO UPDATE SET action=excluded.action,new_start_at=excluded.new_start_at,new_end_at=excluded.new_end_at",(x['cycle_id'],x['original_date'],'move',ns.isoformat(timespec='minutes'),ne.isoformat(timespec='minutes'))); st.success('Garde déplacée sans modifier le cycle.'); st.rerun()
    elif action.startswith('Supprimer'):
     if st.button('Confirmer la suppression',use_container_width=True): execute("INSERT INTO work_cycle_exceptions(cycle_id,original_date,action) VALUES(?,?,?) ON CONFLICT(cycle_id,original_date) DO UPDATE SET action=excluded.action,new_start_at=NULL,new_end_at=NULL",(x['cycle_id'],x['original_date'],'delete')); st.success('Occurrence supprimée.'); st.rerun()
    elif st.button('Rétablir',use_container_width=True): execute('DELETE FROM work_cycle_exceptions WHERE cycle_id=? AND original_date=?',(x['cycle_id'],x['original_date'])); st.success('Garde théorique rétablie.'); st.rerun()
 with tab2:
  for x in query("SELECT * FROM goals ORDER BY CASE WHEN event_date='' THEN 1 ELSE 0 END,event_date"): st.write(f"**{x['name']}** · {x['event_date'] or 'date à définir'} · {x['priority']}")
 with tab3:
  for sec,data in ATHLETE.items():
   with st.expander(sec):
    for k,v in data.items(): st.write(f'**{k} :** {v}')
st.caption('Endurance Coach V4.4 · cycle 24/72 + exceptions individuelles + calendrier mensuel/hebdomadaire.')