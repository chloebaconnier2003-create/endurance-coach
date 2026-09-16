import streamlit as st
import pandas as pd
from datetime import date,timedelta
from db import query,execute
from performance_engine import load_summary,sport_summary,readiness_trend
from v7_engine import week_bounds,week_summary,roadmap,test_catalog,suggested_tests
from weekly_generator import generate_week,generate_until

def week_page():
 st.header('Ma semaine');start,end=week_bounds();sessions=query('SELECT * FROM sessions WHERE date(start_at)>=? AND date(start_at)<=?',(start.isoformat(),end.isoformat()));acts=query('SELECT * FROM activities WHERE date(start_at)>=? AND date(start_at)<=?',(start.isoformat(),end.isoformat()));x=week_summary(sessions,acts);st.subheader(f'Semaine {date.today().isocalendar().week} · {start.strftime("%d/%m")} → {end.strftime("%d/%m")}');st.progress(min(1,x['minute_pct']/100));st.markdown(f"## {x['minute_pct']} % du volume prévu réalisé");a,b,c=st.columns(3);a.metric('Séances',f"{x['done_sessions']}/{x['planned_sessions']}");b.metric('Heures prévues',round(x['planned_minutes']/60,1));c.metric('Heures réalisées',round((x['done_minutes']+x['activity_minutes'])/60,1));st.caption(f"Distance prévue {x['planned_km']} km · réalisée {x['done_km']} km · charge activités {x['load']}")
 with st.expander('⚙️ Générateur hebdomadaire'):
  st.caption('Le moteur place les séances autour des gardes et activités fixes, espace les charges intenses et considère le rugby comme une séance dure.')
  c1,c2=st.columns(2)
  if c1.button('Générer cette semaine',use_container_width=True):
   r=generate_week(start);st.success(r['message']);st.rerun()
  if c2.button('Recalculer cette semaine',use_container_width=True):
   r=generate_week(start,replace=True);st.success(r['message']);st.rerun()
  st.warning('La génération complète crée le plan jusqu’au LéMan. À utiliser après avoir renseigné les contraintes connues.')
  if st.button('Générer toute la préparation → LéMan',use_container_width=True):
   r=generate_until();st.success(f"{r['created']} séances créées sur {r['weeks']} semaines");st.rerun()
 st.subheader('Timeline')
 for i in range(7):
  d=start+timedelta(days=i);st.markdown(f"**{['Lun','Mar','Mer','Jeu','Ven','Sam','Dim'][i]} {d.strftime('%d/%m')}**");day=[s for s in sessions if s['start_at'][:10]==d.isoformat()]
  if not day:st.caption('○ Pas de séance planifiée')
  for s in day:st.write(('✓' if s.get('status')=='completed' else '○')+f" {s['title']} · {s.get('duration_min') or '?'} min")

def rugby_matches_page():
 st.header('Matchs de rugby');st.caption('Un match est traité comme une contrainte fixe et une charge intense. Le générateur évite donc de placer une autre séance dure le même jour et protège les séances clés autour du match.')
 with st.form('rugby_match_add'):
  d=st.date_input('Date du match');start=st.time_input('Heure de début');dur=st.number_input('Durée / bloc mobilisé (min)',60,360,120,15);title=st.text_input('Adversaire / titre','Match de rugby');notes=st.text_area('Notes')
  if st.form_submit_button('Ajouter le match',use_container_width=True):
   execute('INSERT INTO constraints(event_date,event_type,title,duration_min,intensity,fixed,notes) VALUES(?,?,?,?,?,?,?)',(d.isoformat(),'rugby_match',title,dur,'high',1,f"Début {start.strftime('%H:%M')} · {notes}"));st.success('Match ajouté. Les prochaines générations hebdomadaires en tiendront compte.');st.rerun()
 rows=query("SELECT * FROM constraints WHERE event_type='rugby_match' ORDER BY event_date")
 for r in rows:
  c1,c2=st.columns([4,1]);c1.write(f"🏉 **{r['event_date'][8:10]}-{r['event_date'][5:7]}** · {r['title']} · {r['duration_min']} min")
  if c2.button('Suppr.',key=f"rm{r['id']}"):execute('DELETE FROM constraints WHERE id=?',(r['id'],));st.rerun()

def roadmap_page_legacy():
 st.header('Plan prévisionnel · Porto-Vecchio → LéMan');blocks=roadmap();today=date.today().isoformat()
 for b in blocks:
  active=b['start']<=today<=b['end'];st.write(('🟢 ' if active else '○ ')+f"**{b['name']}** · {b['start']} → {b['end']}")

def goals_page_legacy():
 st.header('Objectifs');goals=query("SELECT * FROM goals WHERE COALESCE(event_date,'')!='' ORDER BY event_date")
 for g in goals:
  try:days=(date.fromisoformat(g['event_date'])-date.today()).days
  except:days=None
  with st.expander(f"🏁 {g['name']} · {g['event_date']}"+(f" · J-{days}" if days is not None and days>=0 else '')):st.write(f"Priorité **{g.get('priority') or '—'}** · Sport **{g.get('sport') or '—'}**");st.write(g.get('qualitative_goal') or g.get('notes') or 'Objectif à préciser')

def tests_page():
 st.header('Tests physiques');rows=query('SELECT * FROM physical_tests ORDER BY test_date DESC')
 for s in suggested_tests(rows):st.warning(s)
 with st.expander('＋ Enregistrer un test',expanded=not rows):
  sport=st.selectbox('Sport',list(test_catalog()),format_func=lambda x:{'running':'Course','cycling':'Vélo','swimming':'Natation','strength':'Force'}[x]);typ=st.selectbox('Test',test_catalog()[sport]);d=st.date_input('Date',date.today());value=st.number_input('Résultat numérique',0.,10000.,0.);unit=st.text_input('Unité','');protocol=st.text_area('Protocole / conditions');rpe=st.slider('RPE',1,10,7)
  if st.button('Enregistrer le test',use_container_width=True):execute('INSERT INTO physical_tests(test_date,sport,test_type,result_value,result_unit,protocol,rpe) VALUES(?,?,?,?,?,?,?)',(d.isoformat(),sport,typ,value,unit,protocol,rpe));st.rerun()
 if rows:
  df=pd.DataFrame(rows);st.dataframe(df[['test_date','sport','test_type','result_value','result_unit']],use_container_width=True,hide_index=True);choices=sorted(set(df.test_type));chosen=st.selectbox('Courbe',choices);sub=df[df.test_type==chosen].sort_values('test_date')
  if len(sub)>1:st.line_chart(sub,x='test_date',y='result_value')

def records_page():
 st.header('Records');rows=query('SELECT * FROM personal_records ORDER BY sport,record_type,record_date DESC')
 with st.expander('＋ Ajouter un record'):
  sport=st.selectbox('Sport',['running','swimming','cycling'],key='rs');typ=st.text_input('Type (5 km, FTP, 1500 m...)');value=st.number_input('Valeur',0.,100000.,0.,key='rv');unit=st.text_input('Unité');d=st.date_input('Date',date.today(),key='rd')
  if st.button('Enregistrer record'):execute('INSERT INTO personal_records(sport,record_type,value,unit,record_date) VALUES(?,?,?,?,?)',(sport,typ,value,unit,d.isoformat()));st.rerun()
 for r in rows:st.write(f"🏅 **{r['record_type']}** · {r['value']} {r.get('unit') or ''} · {r.get('record_date') or ''}")

def road_page():
 st.header('Road to LéMan Full Distance');acts=query('SELECT * FROM activities ORDER BY start_at DESC');sports=sport_summary(acts,28);tests=query('SELECT * FROM physical_tests ORDER BY test_date DESC')
 for sport,label in [('swimming','🏊 Natation'),('cycling','🚴 Vélo'),('running','🏃 Course')]:
  x=sports.get(sport,{});st.subheader(label);st.write(f"28 jours · {round((x.get('minutes',0))/60,1)} h · {round(x.get('distance_km',0),1)} km · {x.get('sessions',0)} séances");relevant=[t for t in tests if t['sport']==sport]
  if relevant:st.caption(f"Dernier test : {relevant[0]['test_type']} · {relevant[0]['result_value']} {relevant[0].get('result_unit') or ''}")
 st.info('Les indicateurs restent factuels : volume, régularité, longues sorties et tests. Aucun score Ironman artificiel.')

def stats_page():
 st.header('Statistiques');period=st.selectbox('Période',[7,28,90,180,365],format_func=lambda x:f'{x} jours');start=(date.today()-timedelta(days=period-1)).isoformat();acts=query('SELECT * FROM activities WHERE date(start_at)>=? ORDER BY start_at',(start,));loads=load_summary(acts);sports=sport_summary(acts,period);a,b,c=st.columns(3);a.metric('Charge 7 j',loads['load7']);b.metric('Charge période',sum(v['load'] for v in sports.values()));c.metric('Heures',round(sum(v['minutes'] for v in sports.values())/60,1))
 if loads['daily']:st.line_chart(pd.DataFrame([{'date':d,'charge':v} for d,v in sorted(loads['daily'].items())]),x='date',y='charge')
 if sports:st.bar_chart(pd.DataFrame([{'sport':k,'heures':v['minutes']/60} for k,v in sports.items()]),x='sport',y='heures')
 trend=readiness_trend(query('SELECT * FROM checkins ORDER BY created_at DESC LIMIT 30'))
 if trend:st.line_chart(pd.DataFrame(trend),x='date',y='score')

from season_map import roadmap_page,goals_page
