"""Deterministic plot of actual delivered-reference citations; no simulated links."""
import html,json,collections
from pathlib import Path
from .runtime import BASE

def plot(run_id,arm):
 f=BASE/run_id;profiles=json.loads((f/'population.json').read_text());rows=[json.loads(l) for l in (f/f'{arm}.jsonl').read_text().splitlines()];origins={r['id']:r['peer'] for r in rows if r['kind'] in ['observation','message_sent']};edges=sorted({(origins[r['source_id']],r['peer']) for r in rows if r['kind']=='dependency_cited' and r['source_id'] in origins and origins[r['source_id']]!=r['peer']});proof=json.loads((f/f'{arm}-coordination-proof.json').read_text());assert len(edges)==proof['distinct_directed_coordination_edges']
 topics=list(dict.fromkeys(p['topic'] for p in profiles));points={};labels=[];colors={'legitimate':'#447455','adversarial':'#b24d2d','pressure':'#8a955e'}
 for i,topic in enumerate(topics):
  x=i%4*180;y=i//4*110;labels.append(f'<text x="{x+8}" y="{y+16}" fill="#1c221d" font-size="15" font-family="sans-serif">{html.escape(topic)}</text>')
  for j,p in enumerate(p for p in profiles if p['topic']==topic):points[p['id']]=(x+10+j%8*20,y+36+j//8*17)
 paths=[]
 for a,b in edges:
  x,y=points[a];u,v=points[b];paths.append(f'<path d="M{x},{y} Q{(x+u)/2},{min(y,v)-14} {u},{v}"/>')
 nodes=[]
 for p in profiles:
  x,y=points[p['id']];nodes.append(f'<a href="../#agents?arm={arm}&amp;agent={p["id"]}" aria-label="{p["id"]}"><circle cx="{x}" cy="{y}" r="4" fill="{colors[p["kind"]]}"><title>{html.escape(p["id"]+" / "+p["role"]+" / "+p["topic"])}</title></circle></a>')
 svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 220" width="720" height="220" role="img" aria-label="Actual recorded peer-reference topology, grouped by topic"><rect width="720" height="220" fill="#f8f9f6"/><g fill="none" stroke="#447455" stroke-width=".6" opacity=".14">'+''.join(paths)+'</g>'+''.join(labels)+''.join(nodes)+'</svg>'
 (f/f'{arm}-coordination.svg').write_text(svg);meta={'run_id':run_id,'arm':arm,'nodes':256,'directed_recorded_reference_edges':len(edges),'layout':'Eight topic clusters; fixed profile-order node coordinates. Positions are editorial, edges are actual recorded delivered-reference citations.','nodes_are_model_profiles':True,'animated_traffic':False,'edges':edges,'main_weakly_connected_component':max(proof['coordination_component_sizes'])};(f/f'{arm}-coordination-topology.json').write_text(json.dumps(meta));return svg,meta
if __name__=='__main__':
 import sys
 for a in ['baseline','protected']:plot(sys.argv[1],a)
