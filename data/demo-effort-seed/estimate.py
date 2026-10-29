"""Estimate one demo: python estimate.py scope.json
scope.json = {"demo":..,"era":"plugin|team","use_cases":..,"new_objects":..,...,"second_language":0/1,"rtl":0/1,
              "risks":[...], "co_builder":true/false}  (keys = catalogue units, plural where counted)"""
import json,math,sys
cat=json.load(open(__file__.replace('estimate.py','catalogue.json'),encoding='utf-8'))
s=json.load(open(sys.argv[1],encoding='utf-8'))
U={k:v['hours'] for k,v in cat['units'].items()}; R=cat['risks']; C=cat['calendar']
MAP={'use_cases':'use_case','new_objects':'new_object','extended_objects':'extended_object','lookups':'lookup','pages':'page',
 'mobile_pages':'mobile_page','dashboards':'dashboard','processes':'process','dcm':'dcm','ai_skills':'ai_skill','studio_agents':'studio_agent',
 'studio_tools':'studio_tool','landings':'landing','emails':'email_template','printables':'printable','custom_components':'custom_component',
 'csharp':'csharp','integrations':'integration','second_language':'second_language','rtl':'rtl_extra'}
lines=[('base',U['base'])]+[(k,U[u]*float(s.get(k,0) or 0)) for k,u in MAP.items() if s.get(k)]
risk=[(r,R[r]['hours']) for r in s.get('risks',[])]
raw=sum(h for _,h in lines)+sum(h for _,h in risk)
k=cat['scale_k']; era=cat['eras'][s.get('era','plugin')]
p50=raw*k*era; p80=p50*1.4
cal_wait=sum(R[r]['calendar_days'] for r in s.get('risks',[]))
f=C.get('co_builder_calendar_factor',1) if s.get('co_builder') else 1
d=lambda h: math.ceil(h/C['mentor_hours_per_day'])*f
print(f"{s.get('demo','demo')}: mentor hours P50 {p50:.0f} / P80 {p80:.0f}  (raw {raw:.0f} x k {k} x era {era})")
print(f"build working days P50 {d(p50):.1f} / P80 {d(p80):.1f}; + review {C['review_days_median']} + waits {cal_wait}; queue before start ~{C['queue_days_median']}")
print("biggest cost lines:"); [print(f"  {n:<18}{h*k*era:5.1f} h") for n,h in sorted(lines+risk,key=lambda x:-x[1])[:8]]
