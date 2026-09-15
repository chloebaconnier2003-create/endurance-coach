import streamlit as st
import pandas as pd
from datetime import datetime,date,timedelta
from db import init,query,execute
from profile import ATHLETE,GOALS
from engine import decision,srpe,short_plan

st.set_page_config(page_title="Endurance Coach",page_icon="⚡",layout="wide",initial_sidebar_state="collapsed")
init()
if not query("SELECT id FROM goals LIMIT 1"):
    for g in GOALS: execute("INSERT INTO goals(name,event_date,sport,kind,priority,notes) VALUES(?,?,?,?,?,?)",g)

st.markdown('''<style>
.block-container{max-width:980px;padding-top:1rem;padding-bottom:5rem}.hero{padding:1.1rem 1.2rem;border-radius:22px;background:linear-gradient(135deg,#15171c,#252a33);color:white;margin-bottom:1rem}.eyebrow{font-size:.78rem;opacity:.7;text-transform:uppercase;letter-spacing:.08em}.hero h1{font-size:1.7rem;margin:.2rem 0}.card{padding:1rem 1.1rem;border:1px solid rgba(128,128,128,.22);border-radius:20px;margin:.65rem 0}.session{padding:1.2rem;border-radius:22px;background:rgba(128,128,128,.08);margin:.7rem 0}.bigscore{font-size:2.3rem;font-weight:750;line-height:1}.muted{opacity:.68}.pill{display:inline-block;padding:.25rem .6rem;border-radius:999px;background:rgba(128,128,128,.15);font-size:.82rem;margin-right:.3rem}.stButton button{border-radius:14px;min-height:44px;font-weight:600}div[data-testid="stMetric"]{border:1px solid rgba(128,128,128,.18);padding:10px;border-radius:16px}@media(max-width:640px){.block-container{padding-left:.75rem;padding-right:.75rem}.hero h1{font-size:1.45rem}.bigscore{font-size:2rem}}
</style>''',unsafe_allow_html=True)

def checkin():
    r=query("SELECT * FROM checkins WHERE date(created_at)=? ORDER BY created_at DESC LIMIT 1",(date.today().isoformat(),)); return r[0] if r else None
def today_session():
    r=query("SELECT * FROM sessions WHERE date(start_at)=? AND status='planned' ORDER BY start_at LIMIT 1",(date.today().isoformat(),)); return r[0] if r else None
def last_shift():
    r=query("SELECT * FROM shifts WHERE end_at<=? ORDER BY end_at DESC LIMIT 1",(datetime.now().isoformat(timespec='minutes'),))
    if not r:return None
    x=r[0]; x['hours_since']=(datetime.now()-datetime.fromisoformat(x['end_at'])).total_seconds()/3600; return x
def rugby_recent():
    since=(datetime.now()-timedelta(hours=36)).isoformat(timespec='minutes'); return bool(query("SELECT id FROM activities WHERE sport='rugby' AND start_at>=? LIMIT 1",(since,)))
def next_goal():
    r=query("SELECT * FROM goals WHERE event_date!='' AND event_date>=? ORDER BY event_date LIMIT 1",(date.today().isoformat(),)); return r[0] if r else None
def sport_icon(s):
    return {'running':'🏃','trail':'⛰️','cycling':'🚴','swimming':'🏊','rugby':'🏉','dance':'💃','strength':'💪'}.get((s or '').lower(),'⚡')
def decision_label(x):
    return {'EXECUTE':'Séance maintenue','ADJUST':'Séance adaptée','MOVE':'Séance déplacée','REPLACE':'Séance remplacée','RECOVERY':'Récupération','REST':'Repos','MEDICAL_FLAG':'Vigilance douleur'}.get(x,x)

g=next_goal(); days=(date.fromisoformat(g['event_date'])-date.today()).days if g else None
st.markdown(f'''<div class="hero"><div class="eyebrow">ENDURANCE COACH · {date.today().strftime('%d/%m/%Y')}</div><h1>{'Objectif : '+g['name'] if g else 'Construis ta prochaine étape'}</h1><div>{'J-'+str(days) if days is not None else 'Ajoute une date pour activer le compte à rebours'}</div></div>''',unsafe_allow_html=True)

nav=st.segmented_control("Navigation",["Aujourd’hui","Planning","Progression","Coach","Plus"],default="Aujourd’hui",label_visibility="collapsed")
if not nav: nav="Aujourd’hui"

if nav=="Aujourd’hui":
    ci=checkin(); ps=today_session(); dec,score,status,why,action=decision(ci,ps,last_shift(),rugby_recent())
    a,b=st.columns([1,2])
    with a:
        st.markdown(f'''<div class="card"><div class="eyebrow">ÉTAT DU JOUR</div><div class="bigscore">{score}</div><b>{status}</b><br><span class="muted">Readiness interne</span></div>''',unsafe_allow_html=True)
    with b:
        st.markdown(f'''<div class="card"><div class="eyebrow">DÉCISION DU COACH</div><h3>{decision_label(dec)}</h3><span class="muted">{why}</span></div>''',unsafe_allow_html=True)
    if ps:
        st.markdown(f'''<div class="session"><div class="eyebrow">{sport_icon(ps['sport'])} SÉANCE DU JOUR</div><h2>{ps['title']}</h2><span class="pill">{ps['duration_min']} min</span><span class="pill">{ps['sport'].title()}</span><p>{ps['objective'] or ''}</p><b>{action}</b></div>''',unsafe_allow_html=True)
    else:
        st.info("Pas de séance planifiée aujourd’hui. Le moteur privilégie récupération ou activité facile selon ton état.")
    st.subheader("Les prochains jours")
    upcoming=query("SELECT * FROM sessions WHERE date(start_at)>? AND date(start_at)<=? AND status='planned' ORDER BY start_at LIMIT 4",(date.today().isoformat(),(date.today()+timedelta(days=7)).isoformat()))
    shifts=query("SELECT * FROM shifts WHERE date(start_at)>=? AND date(start_at)<=? ORDER BY start_at LIMIT 3",(date.today().isoformat(),(date.today()+timedelta(days=7)).isoformat()))
    items=[(x['start_at'][:10],sport_icon(x['sport']),x['title'],f"{x['duration_min']} min") for x in upcoming]+[(x['start_at'][:10],'🚑',f"Garde {x['shift_type']}",'Travail') for x in shifts]
    for d,ico,title,meta in sorted(items)[:5]: st.markdown(f"**{d[8:10]}/{d[5:7]}** · {ico} {title} · *{meta}*")
    if not ci:
        st.divider(); st.subheader("Check-in du matin · 30 secondes")
        with st.form("daily"):
            c1,c2=st.columns(2); sleep=c1.number_input("Sommeil (h)",0.0,14.0,7.0,.5); quality=c2.slider("Qualité sommeil",1,5,3); fatigue=c1.slider("Fatigue",1,5,3); motivation=c2.slider("Motivation",1,5,3); soreness=c1.slider("Courbatures",1,5,3); stress=c2.slider("Stress",1,5,3); painloc=c1.text_input("Douleur — zone"); pain=c2.slider("Douleur",0,10,0); trend=st.selectbox("Évolution",["stable","amélioration","aggravation"])
            if st.form_submit_button("Valider mon état",use_container_width=True): execute("INSERT INTO checkins(created_at,sleep_hours,sleep_quality,fatigue,motivation,soreness,stress,pain_location,pain_score,pain_trend) VALUES(?,?,?,?,?,?,?,?,?,?)",(datetime.now().isoformat(timespec='seconds'),sleep,quality,fatigue,motivation,soreness,stress,painloc,pain,trend)); st.rerun()
    else: st.caption("✓ Check-in du jour enregistré")

elif nav=="Planning":
    st.header("Planning")
    future=next_goal()
    if future:
        st.write(f"Prochain objectif : **{future['name']}** · {future['event_date']}")
        if st.button("⚡ Générer les 14 prochains jours",use_container_width=True):
            execute("DELETE FROM sessions WHERE source='auto' AND date(start_at)>=?",(date.today().isoformat(),))
            for s in short_plan(future['name'],date.fromisoformat(future['event_date'])): execute("INSERT INTO sessions(start_at,sport,title,duration_min,priority,intensity,objective,source) VALUES(?,?,?,?,?,?,?,'auto')",(s['date'].isoformat()+'T18:00',s['sport'],s['title'],s['duration'],s['priority'],s['intensity'],s['objective']))
            st.success("Plan généré. Ajoute tes gardes et sports fixes pour que le moteur les prenne en compte."); st.rerun()
    start=date.today(); end=start+timedelta(days=30); ev=[]
    for x in query("SELECT * FROM shifts WHERE date(start_at)>=? AND date(start_at)<=?",(start.isoformat(),end.isoformat())): ev.append([x['start_at'][:10],'🚑',f"Garde {x['shift_type']}",'Travail'])
    for x in query("SELECT * FROM sessions WHERE date(start_at)>=? AND date(start_at)<=?",(start.isoformat(),end.isoformat())): ev.append([x['start_at'][:10],sport_icon(x['sport']),x['title'],f"{x['duration_min']} min"])
    for x in query("SELECT * FROM goals WHERE event_date!='' AND event_date>=? AND event_date<=?",(start.isoformat(),end.isoformat())): ev.append([x['event_date'],'🏁',x['name'],'Objectif'])
    if ev: st.dataframe(pd.DataFrame(sorted(ev),columns=['Date','','Événement','Info']),hide_index=True,use_container_width=True)
    else: st.info("Aucun événement dans les 30 prochains jours.")

elif nav=="Progression":
    st.header("Progression"); acts=query("SELECT * FROM activities ORDER BY start_at")
    if acts:
        df=pd.DataFrame(acts); df['Charge']=df.apply(lambda r:srpe(r['duration_min'],r['rpe']),axis=1); df['Jour']=pd.to_datetime(df['start_at']).dt.date; cutoff=pd.Timestamp.now()-pd.Timedelta(days=7); recent=df[pd.to_datetime(df['start_at'])>=cutoff]
        a,b,c=st.columns(3); a.metric('Charge 7 j',round(recent['Charge'].sum())); b.metric('Temps 7 j',f"{recent['duration_min'].sum()/60:.1f} h"); c.metric('Séances 7 j',len(recent)); st.subheader("Charge quotidienne"); st.line_chart(df.groupby('Jour')['Charge'].sum()); st.subheader("Répartition"); by=df.groupby('sport')['duration_min'].sum().sort_values(ascending=False)/60; st.bar_chart(by); st.dataframe(df[['start_at','sport','title','duration_min','distance_km','elevation_m','rpe','pain','Charge']].sort_values('start_at',ascending=False),hide_index=True,use_container_width=True)
    else: st.info("Ta progression apparaîtra après les premières activités enregistrées.")

elif nav=="Coach":
    ci=checkin(); ps=today_session(); dec,score,status,why,action=decision(ci,ps,last_shift(),rugby_recent()); st.header("Coach"); st.markdown(f"### {decision_label(dec)}"); st.write(why); st.success(action); st.text_area("Parle à ton coach",placeholder="Ex. J’ai mal dormi, rugby demain et ma hanche tire un peu…"); st.caption("Le dialogue IA complet sera branché dans la prochaine étape. Pour l’instant, le moteur de décision est actif.")

elif nav=="Plus":
    tab1,tab2,tab3=st.tabs(["Ajouter","Objectifs","Profil"])
    with tab1:
        choice=st.radio("Ajouter",["Activité","Garde","Objectif","Séance"],horizontal=True)
        if choice=='Activité':
            with st.form('activity'):
                dt=st.text_input('Date/heure',datetime.now().isoformat(timespec='minutes')); sport=st.selectbox('Sport',['running','trail','cycling','swimming','rugby','dance','strength','other']); title=st.text_input('Titre'); duration=st.number_input('Durée (min)',1,1000,60); distance=st.number_input('Distance (km)',0.0,500.0,0.0,.1); elev=st.number_input('D+ (m)',0,10000,0,10); rpe=st.slider('RPE',1,10,4); pain=st.slider('Douleur après',0,10,0)
                if st.form_submit_button('Enregistrer',use_container_width=True): execute("INSERT INTO activities(start_at,sport,title,duration_min,distance_km,elevation_m,rpe,pain) VALUES(?,?,?,?,?,?,?,?)",(dt,sport,title,duration,distance,elev,rpe,pain)); st.success('Activité enregistrée.')
        elif choice=='Garde':
            with st.form('shiftform'):
                typ=st.selectbox('Type',['24h','12h_jour','12h_nuit']); start=st.text_input('Début',datetime.now().replace(hour=8,minute=0).isoformat(timespec='minutes')); end=st.text_input('Fin',(datetime.now()+timedelta(days=1)).replace(hour=8,minute=0).isoformat(timespec='minutes'))
                if st.form_submit_button('Ajouter',use_container_width=True): execute("INSERT INTO shifts(start_at,end_at,shift_type) VALUES(?,?,?)",(start,end,typ)); st.success('Garde ajoutée.')
        elif choice=='Objectif':
            with st.form('goalform'):
                name=st.text_input('Objectif / mission'); d=st.text_input('Date YYYY-MM-DD (facultatif)'); sport=st.text_input('Sport','cycling'); kind=st.selectbox('Type',['competition','mission','test','training_goal']); priority=st.selectbox('Priorité',['A','A/B','B','C','D']); notes=st.text_area('Détails')
                if st.form_submit_button('Créer',use_container_width=True): execute("INSERT INTO goals(name,event_date,sport,kind,priority,notes) VALUES(?,?,?,?,?,?)",(name,d,sport,kind,priority,notes)); st.success('Objectif ajouté.')
        else:
            with st.form('sessionform'):
                dt=st.text_input('Date/heure',datetime.now().replace(hour=18,minute=0).isoformat(timespec='minutes')); sport=st.selectbox('Sport',['running','trail','cycling','swimming','strength']); title=st.text_input('Nom','Endurance facile'); duration=st.number_input('Durée',10,600,60); priority=st.selectbox('Priorité',['P0','P1','P2','P3'],index=2); intensity=st.selectbox('Intensité',['easy','moderate','threshold','vo2','hard']); objective=st.text_area('Objectif physiologique')
                if st.form_submit_button('Planifier',use_container_width=True): execute("INSERT INTO sessions(start_at,sport,title,duration_min,priority,intensity,objective) VALUES(?,?,?,?,?,?,?)",(dt,sport,title,duration,priority,intensity,objective)); st.success('Séance ajoutée.')
    with tab2:
        for goal in query("SELECT * FROM goals ORDER BY CASE WHEN event_date='' THEN 1 ELSE 0 END,event_date"):
            with st.container(border=True): st.markdown(f"**{goal['name']}** · {goal['priority']}"); st.write(goal['event_date'] or 'Date à définir'); st.caption(goal['notes'] or '')
    with tab3:
        for sec,data in ATHLETE.items():
            with st.expander(sec):
                for k,v in data.items(): st.write(f"**{k} :** {v}")

st.caption("Endurance Coach V3 · planification sportive adaptative · ne remplace pas un avis médical.")
