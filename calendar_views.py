import calendar
from datetime import timedelta
import streamlit as st

def _events_by_date(events):
    out={}
    for e in events: out.setdefault(e['date'],[]).append(e)
    return out

def _choose(items,key):
    chosen=None
    for i,e in enumerate(sorted(items,key=lambda x:x.get('time',''))):
        label=f"{e.get('icon','•')} {e.get('time','')} {e['title']}"
        if st.button(label,key=f"{key}_{i}_{e.get('uid',e['title'])}",use_container_width=True): chosen=e
    return chosen

def month_view(year,month,events):
    by=_events_by_date(events); cal=calendar.Calendar(firstweekday=0); weeks=cal.monthdatescalendar(year,month); selected=None
    headers=st.columns(7)
    for c,n in zip(headers,['Lun','Mar','Mer','Jeu','Ven','Sam','Dim']): c.markdown(f'**{n}**')
    for wi,week in enumerate(weeks):
        cols=st.columns(7)
        for col,d in zip(cols,week):
            with col:
                st.markdown(f"**{d.day}**" if d.month==month else f"<span style='opacity:.35'>{d.day}</span>",unsafe_allow_html=True)
                pick=_choose(by.get(d,[])[:4],f"m_{year}_{month}_{wi}_{d.isoformat()}")
                if pick:selected=pick
                if len(by.get(d,[]))>4: st.caption(f"+{len(by[d])-4} autre(s)")
    return selected

def week_view(start,events):
    by=_events_by_date(events); selected=None
    for i in range(7):
        d=start+timedelta(days=i); st.markdown(f"### {['Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi','Dimanche'][d.weekday()]} {d.strftime('%d/%m')}")
        items=by.get(d,[])
        if not items: st.caption('Disponible / aucun événement fixe')
        pick=_choose(items,f"w_{start.isoformat()}_{i}")
        if pick:selected=pick
        st.divider()
    return selected
