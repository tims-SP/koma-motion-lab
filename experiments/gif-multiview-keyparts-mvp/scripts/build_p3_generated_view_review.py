#!/usr/bin/env python3
"""P0 five-view storyboard preview from three original GIF frames and two generated RGBA candidates."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image,ImageDraw

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for piece in iter(lambda:f.read(1024*1024),b""):
            h.update(piece)
    return h.hexdigest()

def compose(root,output):
    root=Path(root).resolve()
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    generated=root/"p3-native-source-trial"
    srcQA=json.loads((generated/"qa.json").read_text())
    assert srcQA["characterId"]=="p0_character_001"
    sourceList=[
      (0,root/"p1-front/diagnostics/front-reference.png","approved-design_P0_original_GIF_reference"),
      (22.5,generated/"yaw0225_whole.png","MiniMax_img2img_generated_RGBA_background_removal"),
      (45,root/"p2-views/whole/yaw045.png","approved-design_P0_original_GIF_reference"),
      (67.5,generated/"yaw0675_whole.png","MiniMax_img2img_generated_RGBA_background_removal"),
      (90,root/"p2-views/whole/yaw090.png","approved-design_P0_original_GIF_reference")
    ]
    originals={float(rec["yawDeg"]):rec for rec in srcQA["sourceGeneration"]["generatedOutputs"]}
    frames=[];registry=[];size=512
    for angle,path,role in sourceList:
        with Image.open(path) as im:
            if im.mode!="RGBA" or im.size!=(1024,1024):
                raise ValueError("P0 view must be RGBA 1024x1024 "+str(path))
            rgba=im.copy()
        alpha=rgba.getchannel("A")
        if any(alpha.getpixel(p)>0 for p in ((0,0),(1023,0),(0,1023),(1023,1023))):
            raise ValueError("P0 view transparent corners absent "+str(path))
        if angle in originals and originals[angle]["sha256"]!=sha(path):
            raise ValueError("Generated candidate SHA mismatch "+str(angle))
        matte=Image.new("RGBA",rgba.size,(43,55,71,255))
        matte.alpha_composite(rgba)
        view=matte.convert("RGB").resize((size,size),Image.Resampling.LANCZOS)
        frames.append(view)
        registry.append({"yawLabelDeg":angle,"sourceRole":role,"path":str(path.relative_to(root)),
                         "sha256":sha(path),"generatedAngleAccuracy":
                         "APPROXIMATE_PENDING_HUMAN_REVIEW" if angle in (22.5,67.5) else "AUTHOR_KEYFRAME"})
    sheet=Image.new("RGB",(size*5,560),(22,31,45));draw=ImageDraw.Draw(sheet)
    for i,frame in enumerate(frames):
        sheet.paste(frame,(i*size,0))
        draw.text((i*size+15,518),str(sourceList[i][0])+"°  "+("Generated" if i in (1,3) else "Original"),fill="white")
    sheet_path=output/"five-view-source-comparison.jpg"
    sheet.save(sheet_path,quality=91)
    palette_source=sheet.crop((0,0,size*5,size)).quantize(colors=254,
                                                   method=Image.Quantize.MEDIANCUT)
    pal=[im.quantize(palette=palette_source,dither=Image.Dither.NONE) for im in frames]
    seq=pal+pal[-2:0:-1]
    gif=output/"five-view-identity-storyboard.gif"
    seq[0].save(gif,save_all=True,append_images=seq[1:],duration=800,
                disposal=2,loop=0,optimize=True)
    with Image.open(gif) as opened:
        if opened.n_frames!=8:raise ValueError("Storyboard GIF frame mismatch")
    qa={"schema":"KOMA-P0-FIVE-VIEW-STORYBOARD-QA-V1",
      "characterId":"p0_character_001","status":"SOURCE_VIEW_CANDIDATES_READY_FOR_ART_REVIEW",
      "sourceReferences":registry,"canvas":[1024,1024],"storyboardResolution":[512,512],
      "outputContact":str(sheet_path),"contactSHA256":sha(sheet_path),
      "outputGIF":str(gif),"GIFSHA256":sha(gif),"GIFFrames":8,
      "generatedViewCount":2,"originalKeyframeCount":3,
      "generatedRGBAProduction":"JPG image-to-image then model-supported background removal",
      "angleFidelity":"PENDING_GENERATIVE_VIEW_CONSTRAINT_VALIDATION",
      "artisticAcceptance":"PENDING"}
    (output/"qa.json").write_text(json.dumps(qa,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({k:qa[k] for k in ("status","GIFFrames","GIFSHA256","contactSHA256",
                                       "angleFidelity","outputGIF")},indent=2,ensure_ascii=False))
    return qa

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True)
    p.add_argument("--out",required=True)
    args=p.parse_args()
    compose(args.root,args.out)
