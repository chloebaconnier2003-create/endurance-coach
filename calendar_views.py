import calendar
from datetime import timedelta
import streamlit as st


def _events_by_date(events):
    out={}
    for e in events:
        out.setdefault(e['date'],[]).append(e)
    return out


def _choose(items,key,compact=False):
    chosen=None
    for i,e in enumerate(sorted(items,key=lambda x:x.get('time',''))):
        if compact:
            label=f"{e.get('icon','•')} {e.get('time','')} {e['title']}"
        else:
            label=f"{e.get('icon','•')} {e.get('time','')} {e['title']}"
        if st.button(label,key=f"{key}_{i}_{e.get('uid',e['title'])}",use_container_width=True):
            chosen=e
    return chosen


def _desktop_month(year,month,by):
    cal=calendar.Calendar(firstweekday=0); weeks=cal.monthdatescalendar(year,month); selected=None
    st.markdown("<div class='desktop-calendar'>",unsafe_allow_html=True)
    headers=st.columns(7,gap='small')
    for c,n in zip(headers,['Lun','Mar','Mer','Jeu','Ven','Sam','Dim']):
        c.markdown(f"<div style='text-align:center;font-weight:700'>{n}</div>",unsafe_allow_html=True)
    for wi,week in enumerate(weeks):
        cols=st.columns(7,gap='small')
        for col,d in zip(cols,week):
            with col:
                st.markdown(f"**{d.day}**" if d.month==month else f"<span style='opacity:.3'>{d.day}</span>",unsafe_allow_html=True)
                pick=_choose(by.get(d,[])[:4],f"desk_{year}_{month}_{wi}_{d.isoformat()}")
                if pick:selected=pick
                if len(by.get(d,[]))>4: st.caption(f"+{len(by[d])-4} autre(s)")
    st.markdown('</div>',unsafe_allow_html=True)
    return selected


def _mobile_month(year,month,by):
    """Agenda-style month view: much easier to read/tap on narrow screens."""
    cal=calendar.Calendar(firstweekday=0); selected=None
    st.markdown("<div class='mobile-calendar'>",unsafe_allow_html=True)
    for week_no,week in enumerate(cal.monthdatescalendar(year,month)):
        visible=[d for d in week if d.month==month]
        if not visible: continue
        st.caption(f"Semaine {visible[0].isocalendar().week}")
        for d in visible:
            items=by.get(d,[])
            dayname=['Lun','Mar','Mer','Jeu','Ven','Sam','Dim'][d.weekday()]
            today=' · Aujourd’hui' if d==__import__('datetime').date.today() else ''
            if items:
                st.markdown(f"**{dayname} {d.day}{today}**")
                pick=_choose(items,f"mob_{year}_{month}_{week_no}_{d.isoformat()}",compact=True)
                if pick:selected=pick
            else:
                st.markdown(f"<div style='opacity:.55;margin:.2rem 0 .55rem 0'><b>{dayname} {d.day}{today}</b> · libre</div>",unsafe_allow_html=True)
        st.divider()
    st.markdown('</div>',unsafe_allow_html=True)
    return selected


def month_view(year,month,events):
    by=_events_by_date(events)
    # Both renderers are present; CSS switches automatically according to viewport width.
    st.markdown("""
    <style>
    .mobile-calendar-marker{display:none}
    @media (max-width: 700px){
      .desktop-calendar{display:none !important}
      div[data-testid='stHorizontalBlock']:has(.desktop-calendar){display:none !important}
      .block-container{padding-left:.55rem!important;padding-right:.55rem!important}
      div[data-testid='stButton'] button{min-height:42px!important;font-size:.86rem!important;text-align:left!important}
    }
    @media (min-width: 701px){
      .mobile-calendar{display:none !important}
    }
    </style>
    """,unsafe_allow_html=True)
    # Streamlit cannot reliably branch Python rendering on browser width without JS/custom components.
    # Keep the desktop grid and add a phone-friendly agenda below; CSS hides the agenda on desktop.
    desktop=_desktop_month(year,month,by)
    st.markdown("<div class='mobile-calendar'>",unsafe_allow_html=True)
    mobile=_mobile_month(year,month,by)
    st.markdown('</div>',unsafe_allow_html=True)
    return mobile or desktop


def week_view(start,events):
    by=_events_by_date(events); selected=None
    st.markdown("""
    <style>
    @media(max-width:700px){
      .block-container{padding-left:.65rem!important;padding-right:.65rem!important}
      div[data-testid='stButton'] button{white-space:normal!important;height:auto!important;min-height:44px!important}
    }
    </style>
    """,unsafe_allow_html=True)
    for i in range(7):
        d=start+timedelta(days=i); st.markdown(f"### {['Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi','Dimanche'][d.weekday()]} {d.strftime('%d/%m')}")
        items=by.get(d,[])
        if not items: st.caption('Disponible / aucun événement fixe')
        pick=_choose(items,f"w_{start.isoformat()}_{i}")
        if pick:selected=pick
        st.divider()
    return selected
