import streamlit as st
import calendar
from datetime import date,timedelta

MONTHS=['Janvier','Février','Mars','Avril','Mai','Juin','Juillet','Août','Septembre','Octobre','Novembre','Décembre']
DAYS=['Lun','Mar','Mer','Jeu','Ven','Sam','Dim']

def _event_line(e):
    return f"{e.get('icon','•')} {e.get('title','')}"

def month_view(year,month,events):
    st.markdown(f"### {MONTHS[month-1]} {year}")
    cols=st.columns(7)
    for i,n in enumerate(DAYS): cols[i].markdown(f"**{n}**")
    cal=calendar.Calendar(firstweekday=0).monthdatescalendar(year,month)
    by={}
    for e in events: by.setdefault(e['date'],[]).append(e)
    for week in cal:
        cols=st.columns(7)
        for i,d in enumerate(week):
            with cols[i]:
                faded=d.month!=month; label=f"**{d.day}**" if not faded else f"*{d.day}*"
                st.markdown(label)
                for e in by.get(d,[])[:3]: st.caption(_event_line(e))
                if len(by.get(d,[]))>3: st.caption(f"+{len(by[d])-3}")

def week_view(anchor,events):
    monday=anchor-timedelta(days=anchor.weekday()); by={}
    for e in events: by.setdefault(e['date'],[]).append(e)
    cols=st.columns(7)
    for i in range(7):
        d=monday+timedelta(days=i)
        with cols[i]:
            st.markdown(f"**{DAYS[i]} {d.day}**")
            if d==date.today(): st.caption('Aujourd’hui')
            if not by.get(d): st.caption('—')
            for e in by.get(d,[]):
                st.markdown(f"{e.get('icon','•')} **{e.get('title','')}**")
                if e.get('meta'): st.caption(e['meta'])
