"""Codex local fallback after mcode timeout and automatic-approval rejection."""

def group_and_pass(rows):
    groups=[]
    for surface in sorted({r['ultimate_surface_order'] for r in rows}):
        members=[r['psd_order'] for r in rows if r['ultimate_surface_order']==surface]
        runs=[]
        for n in members:
            if not runs or n!=runs[-1][-1]+1:runs.append([n])
            else:runs[-1].append(n)
        groups.append({'surface_order':surface,'members':members,'span':[members[0],members[-1]],
                       'gaps':[n for n in range(members[0],members[-1]+1) if n not in members],
                       'contiguous_runs':runs,'requires_multiple_painter_passes':len(runs)>1})
    passes=[];previous=None
    for row in rows:
        key=(row['ultimate_surface_order'],row['is_source_multiply'])
        if key!=previous:
            passes.append({'pass_index':len(passes)+1,'orders':[], 'surface_order':key[0],
                           'blend_policy':'MULTIPLY_SCENE_BACKDROP_REQUIRED' if key[1] else 'NORMAL_LOCAL'})
            previous=key
        passes[-1]['orders'].append(row['psd_order'])
    for group in groups:
        group['requires_multiple_painter_passes']=sum(p['surface_order']==group['surface_order'] for p in passes)>1
    return groups,passes
