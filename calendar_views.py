import calendar
from datetime import date,timedelta
import streamlit as st

def _events_by_date(events):
    out={}
    for e in events: out.setdefault(e['date'],[]).append(e)
    return out

def month_view(year,month,events):
    by=_events_by_date(events); cal=calendar.Calendar(firstweekday=0); weeks=cal.monthdatescalendar(year,month)
    headers=st.columns(7)
    for c,n in zip(headers,['Lun','Mar','Mer','Jeu','Ven','Sam','Dim']): c.markdown(f'**{n}**')
    for week in weeks:
        cols=st.columns(7)
        for col,d in zip(cols,week):
            faded=d.month!=month; items=by.get(d,[]); lines=[]
            for e in items[:4]: lines.append(f"{e.get('icon','•')} {e['title']}")
            if len(items)>4: lines.append(f"+{len(items)-4} autre(s)")
            txt='<br>'.join(lines) or '&nbsp;'
            opacity='.35' if faded else '1'
            col.markdown(f"<div style='min-height:105px;border:1px solid rgba(128,128,128,.2);border-radius:12px;padding:7px;opacity:{opacity}'><b>{d.day}</b><br><span style='font-size:.78rem'>{txt}</span></div>",unsafe_allow_html=True)

def week_view(start,events):
    by=_events_by_date(events)
    for i in range(7):
        d=start+timedelta(days=i); st.markdown(f"### {['Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi','Dimanche'][d.weekday()]} {d.strftime('%d/%m')}")
        items=by.get(d,[])
        if not items: st.caption('Disponible / aucun événement fixe')
        for e in sorted(items,key=lambda x:x.get('time','')):
            meta=' · '.join(x for x in [e.get('time',''),e.get('meta','')] if x)
            st.markdown(f"**{e.get('icon','•')} {e['title']}**"+(f" — {meta}" if meta else ''))
        st.divider()
