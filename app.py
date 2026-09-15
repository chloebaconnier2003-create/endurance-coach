import streamlit as st
import pandas as pd
from datetime import datetime,date,timedelta
from db import init,query,execute
from profile import ATHLETE,GOALS
from engine import decision,srpe,short_plan

st.set_page_config(page_title="Endurance Coach",page_icon="🏊",layout="wide",initial_sidebar_state="expanded")
init()
if not query("SELECT id FROM goals LIMIT 1"):
    for g in GOALS: execute("INSERT INTO goals(name,event_date,sport,kind,priority,notes) VALUES(?,?,?,?,?,?)",g)

st.markdown("""<style>.block-container{max-width:1100px;padding-top:1.2rem}div[data-testid='stMetric']{border:1px solid rgba(128,128,128,.25);padding:12px;border-radius:14px}.stButton button{border-radius:12px;min-height:42px}</style>""",unsafe_allow_html=True)

def checkin():
    r=query("SELECT * FROM checkins WHERE date(created_at)=? ORDER BY created_at DESC LIMIT 1",(date.today().isoformat(),)); return r[0] if r else None
def session():
    r=query("SELECT * FROM sessions WHERE date(start_at)=? AND status='planned' ORDER BY start_at LIMIT 1",(date.today().isoformat(),)); return r[0] if r else None
def shift():
    r=query("SELECT * FROM shifts WHERE end_at<=? ORDER BY end_at DESC LIMIT 1",(datetime.now().isoformat(timespec='minutes'),))
    if not r:return None
    x=r[0]; x['hours_since']=(datetime.now()-datetime.fromisoformat(x['end_at'])).total_seconds()/3600; return x
def rugby_recent():
    since=(datetime.now()-timedelta(hours=36)).isoformat(timespec='minutes'); return bool(query("SELECT id FROM activities WHERE sport='rugby' AND start_at>=? LIMIT 1",(since,)))

st.title("Endurance Coach")
st.caption("Préparation adaptative multisport — objectif LéMan Full Distance 2027")
nav=st.sidebar.radio("Menu",["🏠 Aujourd'hui","🗓️ Calendrier","🎯 Objectifs","📈 Progression","💬 Coach","👤 Profil","➕ Ajouter"])

if nav=="🏠 Aujourd'hui":
    ci=checkin(); ps=session(); dec,score,status,why,action=decision(ci,ps,shift(),rugby_recent())
    a,b,c=st.columns(3); a.metric("État",status); b.metric("Readiness",f"{score}/100"); c.metric("Décision",dec)
    if ps:
        st.subheader("Séance du jour"); st.markdown(f"### {ps['title']}"); st.write(f"**{ps['sport'].title()} · {ps['duration_min']} min · {ps['priority']} · {ps['intensity']}**"); st.write(ps['objective'] or '')
    else: st.info("Aucune séance planifiée aujourd'hui.")
    st.write("**Pourquoi ?**",why); st.success("Adaptation : "+action)
    st.divider(); st.subheader("Check-in rapide")
    with st.form("daily"):
        c1,c2,c3=st.columns(3); sleep=c1.number_input("Sommeil (h)",0.0,14.0,7.0,.5); fatigue=c2.slider("Fatigue",1,5,3); motivation=c3.slider("Motivation",1,5,3); quality=c1.slider("Qualité sommeil",1,5,3); soreness=c2.slider("Courbatures",1,5,3); stress=c3.slider("Stress",1,5,3); painloc=c1.text_input("Douleur — zone"); pain=c2.slider("Douleur",0,10,0); trend=c3.selectbox("Évolution",["stable","amélioration","aggravation"])
        if st.form_submit_button("Valider mon état"):
            execute("INSERT INTO checkins(created_at,sleep_hours,sleep_quality,fatigue,motivation,soreness,stress,pain_location,pain_score,pain_trend) VALUES(?,?,?,?,?,?,?,?,?,?)",(datetime.now().isoformat(timespec='seconds'),sleep,quality,fatigue,motivation,soreness,stress,painloc,pain,trend)); st.rerun()

elif nav=="🗓️ Calendrier":
    st.subheader("Calendrier unifié"); start=date.today()-timedelta(days=7); end=date.today()+timedelta(days=45); ev=[]
    for x in query("SELECT * FROM shifts WHERE date(start_at)>=? AND date(start_at)<=?",(start.isoformat(),end.isoformat())): ev.append([x['start_at'][:10],'Travail','',x['shift_type'],''])
    for x in query("SELECT * FROM sessions WHERE date(start_at)>=? AND date(start_at)<=?",(start.isoformat(),end.isoformat())): ev.append([x['start_at'][:10],'Planifié',x['sport'],x['title'],x['duration_min']])
    for x in query("SELECT * FROM activities WHERE date(start_at)>=? AND date(start_at)<=?",(start.isoformat(),end.isoformat())): ev.append([x['start_at'][:10],'Réalisé',x['sport'],x['title'],x['duration_min']])
    for x in query("SELECT * FROM goals WHERE event_date!='' AND event_date>=? AND event_date<=?",(start.isoformat(),end.isoformat())): ev.append([x['event_date'],'Objectif',x['sport'],x['name'],''])
    if ev: st.dataframe(pd.DataFrame(ev,columns=['Date','Type','Sport','Événement','Durée']).sort_values(['Date','Type']),hide_index=True,use_container_width=True)
    else: st.info("Calendrier vide dans cette fenêtre.")
    future=query("SELECT * FROM goals WHERE event_date!='' AND event_date>=? ORDER BY event_date LIMIT 1",(date.today().isoformat(),))
    if future:
        g=future[0]; st.subheader("Plan automatique — 14 jours"); st.write(f"Prochain objectif : **{g['name']} — {g['event_date']}**")
        if st.button("Générer / régénérer mon plan"):
            execute("DELETE FROM sessions WHERE source='auto' AND date(start_at)>=?",(date.today().isoformat(),))
            for s in short_plan(g['name'],date.fromisoformat(g['event_date'])): execute("INSERT INTO sessions(start_at,sport,title,duration_min,priority,intensity,objective,source) VALUES(?,?,?,?,?,?,?,'auto')",(s['date'].isoformat()+'T18:00',s['sport'],s['title'],s['duration'],s['priority'],s['intensity'],s['objective']))
            st.success("Plan généré. Le moteur quotidien l'adaptera à tes gardes et à ta récupération.")

elif nav=="🎯 Objectifs":
    st.subheader("Objectifs & missions")
    for g in query("SELECT * FROM goals ORDER BY CASE WHEN event_date='' THEN 1 ELSE 0 END,event_date"):
        with st.container(border=True):
            a,b=st.columns([3,1]); a.markdown(f"### {g['name']}"); a.write(f"{g['sport']} · {g['kind']} · priorité {g['priority']}"); a.caption(g['notes'] or ''); b.write(g['event_date'] or 'Date à définir')

elif nav=="📈 Progression":
    st.subheader("Charge & historique"); acts=query("SELECT * FROM activities ORDER BY start_at")
    if acts:
        df=pd.DataFrame(acts); df['Charge sRPE']=df.apply(lambda r:srpe(r['duration_min'],r['rpe']),axis=1); df['Jour']=pd.to_datetime(df['start_at']).dt.date; st.line_chart(df.groupby('Jour')['Charge sRPE'].sum()); a,b,c=st.columns(3); a.metric('Activités',len(df)); b.metric('Temps total',f"{df['duration_min'].sum()/60:.1f} h"); c.metric('Charge totale',round(df['Charge sRPE'].sum())); st.dataframe(df[['start_at','sport','title','duration_min','distance_km','elevation_m','rpe','pain','Charge sRPE']],hide_index=True,use_container_width=True); st.download_button('Exporter CSV',df.to_csv(index=False).encode(),'activities.csv','text/csv')
    else: st.info("Les graphiques apparaîtront après tes premières activités.")

elif nav=="💬 Coach":
    ci=checkin(); ps=session(); dec,score,status,why,action=decision(ci,ps,shift(),rugby_recent()); st.subheader("Coach"); st.markdown(f"### Recommandation actuelle : {dec}"); st.write(why); st.success(action); st.caption("Le chat IA conversationnel connecté sera ajouté dans une prochaine version.")

elif nav=="👤 Profil":
    st.subheader("Athlete Model V1")
    for sec,data in ATHLETE.items():
        with st.expander(sec,expanded=True):
            for k,v in data.items(): st.write(f"**{k} :** {v}")

elif nav=="➕ Ajouter":
    tabs=st.tabs(["Activité","Garde","Objectif","Séance"])
    with tabs[0]:
        with st.form('activity'):
            dt=st.text_input('Date/heure',datetime.now().isoformat(timespec='minutes')); sport=st.selectbox('Sport',['running','trail','cycling','swimming','rugby','dance','strength','other']); title=st.text_input('Titre'); duration=st.number_input('Durée (min)',1,1000,60); distance=st.number_input('Distance (km)',0.0,500.0,0.0,.1); elev=st.number_input('D+ (m)',0,10000,0,10); rpe=st.slider('RPE',1,10,4); pain=st.slider('Douleur après',0,10,0)
            if st.form_submit_button('Enregistrer'): execute("INSERT INTO activities(start_at,sport,title,duration_min,distance_km,elevation_m,rpe,pain) VALUES(?,?,?,?,?,?,?,?)",(dt,sport,title,duration,distance,elev,rpe,pain)); st.success('Activité enregistrée.')
    with tabs[1]:
        with st.form('shiftform'):
            typ=st.selectbox('Type',['24h','12h_jour','12h_nuit']); start=st.text_input('Début',datetime.now().replace(hour=8,minute=0).isoformat(timespec='minutes')); end=st.text_input('Fin',(datetime.now()+timedelta(days=1)).replace(hour=8,minute=0).isoformat(timespec='minutes'))
            if st.form_submit_button('Ajouter la garde'): execute("INSERT INTO shifts(start_at,end_at,shift_type) VALUES(?,?,?)",(start,end,typ)); st.success('Garde ajoutée.')
    with tabs[2]:
        with st.form('goalform'):
            name=st.text_input('Objectif / mission'); d=st.text_input('Date YYYY-MM-DD (facultatif)'); sport=st.text_input('Sport','cycling'); kind=st.selectbox('Type',['competition','mission','test','training_goal']); priority=st.selectbox('Priorité',['A','A/B','B','C','D']); notes=st.text_area('Détails')
            if st.form_submit_button('Créer'): execute("INSERT INTO goals(name,event_date,sport,kind,priority,notes) VALUES(?,?,?,?,?,?)",(name,d,sport,kind,priority,notes)); st.success('Objectif ajouté.')
    with tabs[3]:
        with st.form('sessionform'):
            dt=st.text_input('Date/heure',datetime.now().replace(hour=18,minute=0).isoformat(timespec='minutes')); sport=st.selectbox('Sport',['running','trail','cycling','swimming','strength']); title=st.text_input('Nom','Endurance facile'); duration=st.number_input('Durée',10,600,60); priority=st.selectbox('Priorité',['P0','P1','P2','P3'],index=2); intensity=st.selectbox('Intensité',['easy','moderate','threshold','vo2','hard']); objective=st.text_area('Objectif physiologique')
            if st.form_submit_button('Planifier'): execute("INSERT INTO sessions(start_at,sport,title,duration_min,priority,intensity,objective) VALUES(?,?,?,?,?,?,?)",(dt,sport,title,duration,priority,intensity,objective)); st.success('Séance ajoutée.')

st.divider(); st.caption("Endurance Coach V2 · outil de planification sportive, ne remplace pas un avis médical.")
