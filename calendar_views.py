from datetime import date,timedelta
import streamlit as st

DAYS=['Lun','Mar','Mer','Jeu','Ven','Sam','Dim']
DAY_FULL=['Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi','Dimanche']
MONTHS=['janvier','février','mars','avril','mai','juin','juillet','août','septembre','octobre','novembre','décembre']

def _by_date(events):
 out={}
 for e in events: out.setdefault(e['date'],[]).append(e)
 return out

def _event_label(e):
 bits=[]
 if e.get('time'): bits.append(e['time'])
 if e.get('meta'): bits.append(e['meta'])
 suffix=' · '.join(bits)
 return f"{e.get('icon','•')}  {e['title']}"+(f"\n{suffix}" if suffix else '')

def event_cards(items,key):
 selected=None
 for i,e in enumerate(sorted(items,key=lambda x:x.get('time',''))):
  if st.button(_event_label(e),key=f"{key}_{i}_{e.get('uid',e['title'])}",use_container_width=True): selected=e
 return selected

def month_view(year,month,events):
 """True mobile-first planner: native calendar selector + agenda cards. No 7-column Streamlit grid."""
 by=_by_date(events)
 first=date(year,month,1)
 last=(date(year+1,1,1)-timedelta(days=1)) if month==12 else date(year,month+1,1)-timedelta(days=1)
 default=date.today() if first<=date.today()<=last else first

 st.markdown("""
 <style>
 div[data-testid="stDateInput"] input{font-size:1rem!important;font-weight:650!important}
 div[data-testid="stDateInput"]{margin-bottom:.35rem}
 div[data-testid="stButton"] button{justify-content:flex-start!important;text-align:left!important;padding:.72rem .85rem!important;line-height:1.25!important}
 @media(max-width:700px){
   div[data-testid="stDateInput"] button{min-height:48px!important}
   div[data-testid="stButton"] button{min-height:58px!important;font-size:.92rem!important}
 }
 </style>
 """,unsafe_allow_html=True)

 selected_day=st.date_input(
  'Choisir un jour',value=default,min_value=first,max_value=last,
  format='DD/MM/YYYY',key=f'planner_day_{year}_{month}'
 )
 st.caption(f"{MONTHS[month-1].capitalize()} {year} · touche le champ ci-dessus pour ouvrir le calendrier")
 st.markdown(f"### {DAY_FULL[selected_day.weekday()]} {selected_day.day} {MONTHS[selected_day.month-1]}")
 items=by.get(selected_day,[])
 selected=event_cards(items,f'day_{selected_day.isoformat()}') if items else None
 if not items: st.info('Aucun événement prévu ce jour. Journée disponible.')

 # Useful mobile context without reproducing an unreadable month grid.
 st.markdown('#### Prochains jours')
 upcoming=[]
 for offset in range(1,8):
  d=selected_day+timedelta(days=offset)
  if d>last: break
  if by.get(d): upcoming.append((d,by[d]))
 if not upcoming: st.caption('Aucun événement sur les 7 jours suivants.')
 for d,items2 in upcoming:
  with st.expander(f"{DAYS[d.weekday()]} {d.day:02d}/{d.month:02d} · {len(items2)} événement{'s' if len(items2)>1 else ''}"):
   pick=event_cards(items2,f'next_{d.isoformat()}')
   if pick: selected=pick
 return selected

def week_view(start,events):
 """Vertical timeline designed for one-handed phone use."""
 by=_by_date(events); selected=None
 st.caption(f"Semaine du {start.strftime('%d/%m')} au {(start+timedelta(days=6)).strftime('%d/%m')}")
 for i in range(7):
  d=start+timedelta(days=i); items=by.get(d,[])
  marker=' · AUJOURD’HUI' if d==date.today() else ''
  st.markdown(f"### {DAY_FULL[d.weekday()]} {d.day:02d}/{d.month:02d}{marker}")
  if items:
   pick=event_cards(items,f'week_{start.isoformat()}_{i}')
   if pick: selected=pick
  else: st.caption('○ Libre / récupération possible')
  if i<6: st.divider()
 return selected
