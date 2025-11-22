from scorer import score_transcript
import json, os
p = os.path.join(os.getcwd(), 'static', 'sample.txt')
if os.path.exists(p):
    with open(p,'r',encoding='utf-8') as f:
        t = f.read()
else:
    t = "Hello sample transcript."
res = score_transcript(t)
with open('sample_result.json','w',encoding='utf-8') as f:
    json.dump(res, f, indent=2)
print("Wrote sample_result.json")
