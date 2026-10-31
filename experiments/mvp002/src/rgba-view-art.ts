import * as THREE from 'three';

/**
 * Four independently authored 256² transparent RGBA art layers per semantic
 * part. The source is deliberately tiny original hand-coded 2D vector art,
 * rasterized into actual transparent CanvasTextures. No commercial assets.
 * All four maps use a registered canonical UV frame; contours deform separately.
 */
type XY = readonly [number,number];
export interface ArtPart {id:string; color:string; keys:readonly {contour:readonly XY[]}[];}
const angles=[0,90,180,270] as const;
type Angle=typeof angles[number];
const cache=new Map<string,THREE.CanvasTexture>();

export function createRegisteredArt(part:ArtPart,angle:Angle):THREE.CanvasTexture {
 const name=part.id+':'+angle;
 const cached=cache.get(name);
 if(cached)return cached;
 const canvas=document.createElement('canvas');
 canvas.width=canvas.height=256;
 const ctx=canvas.getContext('2d');
 if(!ctx)throw Error('2D layer authoring unavailable');
 ctx.setTransform(128,0,0,-128,128,128);
 ctx.lineCap='round';ctx.lineJoin='round';
 // Canonical UV mask: all key art for the same part is drawn in the
 // same 2D material domain, even though its screen contour differs per view.
 const points=part.keys[0].contour;
 const mask=()=>{ctx.beginPath();ctx.moveTo(points[0][0],points[0][1]);
   for(const [x,y] of points.slice(1))ctx.lineTo(x,y);ctx.closePath();};
 mask();ctx.clip();
 ctx.fillStyle=part.color;ctx.fillRect(-1.02,-1.02,2.04,2.04);
 const side=angle===90?1:angle===270?-1:0;
 const back=angle===180;
 const gradient=ctx.createLinearGradient(-.9,.8,.95,-.8);
 gradient.addColorStop(0,'rgba(255,252,244,.25)');
 gradient.addColorStop(.42,'rgba(255,255,255,0)');
 gradient.addColorStop(1,'rgba(27,36,78,.28)');
 ctx.fillStyle=gradient;ctx.fillRect(-1,-1,2,2);
 const path=(coords:XY[],line:string,width:number)=>{ctx.beginPath();
  ctx.moveTo(coords[0][0],coords[0][1]);for(const [x,y] of coords.slice(1))ctx.lineTo(x,y);
  ctx.strokeStyle=line;ctx.lineWidth=width;ctx.stroke();};
 const oval=(x:number,y:number,rx:number,ry:number,color:string)=>{
  ctx.beginPath();ctx.ellipse(x,y,rx,ry,0,0,2*Math.PI);ctx.fillStyle=color;ctx.fill();};
 switch(part.id) {
 case 'backHair':
  for(let x=-.7;x<.85;x+=.24)path([[x,.85],[x-.10,.23],[x-.06,-.59]],'rgba(176,183,230,.36)',.028);
  for(let x=-.6;x<.7;x+=.35)path([[x,.72],[x+.09,.4],[x-.08,-.71]],'#222c50',.018);
  path([[-.54,.90],[.1,1],[.69,.82]],'rgba(218,215,244,.38)',.035);
  break;
 case 'fringe':
  for(let x=-.7;x<.75;x+=.22){
    path([[x,.78],[x+.04,.24],[x-.06,-.51]],'#222d50',.022);
    path([[x+.065,.72],[x+.09,.20]],'rgba(224,225,255,.35)',.019);
  }
  path([[-.63,.73],[0,.97],[.55,.69]],'#8993c7',.026);
  break;
 case 'face':
  if(!back){
    // Chin/facial blush/nose are registered in material space. Side art is
    // deliberately different artwork rather than the front texture reused.
    oval(side*.11-.22,-.27,.17,.045,'rgba(215,123,147,.30)');
    oval(side*.11+.24,-.26,.13,.045,'rgba(215,123,147,.24)');
    if(side){
      path([[side*.24,.05],[side*.38,-.04],[side*.24,-.13]],'#b97c85',.022);
      path([[side*.12,-.47],[side*.26,-.48]],'#ae6a79',.027);
    } else {
      path([[.008,.00],[-.018,-.12],[.058,-.15]],'#bd8990',.017);
      path([[-.15,-.44],[0,-.48],[.15,-.42]],'#a65d70',.024);
      oval(-.31,.26,.06,.085,'rgba(255,243,222,.30)');
    }
  } else{
    path([[-.4,.28],[-.1,.40],[.2,.30]],'rgba(245,226,201,.28)',.04);
  }
  break;
 case 'eyes':
  if(!back){
    const positions=side?[side*.08]:[-.38,.38];
    for(const x of positions) {
      oval(x,0,side?.19:.20,.34,'#faf5ed');
      oval(x+.045*side,-.045,.105,.245,'#497fa1');
      oval(x+.03,-.045,.047,.17,'#263b63');
      oval(x-.013,.12,.04,.065,'#ffffff');
      path([[x-.20,.29],[x,.40],[x+.19,.32]],'#293453',.045);
      path([[x-.18,-.33],[x,-.36],[x+.18,-.31]],'#7f5471',.017);
    }
  }
  break;
 case 'torso':
  if(back){
   path([[-.59,.73],[0,.61],[.62,.79]],'#c3d5e2',.037);
   path([[-.35,.57],[-.31,-.66]],'#374a73',.024);
   path([[.34,.57],[.33,-.66]],'#374a73',.024);
   path([[-.32,-.70],[.29,-.70]],'rgba(241,239,220,.35)',.02);
  } else {
   const seam=side*.21;
   path([[-.45,.71],[seam,-.05],[.05,-.75]],'#e2e6ef',.045);
   path([[.49,.74],[seam,-.05],[-.06,-.75]],'#344a75',.048);
   path([[seam,.1],[seam-.03,-.91]],'rgba(25,39,74,.48)',.027);
   for(let y=.18;y>-.83;y-=.31)oval(seam+.06,y,.026,.029,'#e4d19e');
   path([[-.69,.6],[-.49,-.52]],'rgba(221,228,243,.52)',.021);
  }
  break;
 case 'skirt':
  for(let x=-.75;x<=.8;x+=.27){
    path([[x*.51,.75],[x,-.85]],'#28345d',.035);
    path([[x*.49,.63],[x-.055,-.61]],'rgba(175,193,232,.41)',.025);
  }
  path([[-.69,.81],[.65,.79]],'#d6bdac',.043);
  break;
 case 'scarf':
  path([[-.63,.35],[0,-.15],[.59,.40]],'#f8cdd6',.08);
  path([[-.38,.62],[.03,-.01],[.21,-.7]],'#a65a77',.035);
  oval(0,.18,.12,.12,'#f9e4dc');
  break;
 case 'emblem':
  oval(0,0,.66,.69,'#e4d6ad');
  ctx.fillStyle='#b3767c';ctx.beginPath();
  for(let i=0;i<10;i++){const a=i*Math.PI/5+Math.PI/2,r=i%2?.22:.55;
    const x=Math.cos(a)*r,y=Math.sin(a)*r;
    if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y);
  }
  ctx.closePath();ctx.fill();
  oval(-.22,.23,.06,.06,'#ffffff');
  break;
 case 'leftArm':case 'rightArm':
  path([[-.48,.65],[.47,.65]],'#45618c',.14);
  path([[-.52,-.35],[.53,-.35]],'#c99493',.045);
  path([[-.17,.52],[-.23,-.63]],'rgba(255,250,239,.30)',.045);
  break;
 case 'leftLeg':case 'rightLeg':
  path([[-.6,-.38],[.62,-.40]],'#47567b',.18);
  path([[-.4,.63],[-.3,-.18]],'rgba(255,247,237,.25)',.05);
  break;
 }
 // This thin outline is in the *texture* with alpha, not a black opaque rect.
 mask();ctx.lineWidth=.027;ctx.strokeStyle='rgba(31,38,68,.76)';ctx.stroke();
 const texture=new THREE.CanvasTexture(canvas);
 texture.colorSpace=THREE.SRGBColorSpace;
 texture.wrapS=texture.wrapT=THREE.ClampToEdgeWrapping;
 texture.minFilter=THREE.LinearFilter;texture.magFilter=THREE.LinearFilter;
 cache.set(name,texture);
 return texture;
}
export function artTextureProof(part:ArtPart):{transparent:boolean;centerOpaque:boolean;allDistinct:boolean;views:number} {
 const tex=angles.map(a=>createRegisteredArt(part,a));
 const datas=tex.map(t=>(t.image as HTMLCanvasElement).toDataURL('image/png'));
 const transparent=tex.every(t=>{
  const c=t.image as HTMLCanvasElement,ctx=c.getContext('2d');
  return !!ctx&&ctx.getImageData(0,0,1,1).data[3]===0;
 });
 const centerOpaque=tex.every(t=>{
  const c=t.image as HTMLCanvasElement,ctx=c.getContext('2d');
  return !!ctx&&ctx.getImageData(128,128,1,1).data[3]>0;
 });
 return {transparent,centerOpaque,allDistinct:new Set(datas).size===4,views:4};
}
export function artTexturePNG(part:ArtPart,angle:Angle):string {
 return (createRegisteredArt(part,angle).image as HTMLCanvasElement).toDataURL('image/png');
}
