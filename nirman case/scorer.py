import os, math, json, re
from collections import Counter

def normalize(v, vmin, vmax):
    if vmax==vmin:
        return 0.0
    return max(0.0, min(1.0, (v - vmin) / (vmax - vmin)))

def tokenize(text):
    text = text.lower()
    tokens = re.findall(r"\b[a-z0-9']+\b", text)
    return tokens

def keyword_score(transcript_tokens, keywords):
    if not keywords:
        return 0.0
    klist = [k.strip().lower() for k in re.split('[,;|]', keywords) if k.strip()]
    if not klist:
        return 0.0
    tset = set(transcript_tokens)
    found = sum(1 for k in klist if k in tset)
    return found / len(klist)

def length_score(word_count, min_words, max_words):
    if min_words is None and max_words is None:
        return 1.0
    if min_words is None:
        return 1.0 if word_count <= max_words else max(0.0, 1 - (word_count - max_words)/max(1, max_words))
    if max_words is None:
        return 1.0 if word_count >= min_words else word_count / max(1, min_words)
    if word_count < min_words:
        return word_count / max(1, min_words)
    if word_count > max_words:
        return max(0.0, 1 - (word_count - max_words)/max(1, max_words))
    return 1.0

def simple_semantic_score(transcript, target_text):
    ta = set(tokenize(transcript))
    tb = set(tokenize(target_text))
    if not ta or not tb:
        return 0.0
    inter = ta.intersection(tb)
    union = ta.union(tb)
    jaccard = len(inter) / len(union)
    prop = len(inter) / len(tb)
    return 0.5 * jaccard + 0.5 * prop

def load_rubric_from_excel(path):
    try:
        import pandas as pd
        df = pd.read_excel(path)
        df_cols = [c.lower() for c in df.columns]
        def get(col_names):
            for c in col_names:
                if c in df_cols:
                    return df.columns[df_cols.index(c)]
            return None
        crit_col = get(['criterion', 'criteria', 'name'])
        desc_col = get(['description', 'desc'])
        kw_col = get(['keywords', 'keyword', 'key words'])
        weight_col = get(['weight', 'weights'])
        min_col = get(['min', 'minwords', 'min_words', 'min word limit'])
        max_col = get(['max', 'maxwords', 'max_words', 'max word limit'])
        rubric = []
        for _, row in df.iterrows():
            rubric.append({
                'criterion': str(row[crit_col]) if crit_col else '',
                'description': str(row[desc_col]) if desc_col else '',
                'keywords': str(row[kw_col]) if kw_col and not pd.isna(row[kw_col]) else '',
                'weight': float(row[weight_col]) if weight_col and not pd.isna(row[weight_col]) else 1.0,
                'min_words': int(row[min_col]) if min_col and not pd.isna(row[min_col]) else None,
                'max_words': int(row[max_col]) if max_col and not pd.isna(row[max_col]) else None,
            })
        return rubric
    except Exception as e:
        raise e

def default_rubric():
    return [
        {'criterion':'Content', 'description':'Includes personal background, family, hobbies, favorite subject, and a closing thank you.', 'keywords':'family,hobby,science,cricket,thank you', 'weight':3.0, 'min_words':30, 'max_words':200},
        {'criterion':'Clarity', 'description':'Clear sentence structure, simple vocabulary and understandable statements.', 'keywords':'clear,understandable,well', 'weight':2.0, 'min_words':10, 'max_words':200},
        {'criterion':'Fluency', 'description':'Smooth flow, minimal pauses or repetitions (evaluated from transcript)', 'keywords':'um,uh,repeat', 'weight':2.0, 'min_words':5, 'max_words':500},
        {'criterion':'Engagement', 'description':'Interesting facts or hooks that engage listener.', 'keywords':'fun fact,interesting,play', 'weight':1.0, 'min_words':0, 'max_words':200},
    ]

def score_transcript(transcript, rubric=None):
    if rubric is None:
        excel_path = os.path.join(os.getcwd(), 'Case study for interns.xlsx')
        if os.path.exists(excel_path):
            try:
                rubric = load_rubric_from_excel(excel_path)
            except Exception:
                rubric = default_rubric()
        else:
            rubric = default_rubric()

    tokens = tokenize(transcript)
    word_count = len(tokens)
    per = []
    total_weight = sum(max(0.0001, r.get('weight',1.0)) for r in rubric)
    overall_raw = 0.0
    for r in rubric:
        desc = r.get('description','')
        kw = r.get('keywords','') or ''
        w = max(0.0001, float(r.get('weight',1.0)))
        minw = r.get('min_words', None)
        maxw = r.get('max_words', None)
        ks = keyword_score(tokens, kw)
        ls = length_score(word_count, minw, maxw)
        ss = simple_semantic_score(transcript, desc + ' ' + kw)
        comp = 0.5*ss + 0.35*ks + 0.15*ls
        score_0_100 = round(comp * 100, 2)
        overall_raw += comp * w
        feedback = []
        if kw:
            found = [k.strip() for k in re.split('[,;|]', kw) if k.strip() and k.strip().lower() in set(tokens)]
            missing = [k.strip() for k in re.split('[,;|]', kw) if k.strip() and k.strip().lower() not in set(tokens)]
            feedback.append(f"Keywords found: {found}" )
            if missing:
                feedback.append(f"Keywords missing: {missing}")
        feedback.append(f"Semantic score (0-1): {round(ss,3)}")
        feedback.append(f"Length {word_count} words; length score (0-1): {round(ls,3)}")
        per.append({
            'criterion': r.get('criterion',''),
            'score': score_0_100,
            'weight': w,
            'keyword_score': round(ks,3),
            'semantic_score': round(ss,3),
            'length_score': round(ls,3),
            'feedback': ' | '.join(feedback)
        })
    overall = overall_raw / total_weight if total_weight>0 else 0.0
    overall_0_100 = round(overall * 100, 2)
    return {
        'overall_score': overall_0_100,
        'words': word_count,
        'per_criterion': per
    }

if __name__ == "__main__":
    sample_path = os.path.join(os.getcwd(), 'static', 'sample.txt')
    if os.path.exists(sample_path):
        with open(sample_path, 'r', encoding='utf-8') as f:
            transcript = f.read()
    else:
        transcript = "Hello, my name is Sample. I live with my family. I like science and cricket."
    result = score_transcript(transcript)
    print(json.dumps(result, indent=2))
