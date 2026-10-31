"""Codex local-fallback contract validation and schedule proposal."""
import copy
import re
from core026_compositor_groups import group_and_pass

def need(ok,message):
    if not ok:raise ValueError(message)

def build_schedule(records,default_shadow_clips,overlap_observations):
    need(isinstance(records,list) and len(records)==62,'Expected62 records')
    need([r['psd_order'] for r in records]==list(range(1,63)) and
         all(type(r['psd_order']) is int for r in records),'Integer source order1..62 required')
    uuids=[r['observed']['native_uuid'] for r in records]
    need(all(type(u) is int for u in uuids) and len(set(uuids))==62,'Unique integer source UUIDs required')
    need(isinstance(default_shadow_clips,list) and len(default_shadow_clips)==9,'Need9 derived shadow clips')
    receiver={};casters={}
    for r in records:
        n=r['psd_order'];o=r['observed'];d=r['design']
        need(type(o['psd_order']) is int and o['psd_order']==n,'Observed source identity differs')
        need(isinstance(r['texture_sha256'],str) and re.fullmatch('[0-9a-f]{64}',r['texture_sha256']) is not None,'Invalid source SHA')
        need(isinstance(o['native_blend_mode'],str) and isinstance(o['source_blend_mode'],str),'Blend names must be strings')
        for key in ['physical_depth','local_before_behind','local_mask']:need(d[key]=='UNKNOWN','Runtime geometry/mask falsely promoted')
        for key in ['receiver_order','shadow_caster_order']:
            v=d[key];need(v is None or type(v) is int and 1<=v<=62,'Invalid receiver/caster identity')
            need(v!=n,'Self receiver/caster reference')
        receiver[n]=d['receiver_order'];casters[n]=d['shadow_caster_order']
    need(sum(v is None for v in receiver.values())==19,'Need19 independent surfaces')
    def ultimate(n):
        seen=set()
        while receiver[n] is not None:
            need(n not in seen,'Receiver cycle');seen.add(n);n=receiver[n]
        return n
    native_clips=[r['psd_order'] for r in records if r['observed']['native_blend_mode']=='ClipToLower']
    need(native_clips==[28,29,38,39],'Native ClipToLower facts changed')
    multiply=[r['psd_order'] for r in records if 'MULTIPLY' in r['observed']['source_blend_mode']]
    need(len(multiply)==11 and 60 in multiply and 61 in multiply,'Multiply facts changed')
    schedule=[]
    for r in records:
        n=r['psd_order'];o=r['observed']
        schedule.append({'psd_order':n,'native_uuid':o['native_uuid'],'texture_sha256':r['texture_sha256'],
            'native_blend_mode':o['native_blend_mode'],'source_blend_mode':o['source_blend_mode'],
            'receiver_order':receiver[n],'ultimate_surface_order':ultimate(n),'shadow_caster_order':casters[n],
            'is_native_clip_to_lower':n in native_clips,'is_source_multiply':n in multiply,'physical_depth':'UNKNOWN'})
    groups,passes=group_and_pass(schedule)
    need([n for p in passes for n in p['orders']]==list(range(1,63)),'Passes changed painter order')
    face=next(g for g in groups if g['surface_order']==13)
    need(face['members']==list(range(13,44))+list(range(58,62)) and face['gaps']==list(range(44,58)),
         'Face late-paint/source groups changed')
    return {'schema':'core026-compositor-contract/1','status':'PASS_SOURCE_SCHEDULE_AND_PROPOSAL',
            'scope':'DEFAULT_PAINTER_SCHEDULE_ONLY','painter_schedule':schedule,'surface_groups':groups,
            'proposed_passes':passes,'native_clip_orders':native_clips,'source_multiply_orders':multiply,
            'default_shadow_clips':copy.deepcopy(default_shadow_clips),'overlap_observations':copy.deepcopy(overlap_observations),
            'runtime_receiver_compositor':'NOT_IMPLEMENTED','physical_depth':'UNKNOWN','natural_3d_turn':'NOT_ACCEPTED',
            'unknown_attachment_roots':True,'per_layer_eye_uv_motion_required':True,'global_head_bake_allowed':False,
            'runtime_dependencies':{'cross_surface_multiply':'UNRESOLVED_RUNTIME_VALIDATION',
                                    'cross_surface_transparency':'UNRESOLVED_RUNTIME_VALIDATION'}}
