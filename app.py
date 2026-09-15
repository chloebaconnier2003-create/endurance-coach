import streamlit as st
import pandas as pd
from datetime import datetime,date,time,timedelta
from db import init,query,execute
from profile import ATHLETE,GOALS
from engine import decision,srpe
from scheduler import build_plan

st.set_page_config(page_title='Endurance Coach',page_icon='⚡',layout='wide',initial_sidebar_state='collapsed'); init()
if not query('SELECT id FROM goals LIMIT 1'):
    for g in GOALS: execute('INSERT INTO goals(name,event_date,sport,kind,priority,notes) VALUES(?,?,?,?,?,?)',g)
st.markdown('''<style>.block-container{max-width:960px;padding-top:1rem;padding-bottom:5rem}.hero{padding:1.1rem 1.2rem;border-radius:22px;background:linear-gradient(135deg,#15171c,#252a33);color:white;margin-bottom:1rem}.card{padding:1rem;border:1px solid rgba(128,128,128,.22);border-radius:18px;margin:.6rem 0}.eyebrow{font-size:.76rem;opacity:.7;letter-spacing:.08em}.big{font-size:2.2rem;font-weight:750}.pill{display:inline-block;padding:.25rem .6rem;border-radius:999px;background:rgba(128,128,128,.14);font-size:.82rem;margin-right:.3rem}.stButton button{border-radius:14px;min-height:44px;font-weight:600}@media(max-width:640px){.block-container{padding-left:.7rem;padding-right:.7rem}}</style>''',unsafe_allow_html=True)

def one(sql,args=()):
    r=query(sql,args); return r[0] if r else None
def next_goal(): return one("SELECT * FROM goals WHERE COALESCE(event_date,'')!='' AND event_date>=? ORDER BY event_date LIMIT 1",(date.today().isoformat(),))
def today_session(): return one("SELECT * FROM sessions WHERE date(start_at)=? AND status='planned' ORDER BY start_at LIMIT 1",(date.today().isoformat(),))
def checkin(): return one('SELECT * FROM checkins WHERE date(created_at)=? ORDER BY created_at DESC LIMIT 1',(date.today().isoformat(),))
def last_shift():
    x=one('SELECT * FROM shifts WHERE end_at<=? ORDER BY end_at DESC LIMIT 1',(datetime.now().isoformat(timespec='minutes'),))
    if x:
        try:x['hours_since']=(datetime.now()-datetime.fromisoformat(x['end_at'])).total_seconds()/3600
        except:x['hours_since']=999
    return x
def rugby_recent(): return bool(query("SELECT id FROM activities WHERE sport='rugby' AND start_at>=? LIMIT 1",((datetime.now()-timedelta(hours=36)).isoformat(timespec='minutes'),)))
def ico(s): return {'running':'🏃','trail':'⛰️','cycling':'🚴','swimming':'🏊','rugby':'🏉','dance':'💃','strength':'💪'}.get(str(s or '').lower(),'⚡')
def dtiso(d,t): return datetime.combine(d,t).isoformat(timespec='minutes')

g=next_goal(); countdown=(date.fromisoformat(g['event_date'])-date.today()).days if g else None
st.markdown(f"<div class='hero'><div class='eyebrow'>ENDURANCE COACH V4.1 · {date.today().strftime('%d/%m/%Y')}</div><h2>{'Objectif : '+g['name'] if g else 'Ton coach adaptatif'}</h2><div>{'J-'+str(countdown) if countdown is not None else 'Ajoute la date de ton prochain objectif'}</div></div>",unsafe_allow_html=True)
nav=st.segmented_control('Navigation',['Aujourd’hui','Planning','Progression','Coach','Ajouter','Plus'],default='Aujourd’hui',label_visibility='collapsed') or 'Aujourd’hui'

if nav=='Aujourd’hui':
    try:
        ci=checkin(); ps=today_session(); dec,score,status,why,action=decision(ci,ps,last_shift(),rugby_recent()); a,b=st.columns([1,2])
        with a: st.markdown(f"<div class='card'><div class='eyebrow'>ÉTAT DU JOUR</div><div class='big'>{score}</div><b>{status}</b></div>",unsafe_allow_html=True)
        with b: st.markdown(f"<div class='card'><div class='eyebrow'>COACH</div><h3>{dec.replace('_',' ').title()}</h3><span>{why}</span></div>",unsafe_allow_html=True)
        if ps: st.markdown(f"<div class='card'><div class='eyebrow'>{ico(ps['sport'])} SÉANCE DU JOUR</div><h2>{ps['title']}</h2><span class='pill'>{ps['duration_min'] or '?'} min</span><span class='pill'>{ps['sport']}</span><p>{ps['objective'] or ''}</p><b>{action}</b></div>",unsafe_allow_html=True)
        else: st.info('Pas de séance planifiée aujourd’hui.')
        st.subheader('Prochains jours')
        for x in query("SELECT * FROM sessions WHERE date(start_at)>? AND date(start_at)<=? AND status='planned' ORDER BY start_at LIMIT 5",(date.today().isoformat(),(date.today()+timedelta(days=7)).isoformat())): st.write(f"**{x['start_at'][8:10]}/{x['start_at'][5:7]}** · {ico(x['sport'])} {x['title']} · {x['duration_min'] or '?'} min")
        if not ci:
            with st.expander('☀️ Faire mon check-in du jour',expanded=True):
                with st.form('checkin'):
                    c1,c2=st.columns(2); sleep=c1.number_input('Sommeil (h)',0.0,14.0,7.0,.5); fatigue=c2.slider('Fatigue',1,5,3); quality=c1.slider('Qualité du sommeil',1,5,3); motivation=c2.slider('Motivation',1,5,3); soreness=c1.slider('Courbatures',1,5,3); stress=c2.slider('Stress',1,5,3); painloc=c1.text_input('Zone douloureuse'); pain=c2.slider('Douleur',0,10,0); trend=st.selectbox('Évolution de la douleur',['stable','amélioration','aggravation'])
                    if st.form_submit_button('Enregistrer',use_container_width=True): execute('INSERT INTO checkins(created_at,sleep_hours,sleep_quality,fatigue,motivation,soreness,stress,pain_location,pain_score,pain_trend) VALUES(?,?,?,?,?,?,?,?,?,?)',(datetime.now().isoformat(timespec='seconds'),sleep,quality,fatigue,motivation,soreness,stress,painloc,pain,trend)); st.rerun()
    except Exception as e: st.error('Le tableau du jour a rencontré un problème. La V4.1 protège maintenant le reste de l’application.'); st.caption(str(e))

elif nav=='Planning':
    st.header('Planning adaptatif')
    try:
        future=next_goal()
        if future:
            st.write(f"Prochain objectif : **{future['name']}** · {future['event_date']}")
            if st.button('⚡ Recalculer intelligemment les 14 prochains jours',use_container_width=True):
                horizon=(date.today()+timedelta(days=14)).isoformat(); shifts=query('SELECT * FROM shifts WHERE date(start_at)<=? AND date(end_at)>=?',(horizon,(date.today()-timedelta(days=1)).isoformat())); cons=query('SELECT * FROM constraints WHERE event_date>=? AND event_date<=?',(date.today().isoformat(),horizon)); result=build_plan(future,shifts,cons)
                execute("DELETE FROM sessions WHERE source='auto_v4' AND date(start_at)>=?",(date.today().isoformat(),))
                for s in result['sessions']: execute("INSERT INTO sessions(start_at,sport,title,duration_min,priority,intensity,objective,source) VALUES(?,?,?,?,?,?,?,'auto_v4')",(s['date'].isoformat()+'T18:00',s['sport'],s['title'],s['duration'],s['priority'],s['intensity'],s['objective']))
                st.success(f"{len(result['sessions'])} séances placées · phase {result['phase']}"); st.rerun()
        ev=[]; end=(date.today()+timedelta(days=30)).isoformat()
        for x in query('SELECT * FROM shifts WHERE date(start_at)>=? AND date(start_at)<=?',(date.today().isoformat(),end)): ev.append([x['start_at'][:10],'🚑','Garde '+x['shift_type'],'Travail'])
        for x in query('SELECT * FROM constraints WHERE event_date>=? AND event_date<=?',(date.today().isoformat(),end)): ev.append([x['event_date'],'📌',x['title'],'Fixe'])
        for x in query('SELECT * FROM sessions WHERE date(start_at)>=? AND date(start_at)<=?',(date.today().isoformat(),end)): ev.append([x['start_at'][:10],ico(x['sport']),x['title'],f"{x['duration_min'] or '?'} min"])
        if ev: st.dataframe(pd.DataFrame(sorted(ev),columns=['Date','','Événement','Info']),hide_index=True,use_container_width=True)
        else: st.info('Calendrier vide pour les 30 prochains jours. Commence par Ajouter.')
    except Exception as e: st.error('Impossible de calculer le planning pour le moment.'); st.caption(str(e))

elif nav=='Progression':
    st.header('Progression'); acts=query('SELECT * FROM activities ORDER BY start_at')
    if acts:
        df=pd.DataFrame(acts); df['Charge']=df.apply(lambda r:srpe(r.get('duration_min'),r.get('rpe')),axis=1); df['Jour']=pd.to_datetime(df['start_at']).dt.date; recent=df[pd.to_datetime(df['start_at'])>=pd.Timestamp.now()-pd.Timedelta(days=7)]; a,b,c=st.columns(3); a.metric('Charge 7 j',round(recent['Charge'].sum())); b.metric('Temps 7 j',f"{recent['duration_min'].fillna(0).sum()/60:.1f} h"); c.metric('Séances',len(recent)); st.line_chart(df.groupby('Jour')['Charge'].sum())
    else: st.info('Les graphiques apparaîtront avec tes activités.')

elif nav=='Coach':
    st.header('Coach')
    try:
        ci=checkin(); ps=today_session(); dec,score,status,why,action=decision(ci,ps,last_shift(),rugby_recent()); st.markdown(f'### {dec.replace("_"," ").title()}'); st.write(why); st.success(action); st.text_area('Message au coach',placeholder='Ex. J’ai une garde de nuit jeudi et rugby vendredi. Que dois-je modifier ?'); st.caption('Le moteur de décision fonctionne ; la conversation IA qui modifiera automatiquement le calendrier sera la prochaine couche.')
    except Exception as e: st.error('Le coach a rencontré un problème de données.'); st.caption(str(e))

elif nav=='Ajouter':
    st.header('Ajouter au calendrier'); kind=st.segmented_control('Type',['🏋️ Séance','🚑 Garde','🏉 Sport fixe','🏁 Objectif','✅ Activité réalisée'],default='🏋️ Séance')
    if kind=='🏋️ Séance':
        st.caption('Planifie une séance en quelques choix. Les réglages avancés sont optionnels.')
        with st.form('newsession'):
            sport=st.selectbox('Sport',['running','cycling','swimming','trail','strength'],format_func=lambda x:{'running':'🏃 Course','cycling':'🚴 Vélo','swimming':'🏊 Natation','trail':'⛰️ Trail','strength':'💪 Renforcement'}[x]); c1,c2=st.columns(2); d=c1.date_input('Jour',date.today()); t=c2.time_input('Heure',time(18,0)); title=st.text_input('Nom de la séance',placeholder='Ex. Endurance facile'); c3,c4=st.columns(2); duration=c3.number_input('Durée (min)',10,600,60,5); intensity=c4.selectbox('Intensité',['easy','moderate','threshold','hard'],format_func=lambda x:{'easy':'Facile','moderate':'Modérée','threshold':'Seuil / soutenue','hard':'Difficile'}[x]); objective=st.text_area('Consignes / objectif',placeholder='Optionnel — ex. rester en aisance respiratoire'); priority=st.select_slider('Importance',['P3','P2','P1','P0'],value='P2',help='P0 = séance clé, P3 = facilement sacrifiable')
            if st.form_submit_button('➕ Ajouter la séance',use_container_width=True): execute('INSERT INTO sessions(start_at,sport,title,duration_min,priority,intensity,objective) VALUES(?,?,?,?,?,?,?)',(dtiso(d,t),sport,title or 'Séance '+sport,duration,priority,intensity,objective)); st.success('Séance ajoutée au planning.')
    elif kind=='🚑 Garde':
        with st.form('guard'):
            typ=st.selectbox('Type de garde',['24h','12h_jour','12h_nuit']); d=st.date_input('Jour de début',date.today()); defaults={'24h':(time(8),date.today()+timedelta(days=1),time(8)),'12h_jour':(time(7),date.today(),time(20)),'12h_nuit':(time(19),date.today()+timedelta(days=1),time(8))}; sh,ed,eh=defaults[typ]; c1,c2=st.columns(2); start_t=c1.time_input('Début',sh); end_d=c2.date_input('Jour de fin',d+(timedelta(days=1) if typ in {'24h','12h_nuit'} else timedelta(0))); end_t=st.time_input('Fin',eh)
            if st.form_submit_button('🚑 Ajouter la garde',use_container_width=True): execute('INSERT INTO shifts(start_at,end_at,shift_type) VALUES(?,?,?)',(dtiso(d,start_t),dtiso(end_d,end_t),typ)); st.success('Garde ajoutée.')
    elif kind=='🏉 Sport fixe':
        with st.form('fixed'):
            typ=st.selectbox('Événement',['rugby_training','rugby_match','dance','personal','other'],format_func=lambda x:{'rugby_training':'🏉 Entraînement rugby','rugby_match':'🏉 Match rugby','dance':'💃 Danse','personal':'📌 Objectif personnel','other':'📅 Autre'}[x]); d=st.date_input('Jour',date.today()); title=st.text_input('Nom',value='Rugby' if 'rugby' in typ else 'Danse' if typ=='dance' else ''); c1,c2=st.columns(2); duration=c1.number_input('Durée (min)',15,360,90,15); intensity=c2.selectbox('Charge',['easy','moderate','hard'],format_func=lambda x:{'easy':'Faible','moderate':'Moyenne','hard':'Élevée'}[x])
            if st.form_submit_button('📌 Ajouter',use_container_width=True): execute('INSERT INTO constraints(event_date,event_type,title,duration_min,intensity,fixed) VALUES(?,?,?,?,?,1)',(d.isoformat(),typ,title or typ,duration,intensity)); st.success('Événement ajouté et pris en compte par le moteur.')
    elif kind=='🏁 Objectif':
        with st.form('goal'):
            name=st.text_input('Nom de l’objectif'); d=st.date_input('Date',date.today()+timedelta(days=30)); sport=st.selectbox('Sport',['running','trail','cycling','triathlon','other']); priority=st.selectbox('Priorité',['A','A/B','B','C']); notes=st.text_area('Détails')
            if st.form_submit_button('🏁 Ajouter l’objectif',use_container_width=True): execute('INSERT INTO goals(name,event_date,sport,kind,priority,notes) VALUES(?,?,?,?,?,?)',(name,d.isoformat(),sport,'competition',priority,notes)); st.success('Objectif ajouté.')
    else:
        with st.form('activity'):
            sport=st.selectbox('Sport',['running','trail','cycling','swimming','rugby','dance','strength','other']); c1,c2=st.columns(2); d=c1.date_input('Jour',date.today()); t=c2.time_input('Heure',datetime.now().time().replace(second=0,microsecond=0)); title=st.text_input('Titre'); c3,c4=st.columns(2); duration=c3.number_input('Durée (min)',1,1000,60); rpe=c4.slider('Difficulté ressentie /10',1,10,4); distance=st.number_input('Distance (km)',0.0,500.0,0.0,.1); pain=st.slider('Douleur après /10',0,10,0)
            if st.form_submit_button('✅ Enregistrer',use_container_width=True): execute('INSERT INTO activities(start_at,sport,title,duration_min,distance_km,rpe,pain) VALUES(?,?,?,?,?,?,?)',(dtiso(d,t),sport,title,duration,distance,rpe,pain)); st.success('Activité enregistrée.')

else:
    st.header('Profil & objectifs'); tab1,tab2=st.tabs(['Objectifs','Profil athlète'])
    with tab1:
        for goal in query("SELECT * FROM goals ORDER BY CASE WHEN COALESCE(event_date,'')='' THEN 1 ELSE 0 END,event_date"):
            with st.container(border=True): st.write(f"**{goal['name']}** · {goal['priority']} · {goal['event_date'] or 'date à définir'}"); st.caption(goal['notes'] or '')
    with tab2:
        for sec,data in ATHLETE.items():
            with st.expander(sec):
                for k,v in data.items(): st.write(f'**{k} :** {v}')
st.caption('Endurance Coach V4.1 · prototype adaptatif · ne remplace pas un avis médical.')
