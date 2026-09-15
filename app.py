import streamlit as st
import pandas as pd
from datetime import datetime,date,time,timedelta
from db import init,query,execute
from profile import ATHLETE,GOALS
from engine import decision,srpe
from scheduler import build_plan
from calendar_engine import recurring_instances,combined_constraints

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
def ico(s): return {'running':'🏃','trail':'⛰️','cycling':'🚴','swimming':'🏊','rugby':'🏉','rugby_training':'🏉','rugby_match':'🏉','dance':'💃','strength':'💪'}.get(str(s or '').lower(),'⚡')
def dtiso(d,t): return datetime.combine(d,t).isoformat(timespec='minutes')
def recurring_between(start,end):
    shifts=query('SELECT * FROM shifts WHERE date(start_at)<=? AND date(end_at)>=?',(end.isoformat(),(start-timedelta(days=1)).isoformat()))
    rules=query('SELECT * FROM recurring_rules WHERE active=1')
    return recurring_instances(rules,shifts,start,end)

g=next_goal(); countdown=(date.fromisoformat(g['event_date'])-date.today()).days if g else None
st.markdown(f"<div class='hero'><div class='eyebrow'>ENDURANCE COACH V4.2 · {date.today().strftime('%d/%m/%Y')}</div><h2>{'Objectif : '+g['name'] if g else 'Ton coach adaptatif'}</h2><div>{'J-'+str(countdown) if countdown is not None else 'Ajoute la date de ton prochain objectif'}</div></div>",unsafe_allow_html=True)
nav=st.segmented_control('Navigation',['Aujourd’hui','Planning','Progression','Coach','Ajouter','Plus'],default='Aujourd’hui',label_visibility='collapsed') or 'Aujourd’hui'

if nav=='Aujourd’hui':
    ci=checkin(); ps=today_session(); dec,score,status,why,action=decision(ci,ps,last_shift(),rugby_recent()); a,b=st.columns([1,2])
    with a: st.markdown(f"<div class='card'><div class='eyebrow'>ÉTAT DU JOUR</div><div class='big'>{score}</div><b>{status}</b></div>",unsafe_allow_html=True)
    with b: st.markdown(f"<div class='card'><div class='eyebrow'>COACH</div><h3>{dec.replace('_',' ').title()}</h3><span>{why}</span></div>",unsafe_allow_html=True)
    if ps: st.markdown(f"<div class='card'><div class='eyebrow'>{ico(ps['sport'])} SÉANCE DU JOUR</div><h2>{ps['title']}</h2><span class='pill'>{ps['duration_min'] or '?'} min</span><p>{ps['objective'] or ''}</p><b>{action}</b></div>",unsafe_allow_html=True)
    else: st.info('Pas de séance planifiée aujourd’hui.')
    st.subheader('Prochains jours'); start=date.today(); end=start+timedelta(days=7); rec,cancelled=recurring_between(start,end); items=[]
    for x in query("SELECT * FROM sessions WHERE date(start_at)>? AND date(start_at)<=? AND status='planned' ORDER BY start_at",(start.isoformat(),end.isoformat())): items.append((x['start_at'][:10],ico(x['sport']),x['title'],f"{x['duration_min'] or '?'} min"))
    for x in rec: items.append((x['date'].isoformat(),ico(x['event_type']),x['title'],'Récurrent'))
    for x in query('SELECT * FROM shifts WHERE date(start_at)>=? AND date(start_at)<=?',(start.isoformat(),end.isoformat())): items.append((x['start_at'][:10],'🚑','Garde '+x['shift_type'],'Travail'))
    for d,ic,t,m in sorted(items)[:7]: st.write(f"**{d[8:10]}/{d[5:7]}** · {ic} {t} · {m}")
    if cancelled:
        with st.expander(f'↪ {len(cancelled)} récurrence(s) annulée(s) par une garde'):
            for x in cancelled: st.caption(f"{x['date'].strftime('%d/%m')} · {x['title']} — {x['reason']}")
    if not ci:
        with st.expander('☀️ Faire mon check-in du jour',expanded=True):
            with st.form('checkin'):
                c1,c2=st.columns(2); sleep=c1.number_input('Sommeil (h)',0.0,14.0,7.0,.5); fatigue=c2.slider('Fatigue',1,5,3); quality=c1.slider('Qualité du sommeil',1,5,3); motivation=c2.slider('Motivation',1,5,3); soreness=c1.slider('Courbatures',1,5,3); stress=c2.slider('Stress',1,5,3); painloc=c1.text_input('Zone douloureuse'); pain=c2.slider('Douleur',0,10,0); trend=st.selectbox('Évolution',['stable','amélioration','aggravation'])
                if st.form_submit_button('Enregistrer',use_container_width=True): execute('INSERT INTO checkins(created_at,sleep_hours,sleep_quality,fatigue,motivation,soreness,stress,pain_location,pain_score,pain_trend) VALUES(?,?,?,?,?,?,?,?,?,?)',(datetime.now().isoformat(timespec='seconds'),sleep,quality,fatigue,motivation,soreness,stress,painloc,pain,trend)); st.rerun()

elif nav=='Planning':
    st.header('Planning adaptatif'); future=next_goal(); start=date.today(); end=start+timedelta(days=30); rec,cancelled=recurring_between(start,end)
    if future:
        st.write(f"Prochain objectif : **{future['name']}** · {future['event_date']}")
        if st.button('⚡ Recalculer intelligemment les 14 prochains jours',use_container_width=True):
            h=start+timedelta(days=14); shifts=query('SELECT * FROM shifts WHERE date(start_at)<=? AND date(end_at)>=?',(h.isoformat(),(start-timedelta(days=1)).isoformat())); fixed=query('SELECT * FROM constraints WHERE event_date>=? AND event_date<=?',(start.isoformat(),h.isoformat())); recurring,_=recurring_between(start,h); result=build_plan(future,shifts,combined_constraints(fixed,recurring)); execute("DELETE FROM sessions WHERE source='auto_v4' AND date(start_at)>=?",(start.isoformat(),))
            for s in result['sessions']: execute("INSERT INTO sessions(start_at,sport,title,duration_min,priority,intensity,objective,source) VALUES(?,?,?,?,?,?,?,'auto_v4')",(s['date'].isoformat()+'T18:00',s['sport'],s['title'],s['duration'],s['priority'],s['intensity'],s['objective']))
            st.success(f"{len(result['sessions'])} séances placées · les récurrences et gardes ont été prises en compte."); st.rerun()
    ev=[]
    for x in query('SELECT * FROM shifts WHERE date(start_at)>=? AND date(start_at)<=?',(start.isoformat(),end.isoformat())): ev.append([x['start_at'][:10],'🚑','Garde '+x['shift_type'],'Travail'])
    for x in query('SELECT * FROM constraints WHERE event_date>=? AND event_date<=?',(start.isoformat(),end.isoformat())): ev.append([x['event_date'],'📌',x['title'],'Fixe'])
    for x in rec: ev.append([x['date'].isoformat(),ico(x['event_type']),x['title'],'Récurrent'])
    for x in query('SELECT * FROM sessions WHERE date(start_at)>=? AND date(start_at)<=?',(start.isoformat(),end.isoformat())): ev.append([x['start_at'][:10],ico(x['sport']),x['title'],f"{x['duration_min'] or '?'} min"])
    if ev: st.dataframe(pd.DataFrame(sorted(ev),columns=['Date','','Événement','Info']),hide_index=True,use_container_width=True)
    if cancelled:
        st.subheader('Annulés automatiquement')
        for x in cancelled: st.warning(f"{x['date'].strftime('%d/%m')} · {x['title']} — {x['reason']}")

elif nav=='Progression':
    st.header('Progression'); acts=query('SELECT * FROM activities ORDER BY start_at')
    if acts:
        df=pd.DataFrame(acts); df['Charge']=df.apply(lambda r:srpe(r.get('duration_min'),r.get('rpe')),axis=1); df['Jour']=pd.to_datetime(df['start_at']).dt.date; recent=df[pd.to_datetime(df['start_at'])>=pd.Timestamp.now()-pd.Timedelta(days=7)]; a,b,c=st.columns(3); a.metric('Charge 7 j',round(recent['Charge'].sum())); b.metric('Temps 7 j',f"{recent['duration_min'].fillna(0).sum()/60:.1f} h"); c.metric('Séances',len(recent)); st.line_chart(df.groupby('Jour')['Charge'].sum())
    else: st.info('Les graphiques apparaîtront avec tes activités.')

elif nav=='Coach':
    st.header('Coach'); ci=checkin(); ps=today_session(); dec,score,status,why,action=decision(ci,ps,last_shift(),rugby_recent()); st.markdown(f"### {dec.replace('_',' ').title()}"); st.write(why); st.success(action); st.text_area('Message au coach',placeholder='Ex. J’ai une garde jeudi, adapte ma semaine…')

elif nav=='Ajouter':
    st.header('Ajouter au calendrier'); kind=st.segmented_control('Type',['🏋️ Séance','🚑 Garde','🔁 Récurrence','📌 Événement','🏁 Objectif','✅ Activité'],default='🏋️ Séance')
    if kind=='🏋️ Séance':
        with st.form('session'):
            sport=st.selectbox('Sport',['running','cycling','swimming','trail','strength'],format_func=lambda x:{'running':'🏃 Course','cycling':'🚴 Vélo','swimming':'🏊 Natation','trail':'⛰️ Trail','strength':'💪 Renforcement'}[x]); c1,c2=st.columns(2); d=c1.date_input('Jour',date.today()); t=c2.time_input('Heure',time(18)); title=st.text_input('Nom',placeholder='Ex. Endurance facile'); c3,c4=st.columns(2); duration=c3.number_input('Durée (min)',10,600,60,5); intensity=c4.selectbox('Intensité',['easy','moderate','threshold','hard']); objective=st.text_area('Consignes'); priority=st.select_slider('Importance',['P3','P2','P1','P0'],value='P2')
            if st.form_submit_button('➕ Ajouter',use_container_width=True): execute('INSERT INTO sessions(start_at,sport,title,duration_min,priority,intensity,objective) VALUES(?,?,?,?,?,?,?)',(dtiso(d,t),sport,title or 'Séance '+sport,duration,priority,intensity,objective)); st.success('Séance ajoutée.')
    elif kind=='🚑 Garde':
        with st.form('guard'):
            typ=st.selectbox('Type',['24h','12h_jour','12h_nuit']); d=st.date_input('Jour',date.today()); defaults={'24h':(time(8),time(8),1),'12h_jour':(time(7),time(20),0),'12h_nuit':(time(19),time(8),1)}; sh,eh,plus=defaults[typ]; c1,c2=st.columns(2); start_t=c1.time_input('Début',sh); end_d=c2.date_input('Fin — jour',d+timedelta(days=plus)); end_t=st.time_input('Fin — heure',eh)
            if st.form_submit_button('🚑 Ajouter la garde',use_container_width=True): execute('INSERT INTO shifts(start_at,end_at,shift_type) VALUES(?,?,?)',(dtiso(d,start_t),dtiso(end_d,end_t),typ)); st.success('Garde ajoutée. Les récurrences qui se chevauchent seront automatiquement annulées.'); st.rerun()
    elif kind=='🔁 Récurrence':
        st.caption('Exemple : rugby tous les lundis. Une garde qui chevauche le créneau annule uniquement cette occurrence, pas toute la série.')
        with st.form('recurrence'):
            typ=st.selectbox('Activité',['rugby_training','rugby_match','dance','other'],format_func=lambda x:{'rugby_training':'🏉 Rugby — entraînement','rugby_match':'🏉 Rugby — match','dance':'💃 Danse','other':'📅 Autre'}[x]); title=st.text_input('Nom',value='Rugby'); weekday=st.selectbox('Chaque',['Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi','Dimanche']); c1,c2=st.columns(2); start_t=c1.time_input('Heure',time(19)); duration=c2.number_input('Durée (min)',15,360,120,15); intensity=st.selectbox('Charge',['easy','moderate','hard'],index=1); c3,c4=st.columns(2); start_d=c3.date_input('À partir du',date.today()); has_end=c4.checkbox('Date de fin'); end_d=st.date_input('Jusqu’au',date.today()+timedelta(days=180)) if has_end else None
            if st.form_submit_button('🔁 Créer la récurrence',use_container_width=True): execute('INSERT INTO recurring_rules(title,event_type,weekday,start_time,duration_min,intensity,start_date,end_date,active) VALUES(?,?,?,?,?,?,?,?,1)',(title or typ,typ,['Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi','Dimanche'].index(weekday),start_t.strftime('%H:%M'),duration,intensity,start_d.isoformat(),end_d.isoformat() if end_d else None)); st.success('Récurrence créée.'); st.rerun()
    elif kind=='📌 Événement':
        with st.form('fixed'):
            typ=st.selectbox('Type',['rugby_training','rugby_match','dance','personal','other']); d=st.date_input('Jour',date.today()); title=st.text_input('Nom'); duration=st.number_input('Durée',15,360,90,15); intensity=st.selectbox('Charge',['easy','moderate','hard'])
            if st.form_submit_button('📌 Ajouter',use_container_width=True): execute('INSERT INTO constraints(event_date,event_type,title,duration_min,intensity,fixed) VALUES(?,?,?,?,?,1)',(d.isoformat(),typ,title or typ,duration,intensity)); st.success('Événement ajouté.')
    elif kind=='🏁 Objectif':
        with st.form('goal'):
            name=st.text_input('Nom'); d=st.date_input('Date',date.today()+timedelta(days=30)); sport=st.selectbox('Sport',['running','trail','cycling','triathlon','other']); priority=st.selectbox('Priorité',['A','A/B','B','C']); notes=st.text_area('Détails')
            if st.form_submit_button('🏁 Ajouter',use_container_width=True): execute('INSERT INTO goals(name,event_date,sport,kind,priority,notes) VALUES(?,?,?,?,?,?)',(name,d.isoformat(),sport,'competition',priority,notes)); st.success('Objectif ajouté.')
    else:
        with st.form('activity'):
            sport=st.selectbox('Sport',['running','trail','cycling','swimming','rugby','dance','strength','other']); c1,c2=st.columns(2); d=c1.date_input('Jour',date.today()); t=c2.time_input('Heure',datetime.now().time().replace(second=0,microsecond=0)); title=st.text_input('Titre'); duration=st.number_input('Durée (min)',1,1000,60); rpe=st.slider('Difficulté RPE',1,10,4); pain=st.slider('Douleur après',0,10,0)
            if st.form_submit_button('✅ Enregistrer',use_container_width=True): execute('INSERT INTO activities(start_at,sport,title,duration_min,rpe,pain) VALUES(?,?,?,?,?,?)',(dtiso(d,t),sport,title,duration,rpe,pain)); st.success('Activité enregistrée.')

else:
    t1,t2,t3=st.tabs(['Récurrences','Objectifs','Profil'])
    with t1:
        rules=query('SELECT * FROM recurring_rules ORDER BY weekday,start_time')
        if not rules: st.info('Aucune récurrence.')
        for r in rules:
            days=['Lun','Mar','Mer','Jeu','Ven','Sam','Dim']; st.write(f"🔁 **{r['title']}** · {days[r['weekday']]} {r['start_time']} · {r['duration_min']} min")
    with t2:
        for x in query("SELECT * FROM goals ORDER BY CASE WHEN COALESCE(event_date,'')='' THEN 1 ELSE 0 END,event_date"):
            with st.container(border=True): st.write(f"**{x['name']}** · {x['priority']} · {x['event_date'] or 'date à définir'}"); st.caption(x['notes'] or '')
    with t3:
        for sec,data in ATHLETE.items():
            with st.expander(sec):
                for k,v in data.items(): st.write(f'**{k} :** {v}')
st.caption('Endurance Coach V4.2 · récurrences intelligentes et planification sous contraintes · ne remplace pas un avis médical.')
