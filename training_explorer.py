"""Week-by-week season explorer. Preview is available without generating database sessions."""
from datetime import date,timedelta
import streamlit as st
from db import query
from weekly_generator import phase_for,_week_index,prescription,generate_week
from workout_engine import detailed_workout

LABELS={'semi':'M1 · Semi Porto-Vecchio','trail':'M2 · SaintéLyon / trail','reset':'M3 · Récupération et reconstruction','base_run':'M4 · Base marathon et triathlon','marathon':'M5 · Marathon Aveiro','ventoux':'M6 · Transition vélo / Ventoux','half':'M7 · Half Annecy','cinglée':'M8 · Cinglée du Ventoux','colombier':'M9 · Grand Colombier','full':'M10 · Spécifique LéMan','taper':'M11 · Affûtage LéMan'}
ICONS={'running':'🏃','trail':'⛰️','cycling':'🚴','swimming':'🏊','strength':'💪'}
DAYS=['Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi','Dimanche']
FIRST=date(2026,10,12);LAST=date(2027,9,12)
RACES={'2026-10-18':'Semi-marathon Porto-Vecchio','2026-11-28':'SaintéLyon relais · départ 00 h (jusqu’au 29/11)','2027-04-25':'Marathon Aveiro','2027-06-20':'Half Ironman Annecy','2027-09-12':'LéMan Full Distance'}
def _week_dates():
    out=[];d=FIRST
    while d<=LAST:out.append(d);d+=timedelta(days=7)
    return out
def _events(start,end):
    return query("SELECT event_date,event_type,title FROM constraints WHERE event_date>=? AND event_date<=? AND event_type IN ('rugby_match','race') ORDER BY event_date",(start.isoformat(),end.isoformat()))
def _details(s):
    w=detailed_workout(s['sport'],s['intensity'],s['duration_min'],s.get('objective') or '',s.get('title') or '')
    st.write('**Objectif :**',s.get('objective') or 'Endurance et régularité')
    st.write('**Échauffement :**',w['warmup'])
    st.write('**Corps de séance :**',w['main'])
    st.write('**Retour au calme :**',w['cooldown'])
    st.write('**Intensité :**',w['intensity_target'])
    st.write('**Nutrition :**',w['nutrition'])
    st.caption('Séance adaptable à la fatigue, aux gardes et à la douleur. Pas d’allure inventée.')
def training_explorer():
    st.header('📖 Toutes mes séances')
    st.caption('Sélectionne une semaine pour voir les 7 jours, chaque sport et le contenu détaillé en cliquant. Les semaines futures non générées sont des aperçus, pas des rendez-vous confirmés.')
    weeks=_week_dates();current=date.today()-timedelta(days=date.today().weekday())
    default=min(range(len(weeks)),key=lambda i:abs((weeks[i]-current).days))
    selected=st.selectbox('Semaine de préparation',weeks,index=default,format_func=lambda d:f'{d.strftime("%d/%m/%Y")} → {(d+timedelta(days=6)).strftime("%d/%m/%Y")} · {LABELS.get(phase_for(d)[0],"Préparation")}',key='explorer_week')
    end=selected+timedelta(days=6);phase,_=phase_for(selected);w=_week_index(selected,phase)
    st.subheader(LABELS.get(phase,phase))
    st.caption(f'Semaine {w+1} du bloc · {selected.strftime("%d/%m")} au {end.strftime("%d/%m/%Y")}')
    actual=query("SELECT * FROM sessions WHERE date(start_at)>=? AND date(start_at)<=? AND status!='cancelled' ORDER BY start_at",(selected.isoformat(),end.isoformat()))
    fixed=_events(selected,end)
    if actual:
        st.success(f'{len(actual)} séances enregistrées · calendrier réel')
        sessions=actual
    else:
        st.info('Aucune séance enregistrée : aperçu du placement selon les gardes et contraintes connues. Les horaires restent indicatifs.')
        sessions=generate_week(selected,preview=True)['sessions']
        if selected>=date.today():
            if st.button('Planifier cette semaine dans le calendrier',key='explorer_generate'):
                r=generate_week(selected)
                st.success(r['message']);st.rerun()
    by_day={selected+timedelta(days=i):[] for i in range(7)}
    for s in sessions:
        if s.get('start_at'):
            d=date.fromisoformat(s['start_at'][:10])
            if d in by_day:by_day[d].append(s)
    for i,(day,items) in enumerate(by_day.items()):
        st.markdown(f'#### {DAYS[i]} {day.strftime("%d/%m")}')
        for ev in fixed:
            if ev['event_date']==day.isoformat():
                st.warning(('🏉 ' if ev['event_type']=='rugby_match' else '🏁 ')+ev['title'])
        if items:
            for s in items:
                with st.expander(f"{ICONS.get(s['sport'],'📌')} {s['title']} · {s['duration_min']} min · {s['sport']} · {s.get('status','planned')}"):
                    _details(s)
        elif not actual:
            st.caption('Repos ou indisponibilité prévisionnelle')
        else:
            st.caption('Repos / aucune séance enregistrée')
    if not actual:
        st.divider();st.subheader('Séances de la semaine, par sport · aperçu')
        for sport in ('swimming','cycling','running','trail','strength'):
            group=[s for s in sessions if s['sport']==sport]
            if not group:continue
            st.markdown(f"**{ICONS.get(sport,'📌')} { {'swimming':'Natation','cycling':'Vélo / home-trainer','running':'Course à pied','trail':'Trail','strength':'Renforcement'}.get(sport,sport)}**")
            for j,s in enumerate(group):
                with st.expander(f"{s['title']} · {s['duration_min']} min · {s['intensity']}",expanded=False):
                    _details(s)
