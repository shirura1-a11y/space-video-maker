import json, subprocess, sys
from pathlib import Path
import numpy as np
p=Path(sys.argv[1]);out=p.parent
meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(p)]))
v=next(s for s in meta['streams'] if s['codec_type']=='video');a=next(s for s in meta['streams'] if s['codec_type']=='audio')
layout=json.loads((out/'layout.json').read_text());preview='preview' in p.name
checks={'duration':65<=float(meta['format']['duration'])<=75,'resolution':[v['width'],v['height']]==([720,1280] if preview else [1080,1920]),'fps':v['avg_frame_rate']=='30/1','video_codec':v['codec_name']=='h264','audio_codec':a['codec_name']=='aac','subtitle_bounds':layout['subtitle_boxes_checked']>0}
# Full decode catches corrupt packets, not merely readable metadata.
subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(p),'-f','null','-'],check=True)
checks['full_decode']=True
samples={}
for t in [1,8,22,36,50,64]:
    raw=subprocess.check_output(['ffmpeg','-v','error','-ss',str(t),'-i',str(p),'-frames:v','1','-vf','scale=180:320','-f','rawvideo','-pix_fmt','rgb24','-'])
    pix=np.frombuffer(raw,dtype=np.uint8).reshape(320,180,3)
    # Exclude text: ensure the actual scene region contains luminous content.
    scene=pix[80:210];fraction=float(np.mean(np.max(scene,axis=2)>24));samples[str(t)]={'scene_lit_fraction':fraction,'mean':float(scene.mean())}
    checks[f'nonblack_{t}s']=fraction>.001
raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-vn','-f','f32le','-acodec','pcm_f32le','-'])
sound=np.frombuffer(raw,dtype='<f4');peak=float(np.max(np.abs(sound)));checks['audio_not_silent']=float(np.sqrt(np.mean(sound**2)))>.005;checks['audio_no_clipping']=peak<.99
report={'passed':all(checks.values()),'checks':checks,'duration_seconds':float(meta['format']['duration']),'bytes':p.stat().st_size,'resolution':[v['width'],v['height']],'fps':v['avg_frame_rate'],'audio_peak':peak,'scene_samples':samples,'note':'Final 68–70s fade is intentional; CG positions and sizes are schematic.'}
(out/'quality_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
if not report['passed']:sys.exit(1)
