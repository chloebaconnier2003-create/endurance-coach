from datetime import date,timedelta
import calendar
import streamlit as st
DAYS=['Lun','Mar','Mer','Jeu','Ven','Sam','Dim']
DAY_FULL=['Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi','Dimanche']
MONTHS=['janvier','février','mars','avril','mai','juin','juillet','août','septembre','octobre','novembre','décembre']

def _by_date(events):
 out={}
 for e in events:out.setdefault(e['date'],[]).append(e)
 return out

def _label(e):
 return f"{e.get('icon','•')} {e.get('time','')} {e['title']}".replace('  ',' ')

def _cards(items,key):
 selected=None
 for i,e in enumerate(sorted(items,key=lambda x:x.get('time',''))):
  meta=e.get('meta',''); label=_label(e)+(f"\n{meta}" if meta else '')
  if st.button(label,key=f"{key}_{i}_{e.get('uid',e['title'])}",use_container_width=True):selected=e
 return selected

def month_view(year,month,events):
 by=_by_date(events); selected=None
 st.markdown('''<style>
 .ec-month{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:5px}.ec-head{text-align:center;font-size:.76rem;font-weight:750;opacity:.65;padding:.3rem 0}.ec-day{min-height:112px;border:1px solid rgba(128,128,128,.22);border-radius:12px;padding:7px;overflow:hidden}.ec-day.today{border:2px solid currentColor}.ec-num{font-weight:800;font-size:.85rem;margin-bottom:5px}.ec-event{font-size:.69rem;line-height:1.15;margin:3px 0;padding:4px;border-radius:6px;background:rgba(128,128,128,.13);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.ec-empty{opacity:.2}
 @media(max-width:700px){.ec-month{gap:2px}.ec-head{font-size:.62rem}.ec-day{min-height:67px;padding:3px;border-radius:7px}.ec-num{font-size:.68rem;margin-bottom:2px}.ec-event{font-size:.54rem;padding:2px;margin:2px 0}.ec-event .ec-title{display:none}}
 </style>''',unsafe_allow_html=True)
 weeks=calendar.Calendar(firstweekday=0).monthdatescalendar(year,month)
 html='<div class="ec-month">'+''.join(f'<div class="ec-head">{d}</div>' for d in DAYS)
 for week in weeks:
  for d in week:
   if d.month!=month:html+='<div class="ec-day ec-empty"></div>';continue
   cls='ec-day today' if d==date.today() else 'ec-day';html+=f'<div class="{cls}"><div class="ec-num">{d.day}</div>'
   for e in sorted(by.get(d,[]),key=lambda x:x.get('time',''))[:3]:html+=f'<div class="ec-event">{e.get("icon","•")} {e.get("time","")} <span class="ec-title">{e["title"]}</span></div>'
   extra=len(by.get(d,[]))-3
   if extra>0:html+=f'<div class="ec-event">+{extra}</div>'
   html+='</div>'
 html+='</div>';st.markdown(html,unsafe_allow_html=True)
 st.caption('Sur téléphone : aperçu compact du mois. Sélectionne un jour ci-dessous pour ouvrir son agenda détaillé.')
 first=date(year,month,1);last=(date(year+1,1,1)-timedelta(days=1)) if month==12 else date(year,month+1,1)-timedelta(days=1);default=date.today() if first<=date.today()<=last else first
 chosen=st.date_input('Ouvrir une journée',default,min_value=first,max_value=last,format='DD/MM/YYYY',key=f'open_day_{year}_{month}')
 st.markdown(f'### {DAY_FULL[chosen.weekday()]} {chosen.day} {MONTHS[chosen.month-1]}')
 items=by.get(chosen,[])
 if items:selected=_cards(items,f'monthday_{chosen.isoformat()}')
 else:st.info('Journée libre : aucun événement enregistré.')
 return selected

def week_view(start,events):
 by=_by_date(events);selected=None
 st.caption(f"{start.strftime('%d/%m')} → {(start+timedelta(days=6)).strftime('%d/%m')}")
 for i in range(7):
  d=start+timedelta(days=i);items=by.get(d,[]);today=' · AUJOURD’HUI' if d==date.today() else ''
  st.markdown(f'### {DAY_FULL[i]} {d.strftime("%d/%m")}{today}')
  if items:
   pick=_cards(items,f'week_{start.isoformat()}_{i}')
   if pick:selected=pick
  else:st.caption('○ Aucun événement')
  if i<6:st.divider()
 return selected
