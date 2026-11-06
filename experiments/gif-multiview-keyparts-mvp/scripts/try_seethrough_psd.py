#!/usr/bin/env python3
"""Run See-through on recovered P0 reference and record native PSD/QA provenance.

Official upstream: https://github.com/shitagaki-lab/see-through
The external hosted inference is user-authorized and sends the P0 source image
to the provider. This optional test does not replace the approved source art.
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
from datetime import datetime,timezone
from gradio_client import Client,handle_file

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for x in iter(lambda:f.read(1024*1024),b""):h.update(x)
    return h.hexdigest()

def main(args):
    source=Path(args.input).resolve()
    out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=True)
    qa={
        "schema":"KOMA-P0-SEE-THROUGH-INFERENCE-QA-V1",
        "characterId":"p0_character_001",
        "recordedAtUTC":datetime.now(timezone.utc).isoformat(),
        "provider":"https://huggingface.co/spaces/24yearsold/see-through-demo",
        "upstreamSource":"https://github.com/shitagaki-lab/see-through",
        "upstreamCommit":"df019de5129d6c4b406587a14c3501669441a783",
        "input":{"path":str(source),"sha256":sha(source)},
        "settings":{"resolution":int(args.resolution),"seed":int(args.seed),
                    "splitLeftRight":bool(args.split)},
        "status":"SUBMITTED","sourceArtRole":"recovered P0 source reference",
        "artisticAcceptance":"PENDING"}
    dest=out/"inference-qa.json"
    def write():dest.write_text(json.dumps(qa,indent=2,ensure_ascii=False)+"\n")
    write()
    try:
        client=Client(args.space,verbose=False)
        response=client.predict(handle_file(str(source)),
                                int(args.resolution),int(args.seed),bool(args.split),
                                api_name="/inference")
        qa["outputType"]=type(response).__name__
        layers=response if isinstance(response,(list,tuple)) else [response]
        outputs=[]
        for i,item in enumerate(layers):
            if isinstance(item,str) and Path(item).is_file():
                origin=Path(item)
            elif isinstance(item,dict) and Path(item.get("path","")).is_file():
                origin=Path(item["path"])
            else:
                continue
            filename=origin.name
            if filename.lower().endswith(".psd"):
                filename="p0-character-001-see-through.psd"
            target=out/filename
            shutil.copy2(origin,target)
            outputs.append({"path":str(target),"bytes":target.stat().st_size,
                            "sha256":sha(target),"extension":target.suffix})
        qa["outputFiles"]=outputs
        qa["resultSummary"]=str(response)[:700]
        psd=[p for p in outputs if p["extension"].lower()==".psd"]
        qa["status"]="PSD_RECEIVED_AWAITING_LAYER_INSPECTION" if psd else "NO_PSD_IN_RETURN"
    except Exception as error:
        qa["status"]="INFERENCE_UNAVAILABLE"
        qa["exceptionType"]=type(error).__name__
        qa["errorDetail"]=str(error)[:1800]
    write()
    print(json.dumps({"status":qa["status"],"outputs":qa.get("outputFiles",[]),
                      "exceptionType":qa.get("exceptionType"),
                      "errorDetail":qa.get("errorDetail")},ensure_ascii=False,indent=2))
    return qa

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--space",default="https://24yearsold-see-through-demo.hf.space")
    p.add_argument("--resolution",type=int,default=768)
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--split",action="store_true")
    main(p.parse_args())
