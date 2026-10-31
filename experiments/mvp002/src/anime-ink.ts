/**
 * MVP-005: authored anime-style detail strokes in stable part-local UV.
 * Pure TypeScript source art; each semantic component keeps a transparent
 * independent texture, re-registered to every key-view contour.
 *
 * Scope: painterly detail/lookdev of the existing rig, NOT a claim of
 * generative, hand-illustrated, production-quality multi-view textures.
 */
type Angle = 0|90|180|270;
type XY=readonly [number,number];

const rgba=(r:number,g:number,b:number,a:number)=>'rgba('+r+','+g+','+b+','+a+')';
function path(ctx:CanvasRenderingContext2D,xy:readonly XY[],color:string,width:number,closed=false):void{
 ctx.beginPath();ctx.moveTo(xy[0][0],xy[0][1]);
 for(const [x,y] of xy.slice(1))ctx.lineTo(x,y);
 if(closed)ctx.closePath();
 ctx.lineCap='round';ctx.lineJoin='round';ctx.strokeStyle=color;ctx.lineWidth=width;ctx.stroke();
}
function oval(ctx:CanvasRenderingContext2D,x:number,y:number,rx:number,ry:number,color:string):void{
 ctx.beginPath();ctx.ellipse(x,y,rx,ry,0,0,2*Math.PI);ctx.fillStyle=color;ctx.fill();
}
function ribbon(ctx:CanvasRenderingContext2D,vertices:readonly XY[],color:string):void{
 ctx.beginPath();ctx.moveTo(vertices[0][0],vertices[0][1]);
 for(const [x,y] of vertices.slice(1))ctx.lineTo(x,y);
 ctx.closePath();ctx.fillStyle=color;ctx.fill();
}
function eye(ctx:CanvasRenderingContext2D,x:number,y:number,profile:boolean):void{
 const w=profile?.29:.245,h=.25;
 ctx.save();ctx.translate(x,y);
 // Eyes are authored as actual Alpha-only islands, not a white panel.
 ctx.beginPath();
 ctx.moveTo(-w,.025);
 ctx.bezierCurveTo(-w*.65,.27,w*.45,.30,w,.015);
 ctx.bezierCurveTo(w*.5,-.13,-w*.45,-.13,-w,.025);
 ctx.closePath();
 ctx.fillStyle='#faf4ed';ctx.fill();
 ctx.save();ctx.clip();
 const iris=ctx.createRadialGradient(.028,-.03,.014,.005,-.075,.21);
 iris.addColorStop(0,'#c6edf0');iris.addColorStop(.43,'#6195b7');iris.addColorStop(.76,'#39597f');iris.addColorStop(1,'#273854');
 oval(ctx,.023,-.075,.145,h,iris);
 oval(ctx,.024,-.087,.072,.163,'#29344f');
 oval(ctx,-.03,.060,.052,.063,'#fefefe');
 oval(ctx,.087,-.124,.026,.031,'#d5f5ff');
 path(ctx,[[-.19,-.05],[-.06,-.14],[.12,-.18]],rgba(157,188,212,.66),.013);
 ctx.restore();
 ctx.beginPath();ctx.moveTo(-w-.03,.033);ctx.bezierCurveTo(-w*.6,.35,w*.59,.37,w+.025,.07);
 ctx.strokeStyle='#30304a';ctx.lineWidth=.066;ctx.stroke();
 for(let j=0;j<3;j++){
  const xx=w*(.50+j*.24);
  path(ctx,[[xx,.18],[xx+.07,.25+.035*j]],'#32314a',.036);
 }
 path(ctx,[[-w+.065,-.14],[0,-.185],[w*.74,-.13]],'#935c74',.022);
 ctx.restore();
}
function fringe(ctx:CanvasRenderingContext2D,side:number):void{
 // Use curved groups to avoid the rectangular flat bangs from previous MVP.
 for(let i=0;i<8;i++){
   const x=-.79+i*.225+side*.03;
   const p:XY[]=[
     [x,.85-.03*(i%3)],
     [x+.11,.63],
     [x-.035,.20-.08*(i%2)],
     [x+.075,-.65+.11*(i%3)]
   ];
   path(ctx,p,rgba(20,30,58,.65),.030);
   path(ctx,[[x+.055,.69],[x+.09,.39],[x+.02,-.16]],rgba(206,215,251,.56),.022);
 }
 path(ctx,[[-.66,.75],[side*.025,.97],[.61,.74]],rgba(227,226,248,.66),.040);
 path(ctx,[[-.54,.57],[-.30,.72],[.12,.80],[.49,.54]],rgba(128,154,201,.43),.025);
 for(let x=-.64;x<.6;x+=.31)oval(ctx,x,.70,.027,.015,rgba(242,245,255,.35));
}
function longHair(ctx:CanvasRenderingContext2D,side:number,back:boolean):void{
 for(let i=0;i<10;i++){
   const x=-.72+i*.154;
   const drift=.09*Math.sin(i*2.5+side);
   path(ctx,[[x,.85],[x+drift,.40],[x-drift*.7,-.25],[x+.06,-.91]],rgba(20,30,66,.5),.033);
   path(ctx,[[x+.045,.70],[x+.07+drift,.26],[x+.055,-.48]],rgba(198,206,247,.37),.022);
 }
 path(ctx,[[-.60,.79],[-.16,.98],[.48,.81]],rgba(232,224,250,.53),.05);
 if(back){
   path(ctx,[[-.64,.44],[0,.76],[.67,.43]],rgba(106,123,173,.77),.032);
   path(ctx,[[-.36,.37],[-.44,-.73]],'#222c54',.028);
 }
}
function jacket(ctx:CanvasRenderingContext2D,side:number,back:boolean):void{
 if(back){
  ribbon(ctx,[[-.55,.75],[-.10,.61],[.06,.10],[-.11,-.76],[-.50,-.62]],rgba(27,40,74,.30));
  ribbon(ctx,[[.12,.64],[.52,.76],[.44,-.63],[.15,-.8],[-.01,.10]],rgba(24,33,65,.27));
  path(ctx,[[-.59,.76],[-.13,.54],[.33,.62],[.62,.76]],'#c3d4e0',.043);
  for(let y=.23;y>-.73;y-=.34)path(ctx,[[-.43,y],[.41,y+.02]],rgba(219,223,239,.28),.019);
 }else{
  ribbon(ctx,[[-.55,.85],[-.31,.52],[side*.10,.03],[-.05,-.67],[-.40,-.77]],'#485d87');
  ribbon(ctx,[[.57,.85],[.27,.57],[side*.10,.03],[.07,-.75],[.42,-.75]],'#435379');
  path(ctx,[[-.50,.85],[-.30,.52],[side*.1,-.08],[.02,-.78]],'#e3e8f0',.052);
  path(ctx,[[.52,.82],[.25,.53],[side*.10,-.08],[-.02,-.78]],'#263956',.046);
  for(let y=.20;y>-.82;y-=.22) {
    oval(ctx,side*.14+.09,y,.036,.032,'#dcc7a1');
    oval(ctx,side*.14+.082,y+.015,.012,.011,'#ffffff');
  }
  path(ctx,[[-.70,.70],[-.55,.15],[-.56,-.62]],rgba(227,239,255,.6),.022);
  path(ctx,[[.63,.68],[.54,.13],[.59,-.72]],rgba(37,48,76,.6),.024);
 }
}
function pleats(ctx:CanvasRenderingContext2D,side:number,back:boolean):void{
 path(ctx,[[-.65,.81],[.67,.80]],'#dfc5be',.050);
 for(let i=-3;i<=3;i++){
  const x=i*.24,dx=(i%2===0?.08:-.07);
  ribbon(ctx,[[x*.50,.72],[x*.53+.06,.70],[x+dx+.12,-.89],[x+dx-.06,-.88]],
   rgba(31,42,93,.20+(i%3)*.052));
  path(ctx,[[x*.53,.70],[x+dx,-.84]],i%2===0?'#8696c3':'#313c74',i%2===0?.034:.041);
  path(ctx,[[x*.53+.056,.59],[x+dx+.045,-.65]],rgba(219,224,247,.32),.019);
 }
 if(side)path(ctx,[[side*.25,.62],[side*.43,.12],[side*.58,-.78]],'#c6c3db',.029);
 if(back)path(ctx,[[-.73,-.68],[0,-.79],[.72,-.68]],'#e2d5d5',.03);
}
function face(ctx:CanvasRenderingContext2D,side:number,back:boolean):void{
 if(back)return;
 const blush=rgba(223,133,148,.17);
 oval(ctx,-.38,-.28,.16,.08,blush);oval(ctx,.37,-.26,.14,.08,blush);
 for(let i=0;i<5;i++){
  oval(ctx,-.42+i*.07,-.23,.010,.007,rgba(190,116,125,.33));
 }
 if(side){
  path(ctx,[[side*.25,.07],[side*.38,-.08],[side*.26,-.14]],'#ae7985',.026);
  path(ctx,[[side*.05,-.49],[side*.17,-.48],[side*.22,-.46]],'#a45f73',.029);
 }else{
  path(ctx,[[.025,.10],[-.018,-.055],[.067,-.113]],'#b98589',.018);
  path(ctx,[[-.18,-.49],[-.07,-.505],[.043,-.50],[.14,-.47]],'#9f6577',.034);
  oval(ctx,-.27,.47,.14,.095,rgba(255,244,218,.21));
 }
 // Linework near chin gives the face shape an authored anime contour.
 path(ctx,[[-.66,-.15],[-.48,-.67],[-.15,-.88],[.12,-.90],[.46,-.70]],rgba(158,98,103,.23),.022);
}
function garmentSmall(ctx:CanvasRenderingContext2D,id:string):void{
 if(id==='scarf'){
  ribbon(ctx,[[-.68,.34],[0,-.24],[.52,.26],[.35,.53],[0,.13],[-.35,.65]],'#e7b4c7');
  path(ctx,[[-.60,.42],[0,-.12],[.53,.30]],'#fae1df',.061);
  oval(ctx,-.07,.23,.18,.14,'#fae7de');
  oval(ctx,-.10,.29,.044,.027,'#fffef6');
  path(ctx,[[.04,.0],[.22,-.75]],'#a45d77',.037);
 }
 if(id==='emblem'){
  oval(ctx,0,0,.74,.75,'#b5a17b');oval(ctx,0,.03,.63,.61,'#f6e2a8');
  ribbon(ctx,[[0,.56],[.14,.13],[.54,.13],[.24,-.15],[.33,-.54],[0,-.30],
    [-.38,-.53],[-.23,-.1],[-.56,.19],[-.13,.17]],'#a86b77');
  oval(ctx,-.20,.30,.10,.07,'#fffdf0');
 }
 if(id.includes('Arm')){
  path(ctx,[[-.55,.62],[.56,.62]],'#d9dbe3',.11);
  path(ctx,[[-.53,-.35],[.55,-.35]],'#bf8397',.061);
  path(ctx,[[-.27,.48],[-.23,-.60]],rgba(253,246,239,.34),.04);
  path(ctx,[[.23,.48],[.28,-.58]],rgba(55,56,104,.42),.03);
 }
 if(id.includes('Leg')){
  path(ctx,[[-.60,-.34],[.59,-.35]],'#2e3c61',.18);
  path(ctx,[[-.36,.61],[-.26,-.27]],rgba(252,242,240,.37),.041);
  path(ctx,[[.25,.57],[.18,-.22]],rgba(120,102,120,.25),.025);
 }
}
export function paintAnimeDetails(ctx:CanvasRenderingContext2D,id:string,angle:Angle):void{
 const side=angle===90?1:angle===270?-1:0,back=angle===180;
 // Caller has installed the canonical part UV coordinate system/clip.
 ctx.save();
 if(id==='face')face(ctx,side,back);
 else if(id==='eyes'){
  if(!back){
   if(side)eye(ctx,side*.06,0,true);
   else{eye(ctx,-.43,0,false);eye(ctx,.43,0,false);}
   path(ctx,[[-.75,.73],[-.43,.79],[-.13,.72]],'#353b59',.062);
   if(!side)path(ctx,[[.15,.74],[.44,.79],[.75,.73]],'#353b59',.062);
  }
 }else if(id==='fringe')fringe(ctx,side);
 else if(id==='backHair')longHair(ctx,side,back);
 else if(id==='torso')jacket(ctx,side,back);
 else if(id==='skirt')pleats(ctx,side,back);
 else garmentSmall(ctx,id);
 ctx.restore();
}
