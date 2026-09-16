import streamlit as st
import pandas as pd
from datetime import datetime,date,time,timedelta
from db import init,query,execute
from profile import ATHLETE,GOALS
from engine import decision,srpe
from scheduler import build_plan
from calendar_engine import recurring_instances,combined_constraints,all_shifts
from calendar_views import month_view,week_view
from workout_engine import detailed_workout
from performance_engine import load_summary,sport_summary,readiness_trend
from coach_engine import coach_brief,adaptation_options
st.set_page_config(page_title='Endurance Coach V6',page_icon='⚡',layout='wide',initial_sidebar_state='collapsed'); init()
if not query('SELECT id FROM goals LIMIT 1'):
 for g in GOALS: execute('INSERT INTO goals(name,event_date,sport,kind,priority,notes) VALUES(?,?,?,?,?,?)',g)
st.markdown("""<style>.block-container{max-width:1050px;padding-top:.7rem;padding-bottom:6rem}.hero,.card{padding:1rem;border-radius:20px}.hero{background:linear-gradient(135deg,#15171c,#29303a);color:white}.card{border:1px solid rgba(128,128,128,.22);margin:.6rem 0}.stButton button{border-radius:14px;min-height:44px;font-weight:600;white-space:normal}@media(max-width:700px){.block-container{padding-left:.6rem!important;padding-right:.6rem!important}.hero h2{font-size:1.35rem!important}.stButton button{min-height:48px}}</style>""",unsafe_allow_html=True)
def one(sql,args=()):
 r=query(sql,args); return r[0] if r else None
def next_goal(): return one("SELECT * FROM goals WHERE COALESCE(event_date,'')!='' AND event_date>=? ORDER BY event_date LIMIT 1",(date.today().isoformat(),))
def checkin(): return one('SELECT * FROM checkins WHERE date(created_at)=? ORDER BY created_at DESC LIMIT 1',(date.today().isoformat(),))
def today_session(): return one("SELECT * FROM sessions WHERE date(start_at)=? AND status='planned' ORDER BY start_at LIMIT 1",(date.today().isoformat(),))
def ico(s): return {'running':'🏃','trail':'⛰️','cycling':'🚴','swimming':'🏊','rugby':'🏉','rugby_training':'🏉','rugby_match':'🏉','dance':'💃','strength':'💪'}.get(str(s or '').lower(),'📌')
def dtiso(d,t): return datetime.combine(d,t).isoformat(timespec='minutes')
def shifts_between(start,end):
 manual=query('SELECT * FROM shifts WHERE date(start_at)<=? AND date(end_at)>=?',(end.isoformat(),(start-timedelta(days=1)).isoformat())); return all_shifts(manual,query('SELECT * FROM work_cycles WHERE active=1'),start,end,query('SELECT * FROM work_cycle_exceptions'))
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
def work_label(t): return {'24h':'Garde 24 h','12h_jour':'Garde 12 h jour','12h_nuit':'Garde 12 h nuit','formation':'Formation 08h–16h','sst':'SST 07h30–17h'}.get(t,'Travail '+str(t))
def events_between(start,end):
 events=[]; ss=shifts_between(start,end); rules=query('SELECT * FROM recurring_rules WHERE active=1'); rec,cancel=recurring_instances(rules,ss,start,end); rex={(x['rule_id'],x['original_date']):x for x in query('SELECT * FROM recurring_exceptions')}
 for x in ss:
  d=datetime.fromisoformat(x['start_at']).date(); events.append({'date':d,'time':x['start_at'][11:16],'icon':'🚑','title':work_label(x['shift_type']),'meta':'cycle' if x.get('virtual') else 'travail','kind':'cycle_shift' if x.get('virtual') else 'shift','id':x.get('id'),'cycle_id':x.get('cycle_id'),'original_date':x.get('original_date'),'start_at':x['start_at'],'end_at':x['end_at'],'uid':'sh'+str(x.get('id') or x.get('original_date'))})
 for x in rec:
  original=x['date'].isoformat(); ex=rex.get((x['rule_id'],original))
  if ex and ex['action']=='delete': continue
  if ex and ex['action']=='move' and ex.get('new_start_at'):
   ns=datetime.fromisoformat(ex['new_start_at']); x=dict(x); x['date']=ns.date(); x['start_at']=ns; x['end_at']=datetime.fromisoformat(ex['new_end_at'])
  events.append({'date':x['date'],'time':x['start_at'].strftime('%H:%M'),'icon':ico(x['event_type']),'title':x['title'],'meta':'récurrent','kind':'recurring','rule_id':x['rule_id'],'original_date':original,'duration_min':x['duration_min'],'intensity':x['intensity'],'uid':f"r{x['rule_id']}_{original}"})
 for x in query('SELECT * FROM constraints WHERE event_date>=? AND event_date<=?',(start.isoformat(),end.isoformat())): events.append({'date':date.fromisoformat(x['event_date']),'icon':'📌','title':x['title'],'meta':'fixe','kind':'constraint','id':x['id'],'uid':'c'+str(x['id'])})
 for x in query("SELECT * FROM sessions WHERE date(start_at)>=? AND date(start_at)<=? AND status='planned'",(start.isoformat(),end.isoformat())): events.append({'date':date.fromisoformat(x['start_at'][:10]),'time':x['start_at'][11:16],'icon':ico(x['sport']),'title':x['title'],'meta':f"{x['duration_min'] or '?'} min",'kind':'session','id':x['id'],'sport':x['sport'],'duration_min':x['duration_min'],'intensity':x['intensity'],'objective':x['objective'],'priority':x['priority'],'start_at':x['start_at'],'uid':'s'+str(x['id'])})
 for x in query("SELECT * FROM goals WHERE event_date!='' AND event_date>=? AND event_date<=?",(start.isoformat(),end.isoformat())): events.append({'date':date.fromisoformat(x['event_date']),'icon':'🏁','title':x['name'],'meta':'objectif','kind':'goal','id':x['id'],'uid':'g'+str(x['id'])})
 return events,cancel
def event_editor(e):
 st.subheader(f"{e.get('icon','📌')} {e['title']}"); st.caption(f"{e['date'].strftime('%d/%m/%Y')} · {e.get('time','')} · {e.get('meta','')}")
 if e['kind']=='session':
  w=detailed_workout(e.get('sport'),e.get('intensity'),e.get('duration_min'),e.get('objective')); st.write('**Échauffement** — '+w['warmup']); st.write('**Bloc principal** — '+w['main']); st.write('**Retour au calme** — '+w['cooldown']); st.write('**Cible** — '+w['intensity_target']); st.info(w['coach_note'])
  with st.expander('Modifier / déplacer / supprimer'):
   nd=st.date_input('Jour',e['date'],key='sd'+str(e['id'])); nt=st.time_input('Heure',datetime.fromisoformat(e['start_at']).time(),key='st'+str(e['id'])); dur=st.number_input('Durée',10,600,int(e.get('duration_min') or 60),5,key='du'+str(e['id'])); c1,c2=st.columns(2)
   if c1.button('Enregistrer',key='save'+str(e['id']),use_container_width=True): execute('UPDATE sessions SET start_at=?,duration_min=? WHERE id=?',(dtiso(nd,nt),dur,e['id'])); st.rerun()
   if c2.button('Supprimer',key='del'+str(e['id']),use_container_width=True): execute('DELETE FROM sessions WHERE id=?',(e['id'],)); st.rerun()
 elif e['kind']=='recurring':
  nd=st.date_input('Nouvelle date',e['date'],key='rd'); nt=st.time_input('Nouvelle heure',datetime.strptime(e.get('time','19:00'),'%H:%M').time(),key='rt'); c1,c2=st.columns(2)
  if c1.button('Déplacer cette occurrence',use_container_width=True):
   ns=datetime.combine(nd,nt); execute("INSERT INTO recurring_exceptions(rule_id,original_date,action,new_start_at,new_end_at) VALUES(?,?,?,?,?) ON CONFLICT(rule_id,original_date) DO UPDATE SET action='move',new_start_at=excluded.new_start_at,new_end_at=excluded.new_end_at",(e['rule_id'],e['original_date'],'move',ns.isoformat(timespec='minutes'),(ns+timedelta(minutes=int(e.get('duration_min') or 90))).isoformat(timespec='minutes'))); st.rerun()
  if c2.button('Supprimer cette occurrence',use_container_width=True): execute("INSERT INTO recurring_exceptions(rule_id,original_date,action) VALUES(?,?,?) ON CONFLICT(rule_id,original_date) DO UPDATE SET action='delete'",(e['rule_id'],e['original_date'],'delete')); st.rerun()
 elif e['kind']=='cycle_shift':
  st.caption('Cette modification ne décale pas le reste du cycle.'); nd=st.date_input('Nouvelle date',e['date'],key='gd'); c1,c2=st.columns(2)
  if c1.button('Déplacer',use_container_width=True):
   old=datetime.fromisoformat(e['start_at']); ns=datetime.combine(nd,old.time()); execute("INSERT INTO work_cycle_exceptions(cycle_id,original_date,action,new_start_at,new_end_at) VALUES(?,?,?,?,?) ON CONFLICT(cycle_id,original_date) DO UPDATE SET action='move',new_start_at=excluded.new_start_at,new_end_at=excluded.new_end_at",(e['cycle_id'],e['original_date'],'move',ns.isoformat(timespec='minutes'),(ns+timedelta(hours=24)).isoformat(timespec='minutes'))); st.rerun()
  if c2.button('Supprimer occurrence',use_container_width=True): execute("INSERT INTO work_cycle_exceptions(cycle_id,original_date,action) VALUES(?,?,?) ON CONFLICT(cycle_id,original_date) DO UPDATE SET action='delete'",(e['cycle_id'],e['original_date'],'delete')); st.rerun()
 elif e['kind']=='shift':
  if st.button('Supprimer cette période de travail'): execute('DELETE FROM shifts WHERE id=?',(e['id'],)); st.rerun()
 elif e['kind']=='constraint':
  if st.button('Supprimer cet événement'): execute('DELETE FROM constraints WHERE id=?',(e['id'],)); st.rerun()
g=next_goal(); countdown=(date.fromisoformat(g['event_date'])-date.today()).days if g else None
st.markdown(f"<div class='hero'><small>ENDURANCE COACH · V6</small><h2>{g['name'] if g else 'Ton coach adaptatif'}</h2><b>{'J-'+str(countdown) if countdown is not None else ''}</b><br><small>Travail · récupération · multisport · objectifs</small></div>",unsafe_allow_html=True)
nav=st.segmented_control('Navigation',['🏠 Aujourd’hui','📅 Planning','📈 Progression','🤖 Coach','＋ Ajouter','••• Plus'],default='🏠 Aujourd’hui',label_visibility='collapsed') or '🏠 Aujourd’hui'
if nav=='🏠 Aujourd’hui':
 ci=checkin(); ps=today_session(); dec,score,status,why,action=decision(ci,ps,last_shift(),rugby_recent()); acts=query('SELECT * FROM activities WHERE start_at>=?',((date.today()-timedelta(days=28)).isoformat(),)); loads=load_summary(acts); a,b,c=st.columns(3); a.metric('Forme',score); b.metric('Charge 7 j',loads['load7']); c.metric('Objectif',f'J-{countdown}' if countdown is not None else '—'); st.markdown(f"### {status.replace('_',' ')} · {dec.replace('_',' ').title()}"); st.write(why)
 if ps:
  w=detailed_workout(ps['sport'],ps['intensity'],ps['duration_min'],ps['objective']); st.markdown(f"<div class='card'><small>SÉANCE DU JOUR</small><h2>{ico(ps['sport'])} {ps['title']}</h2><b>{ps['duration_min']} min · {ps['intensity']}</b><p>{w['summary']}</p></div>",unsafe_allow_html=True)
  with st.expander('▶ Voir la séance complète',expanded=True): st.write('**Échauffement** — '+w['warmup']); st.write('**Bloc principal** — '+w['main']); st.write('**Retour au calme** — '+w['cooldown']); st.write('**Cible** — '+w['intensity_target']); st.write('**Nutrition** — '+w['nutrition'])
 else: st.info('Aucune séance obligatoire aujourd’hui.')
 st.markdown('### Coach du jour')
 for msg in coach_brief(score,status,ps,g,last_shift(),loads): st.write('• '+msg)
 if not ci:
  with st.expander('☀️ Check-in du jour',expanded=True):
   with st.form('check'):
    sleep=st.number_input('Sommeil (h)',0.,14.,7.,.5); fatigue=st.slider('Fatigue',1,5,3); quality=st.slider('Qualité sommeil',1,5,3); motivation=st.slider('Motivation',1,5,3); soreness=st.slider('Courbatures',1,5,3); stress=st.slider('Stress',1,5,3); painloc=st.text_input('Zone douloureuse'); pain=st.slider('Douleur',0,10,0); trend=st.selectbox('Évolution',['stable','amélioration','aggravation'])
    if st.form_submit_button('Enregistrer',use_container_width=True): execute('INSERT INTO checkins(created_at,sleep_hours,sleep_quality,fatigue,motivation,soreness,stress,pain_location,pain_score,pain_trend) VALUES(?,?,?,?,?,?,?,?,?,?)',(datetime.now().isoformat(),sleep,quality,fatigue,motivation,soreness,stress,painloc,pain,trend)); st.rerun()
elif nav=='📅 Planning':
 st.header('Planning mobile-first'); view=st.segmented_control('Vue',['Jour / Mois','Semaine'],default='Jour / Mois'); selected=None
 if view=='Jour / Mois':
  c1,c2=st.columns(2); y=c1.selectbox('Année',range(date.today().year,date.today().year+3)); m=c2.selectbox('Mois',range(1,13),index=date.today().month-1,format_func=lambda x:['Janvier','Février','Mars','Avril','Mai','Juin','Juillet','Août','Septembre','Octobre','Novembre','Décembre'][x-1]); start=date(y,m,1); end=(date(y+1,1,1)-timedelta(days=1)) if m==12 else date(y,m+1,1)-timedelta(days=1); ev,cancel=events_between(start,end); selected=month_view(y,m,ev)
 else:
  chosen=st.date_input('Semaine contenant le',date.today()); start=chosen-timedelta(days=chosen.weekday()); end=start+timedelta(days=6); ev,cancel=events_between(start,end); selected=week_view(start,ev)
 if selected: st.session_state['selected_event']=selected
 if st.session_state.get('selected_event'): st.divider(); event_editor(st.session_state['selected_event'])
 st.divider()
 if g and st.button('⚡ Recalculer les 14 prochains jours',use_container_width=True):
  s=date.today(); h=s+timedelta(days=13); ss=shifts_between(s,h); fixed=query('SELECT * FROM constraints WHERE event_date>=? AND event_date<=?',(s.isoformat(),h.isoformat())); rec,_=recurring_instances(query('SELECT * FROM recurring_rules WHERE active=1'),ss,s,h); result=build_plan(g,ss,combined_constraints(fixed,rec),start=s,days=14); execute("DELETE FROM sessions WHERE date(start_at)>=? AND date(start_at)<=? AND source LIKE 'auto%'",(s.isoformat(),h.isoformat()))
  for x in result['sessions']: execute("INSERT INTO sessions(start_at,sport,title,duration_min,priority,intensity,objective,source) VALUES(?,?,?,?,?,?,?,'auto_v6')",(x['date'].isoformat()+'T18:00',x['sport'],x['title'],x['duration'],x['priority'],x['intensity'],x['objective']))
  st.success(f"{len(result['sessions'])} séances placées · {len(result['unscheduled'])} non forcées"); st.rerun()
elif nav=='📈 Progression':
 st.header('Progression'); acts=query('SELECT * FROM activities ORDER BY start_at DESC'); loads=load_summary(acts); sports=sport_summary(acts); a,b,c=st.columns(3); a.metric('Charge 7 j',loads['load7']); b.metric('Référence 28 j',loads['weekly_baseline']); c.metric('Ratio',loads['ratio'] if loads['ratio'] is not None else '—')
 if loads['daily']: st.line_chart(pd.DataFrame([{'Jour':d,'Charge':v} for d,v in sorted(loads['daily'].items())]),x='Jour',y='Charge')
 st.subheader('28 derniers jours')
 for sport,x in sports.items(): st.write(f"{ico(sport)} **{sport.title()}** · {x['sessions']} séances · {round(x['minutes']/60,1)} h · {round(x['distance_km'],1)} km · {round(x['elevation_m'])} m D+")
 trend=readiness_trend(query('SELECT * FROM checkins ORDER BY created_at DESC LIMIT 14'))
 if trend: st.subheader('Récupération'); st.line_chart(pd.DataFrame(trend),x='date',y='score')
elif nav=='🤖 Coach':
 ci=checkin(); ps=today_session(); dec,score,status,why,action=decision(ci,ps,last_shift(),rugby_recent()); loads=load_summary(query('SELECT * FROM activities WHERE start_at>=?',((date.today()-timedelta(days=28)).isoformat(),))); st.header('Coach adaptatif'); st.markdown(f"### {dec.replace('_',' ').title()}"); st.write(why); st.success(action)
 for msg in coach_brief(score,status,ps,g,last_shift(),loads): st.write('• '+msg)
 if ps:
  st.subheader('Options d’adaptation')
  for opt in adaptation_options(ps,why): st.write('→ '+opt)
elif nav=='＋ Ajouter':
 st.header('Ajouter'); kind=st.selectbox('Type',['🏋️ Séance','🚑 Travail / garde','🔁 Récurrence','🗓️ Cycle travail','📌 Événement','🏁 Objectif','✅ Activité'])
 if kind=='🚑 Travail / garde':
  labels={'Garde 24 h':'24h','Garde 12 h jour':'12h_jour','Garde 12 h nuit':'12h_nuit','Formation 08h–16h':'formation','SST 07h30–17h':'sst'}; chosen=st.selectbox('Type',list(labels)); typ=labels[chosen]; d=st.date_input('Jour',date.today()); defaults={'24h':(time(8),time(8),1),'12h_jour':(time(7),time(20),0),'12h_nuit':(time(19),time(8),1),'formation':(time(7),time(17),0),'sst':(time(6,30),time(18),0)}; sh,eh,plus=defaults[typ]; stt=st.time_input('Indisponible à partir de',sh); ed=st.date_input('Fin',d+timedelta(days=plus)); et=st.time_input('Disponible à partir de',eh)
  if st.button('Ajouter travail',use_container_width=True): execute('INSERT INTO shifts(start_at,end_at,shift_type) VALUES(?,?,?)',(dtiso(d,stt),dtiso(ed,et),typ)); st.rerun()
 elif kind=='🔁 Récurrence':
  typ=st.selectbox('Activité',['rugby_training','rugby_match','dance','other']); title=st.text_input('Nom','Rugby'); wd=st.selectbox('Chaque',['Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi','Dimanche']); tt=st.time_input('Heure',time(19)); dur=st.number_input('Durée',15,360,120,15); intensity=st.selectbox('Charge',['easy','moderate','hard']); sd=st.date_input('À partir du',date.today())
  if st.button('Créer récurrence',use_container_width=True): execute('INSERT INTO recurring_rules(title,event_type,weekday,start_time,duration_min,intensity,start_date,active) VALUES(?,?,?,?,?,?,?,1)',(title,typ,['Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi','Dimanche'].index(wd),tt.strftime('%H:%M'),dur,intensity,sd.isoformat())); st.rerun()
 elif kind=='🗓️ Cycle travail':
  anchor=st.date_input('Date d’une garde de référence',date.today())
  if st.button('Activer cycle 24/72',use_container_width=True): execute('UPDATE work_cycles SET active=0'); execute('INSERT INTO work_cycles(title,anchor_date,cycle_days,active) VALUES(?,?,4,1)',('Cycle 24/72',anchor.isoformat())); st.rerun()
 elif kind=='🏋️ Séance':
  sport=st.selectbox('Sport',['running','cycling','swimming','trail','strength']); d=st.date_input('Jour',date.today()); t=st.time_input('Heure',time(18)); title=st.text_input('Nom'); duration=st.number_input('Durée',10,600,60,5); intensity=st.selectbox('Intensité',['easy','moderate','threshold','hard']); objective=st.text_area('Objectif'); priority=st.select_slider('Importance',['P3','P2','P1','P0'],value='P2')
  if st.button('Ajouter séance',use_container_width=True): execute('INSERT INTO sessions(start_at,sport,title,duration_min,priority,intensity,objective) VALUES(?,?,?,?,?,?,?)',(dtiso(d,t),sport,title or 'Séance '+sport,duration,priority,intensity,objective)); st.rerun()
 elif kind=='📌 Événement':
  title=st.text_input('Nom','Mont Ventoux'); d=st.date_input('Date',date.today()); dur=st.number_input('Durée estimée',15,1000,120,15); intensity=st.selectbox('Charge',['easy','moderate','hard'])
  if st.button('Ajouter événement',use_container_width=True): execute('INSERT INTO constraints(event_date,event_type,title,duration_min,intensity) VALUES(?,?,?,?,?)',(d.isoformat(),'personal',title,dur,intensity)); st.rerun()
 elif kind=='🏁 Objectif':
  name=st.text_input('Nom'); d=st.date_input('Date',date.today()); sport=st.text_input('Sport','running'); priority=st.selectbox('Priorité',['A','A/B','B','C','D'])
  if st.button('Ajouter objectif',use_container_width=True): execute('INSERT INTO goals(name,event_date,sport,kind,priority) VALUES(?,?,?,?,?)',(name,d.isoformat(),sport,'competition',priority)); st.rerun()
 else:
  sport=st.selectbox('Sport',['running','cycling','swimming','trail','rugby','dance','strength']); d=st.date_input('Date',date.today()); dur=st.number_input('Durée',1,1000,60); dist=st.number_input('Distance km',0.,500.,0.,.1); elev=st.number_input('D+ m',0,10000,0,10); rpe=st.slider('RPE',1,10,4); title=st.text_input('Titre')
  if st.button('Enregistrer activité',use_container_width=True): execute('INSERT INTO activities(start_at,sport,title,duration_min,distance_km,elevation_m,rpe) VALUES(?,?,?,?,?,?,?)',(d.isoformat()+'T12:00',sport,title,dur,dist,elev,rpe)); st.rerun()
else:
 st.header('Plus'); st.subheader('Objectifs')
 for x in query('SELECT * FROM goals ORDER BY event_date'): st.write(f"🏁 **{x['name']}** · {x['event_date']} · priorité {x['priority']}")
 st.subheader('Profil athlète')
 for sec,data in ATHLETE.items():
  with st.expander(sec):
   for k,v in data.items(): st.write(f'**{k} :** {v}')
st.caption('Endurance Coach V6 · mobile-first · charge multisport · coach adaptatif')