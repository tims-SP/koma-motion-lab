import './main';
const shot=document.querySelector<HTMLSelectElement>('#shot');
const scrub=document.querySelector<HTMLInputElement>('#scrub');
const time=document.querySelector<HTMLOutputElement>('#time');
if(!shot||!scrub||!time)throw Error('Preview controls missing');
function draw():void{
 if(!shot||!scrub||!time)return;
 window.demoRender(shot.value as 'turn'|'action'|'fx',Number(scrub.value),72);
 time.textContent=scrub.value+' / 72';
}
shot.addEventListener('change',draw);
scrub.addEventListener('input',draw);
draw();
