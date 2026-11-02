#!/usr/bin/env python3
"""Install the C05 anchor-view experiment into a C03-prepared official Cubism Web demo."""
from pathlib import Path
import argparse
import shutil

def main():
 p=argparse.ArgumentParser()
 p.add_argument('--samples',type=Path,required=True)
 p.add_argument('--adapter',type=Path,required=True)
 p.add_argument('--proxy',type=Path,required=True)
 a=p.parse_args()
 demo=a.samples.resolve()/'Samples/TypeScript/Demo'
 assert (demo/'src/r1999-three-adapter.ts').is_file(), 'Run prepare-c03.py first'
 for supplied,target in [(a.adapter,demo/'src/r1999-three-adapter.ts'),
                         (a.proxy,demo/'src/view-proxy.ts')]:
  if not supplied.is_file():raise FileNotFoundError(supplied)
  shutil.copy2(supplied,target)
 print('C05_ANCHOR_PROXY_PREPARED',{'demo':str(demo),'assets':'private','source':'Cubism'})
if __name__=='__main__': main()
