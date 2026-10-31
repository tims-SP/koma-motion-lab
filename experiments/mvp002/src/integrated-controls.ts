import './integrated';
const scrub=document.querySelector<HTMLInputElement>('#scrub');
const status=document.querySelector<HTMLOutputElement>('#status');
if(!scrub||!status)throw Error('Integrated controls missing');
scrub.addEventListener('input',()=>{
 const frame=Number(scrub.value),data=window.renderIntegrated(frame,144);
 status.textContent=frame+'/144  yaw '+data.yaw.toFixed(1)+'°  IK error '+data.ikError.toFixed(4)+'  depth '+data.handMinusTorsoDepth.toFixed(3);
});
