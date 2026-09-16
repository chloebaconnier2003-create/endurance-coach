import calendar
from datetime import date,timedelta
import streamlit as st

def _by_date(events):
 out={}
 for e in events:out.setdefault(e['date'],[]).append(e)
 return out

def event_cards(items,key):
 selected=None
 for i,e in enumerate(sorted(items,key=lambda x:x.get('time',''))):
  meta=' · '.join(x for x in [e.get('time',''),e.get('meta','')] if x)
  label=f"{e.get('icon','•')}  {e['title']}"+(f"  ·  {meta}" if meta else '')
  if st.button(label,key=f"{key}_{i}_{e.get('uid',e['title'])}",use_container_width=True):selected=e
 return selected

def month_view(year,month,events):
 """Stable mobile-first month: compact date selector + daily agenda. Optional desktop overview below."""
 by=_by_date(events); first=date(year,month,1); last=(date(year+1,1,1)-timedelta(days=1)) if month==12 else date(year,month+1,1)-timedelta(days=1)
 default=date.today() if first<=date.today()<=last else first
 days=[]; d=first
 while d<=last:days.append(d); d+=timedelta(days=1)
 selected_day=st.selectbox('Jour',days,index=days.index(default),format_func=lambda x:f"{['Lun','Mar','Mer','Jeu','Ven','Sam','Dim'][x.weekday()]} {x.day:02d}/{x.month:02d}",key=f'mobile_day_{year}_{month}')
 st.markdown(f"### {['Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi','Dimanche'][selected_day.weekday()]} {selected_day.strftime('%d %B').replace('September','septembre')}")
 items=by.get(selected_day,[])
 selected=event_cards(items,f'day_{selected_day}') if items else None
 if not items:st.info('Journée libre dans le planning.')
 with st.expander('🗓️ Vue d’ensemble du mois'):
  cal=calendar.Calendar(firstweekday=0)
  st.caption('Aperçu compact — sélectionne ensuite le jour ci-dessus pour agir sur un événement.')
  for week in cal.monthdatescalendar(year,month):
   cols=st.columns(7,gap='small')
   for col,d in zip(cols,week):
    if d.month!=month:col.markdown(' ');continue
    n=len(by.get(d,[])); marker=' •' if n else ''
    col.markdown(f"<div style='text-align:center;padding:.35rem .1rem;border-radius:10px;border:1px solid rgba(128,128,128,.18)'><b>{d.day}</b><br><small>{marker}</small></div>",unsafe_allow_html=True)
 return selected

def week_view(start,events):
 by=_by_date(events); selected=None
 for i in range(7):
  d=start+timedelta(days=i); today=' · AUJOURD’HUI' if d==date.today() else ''
  st.markdown(f"#### {['LUNDI','MARDI','MERCREDI','JEUDI','VENDREDI','SAMEDI','DIMANCHE'][d.weekday()]} {d.strftime('%d/%m')}{today}")
  items=by.get(d,[])
  pick=event_cards(items,f'w_{start}_{i}') if items else None
  if pick:selected=pick
  if not items:st.caption('Libre / récupération possible')
  st.divider()
 return selected
