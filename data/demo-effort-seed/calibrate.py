"""Calibrate catalogue.json on ledger.csv: scale_k (median actual/predicted mentor hours),
leave-one-out check, calendar parameters. Writes back scale_k and calendar into catalogue.json."""
import csv,json,math,statistics as st
cat=json.load(open('catalogue.json',encoding='utf-8'))
U={k:v['hours'] for k,v in cat['units'].items()}; R=cat['risks']
L=list(csv.DictReader(open('ledger.csv',encoding='utf-8-sig')))
# risk flags per demo (anonymised ids), kept here so they are reviewable
RISKS={}  # optional: risk flags per ledger demo, e.g. {"Demo 01": ["studio_first_on_stand"]}
INCOMPLETE=set()  # demos where the recorded hours cover only part of the build
def n(r,k):
    try: return float(r[k])
    except: return 0.0
def scope_hours(r):
    loc=(r['localization'] or '').lower()
    second=0 if (loc.startswith('none') or loc.startswith('one language') or 'english only' in loc or not loc) else 1
    rtl=1 if 'arab' in loc else 0
    h=(U['base']+U['use_case']*n(r,'use_cases')+U['new_object']*n(r,'new_objects')+U['extended_object']*n(r,'extended_objects')
       +U['lookup']*n(r,'lookups')+U['page']*n(r,'pages')+U['mobile_page']*n(r,'mobile_pages')+U['dashboard']*n(r,'dashboards')
       +U['process']*n(r,'processes')+U['dcm']*n(r,'dcm')+U['ai_skill']*n(r,'ai_skills')+U['studio_agent']*n(r,'studio_agents')
       +U['studio_tool']*n(r,'studio_tools')+U['landing']*n(r,'landings')+U['email_template']*n(r,'emails')+U['printable']*n(r,'printables')
       +U['custom_component']*n(r,'custom_components')+U['csharp']*(r['csharp']=='True')+U['integration']*n(r,'integrations')
       +U['second_language']*second+U['rtl_extra']*rtl)
    h+=sum(R[x]['hours'] for x in RISKS.get(r['demo'],[]))
    return h*cat['eras'][r['era']]
SHARED={r['demo'] for r in L if r['co_builders'].strip()}|{d for d,v in RISKS.items() if 'inherited_build' in v}
train=[r for r in L if r['status']=='delivered' and r['mentor_hours'] and r['demo'] not in INCOMPLETE|SHARED]
med={}
for era in ('pre-plugin','plugin','team'):
    rr=[float(r['mentor_hours'])/(scope_hours(r)/cat['eras'][r['era']]) for r in train if r['era']==era]
    if rr: med[era]=st.median(rr); print('raw ratio fact/scope by era', era, 'n=%d median %.2f'%(len(rr),med[era]))
for era in ('pre-plugin','team'):  # refit an era factor only when both it and the plugin era have >=2 demos
    if era in med and 'plugin' in med and sum(1 for r in train if r['era']==era)>=2 and sum(1 for r in train if r['era']=='plugin')>=2:
        cat['eras'][era]=round(med[era]/med['plugin'],2); print(era,'era factor refitted to',cat['eras'][era])
if len(train)<3:
    print('Not enough delivered solo demos in ledger.csv to calibrate (have %d, need 3). The seed values in catalogue.json stay as they are.'%len(train)); raise SystemExit(0)
ratios={r['demo']:float(r['mentor_hours'])/scope_hours(r) for r in train}
k=st.median(ratios.values())
print('scale_k = %.2f (n=%d)'%(k,len(train)))
print('%-12s %-10s %6s %6s %6s'%('demo','era','fact','pred','err'))
errs=[];inside=0
for r in train:
    k_loo=st.median([v for d,v in ratios.items() if d!=r['demo']])
    p=k_loo*scope_hours(r); a=float(r['mentor_hours'])
    lo,hi=p*0.7,p*1.4; inside+= lo<=a<=hi
    errs.append(abs(p-a)/a)
    print('%-12s %-10s %6.0f %6.0f %+5.0f%%'%(r['demo'],r['era'],a,p,(p-a)/a*100))
print('leave-one-out: median abs error %.0f%%, fact inside [0.7p,1.4p] in %d/%d'%(st.median(errs)*100,inside,len(train)))
plug=[r for r in L if r['era']=='plugin' and r['status']=='delivered' and r['mentor_hours']]
hpd=st.median(float(r['mentor_hours'])/max(1,float(r['mentor_wd'])) for r in plug if r['demo'] not in INCOMPLETE)
rev=st.median(float(r['review_wd']) for r in plug if r['review_wd']!='')
q=st.median(float(r['queue_wd']) for r in L if r['queue_wd']!='' and r['era']=='plugin')
print('plugin era: mentor hours/day %.1f, review days median %.1f, queue days median %.1f'%(hpd,rev,q))
# calendar check: predicted in-progress->resolved working days vs fact (plugin era, delivered)
print('calendar check (plugin, in progress -> resolved, working days):'); print('  shared/inherited excluded from fit:',sorted(SHARED))
for r in plug:
    if r['demo'] in INCOMPLETE: continue
    p=math.ceil(k*scope_hours(r)/hpd)*(cat['calendar'].get('co_builder_calendar_factor',1) if r['co_builders'].strip() else 1)+rev+sum(R[x]['calendar_days'] for x in RISKS.get(r['demo'],[]))
    print('  %-12s fact %s pred %.1f'%(r['demo'],r['inprogress_to_resolved_wd'],p))
cat['scale_k']=round(k,2); cat['calendar'].update(mentor_hours_per_day=round(hpd,1),review_days_median=rev,queue_days_median=q)
json.dump(cat,open('catalogue.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
