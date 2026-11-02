'use strict';
const $ = id => document.getElementById(id);
let token = sessionStorage.getItem('classroom-token') || '';
let room = '', current = null, history = [], refreshing = false, sending = false;
const text = (id, value) => { $(id).textContent = value; };
const pretty = s => s.toLowerCase().replaceAll('_', ' ').replace(/^./, c => c.toUpperCase());
const report = error => { text('error', error.message); $('error').classList.remove('hidden'); };
async function api(path, data) {
  const response = await fetch(path, {method: data ? 'POST' : 'GET', headers: {...(token ? {Authorization: `Bearer ${token}`} : {}), ...(data ? {'Content-Type':'application/json'} : {})}, ...(data ? {body:JSON.stringify(data)} : {}), signal:AbortSignal.timeout(8000)});
  if (!response.ok) { const body = await response.json().catch(() => ({})); throw new Error(response.status === 401 ? 'Enter your dashboard access token using Configure access token.' : `Request failed (${response.status}): ${typeof body.detail === 'string' ? body.detail : 'Check the input values.'}`); }
  return response.json();
}
function sensorsToForm(s) {
  for (const [id, key] of [['temp','temperature'],['humidity','humidity'],['light','light'],['air','air_quality']]) { $(`s-${id}`).value = s[key]; $(`s-${id}`).dispatchEvent(new Event('input')); }
  $('s-occupied').checked = s.occupancy; $('s-valid').checked = s.sensor_valid;
}
function render(s) {
  text('connection', s.online ? '● Live · receiving telemetry' : '○ Offline · showing last reading');
  text('presence', s.occupancy ? '● OCCUPIED' : '○ EMPTY');
  text('source', s.source === 'simulator' ? 'Software simulator · no physical device' : 'ESP32 · Wokwi');
  text('updated', `Updated ${new Date(s.received_at*1000).toLocaleTimeString()}`);
  text('alert', s.alert + (s.sensor_valid ? '' : ' · SENSOR FAULT')); $('alert').dataset.level = s.alert;
  for (const [id, key, unit] of [['temperature','temperature','°C'],['humidity','humidity','%'],['light','light','%'],['air','air_quality','/100']]) {
    $(id).replaceChildren(document.createTextNode(s[key].toFixed(1)+' '), Object.assign(document.createElement('small'),{textContent:unit}));
  }
  $('temp-bar').style.width = `${Math.max(0, Math.min(100, s.temperature*2))}%`;
  for (const [id,key] of [['humidity','humidity'],['light','light'],['air','air_quality']]) $(`${id}-bar`).style.width = `${s[key]}%`;
  text('humidity-caption', s.humidity>75 ? 'High humidity · ventilation advised' : 'Relative humidity');
  text('light-caption', `${s.light<40?'DARK':s.light<70?'NORMAL':'BRIGHT'} · normalized brightness`);
  text('air-caption', `${s.air_quality>=85?'DANGEROUS':s.air_quality>=60?'POOR':s.air_quality>=35?'MODERATE':'GOOD'} · simulated index`);
  text('power', s.power_w.toFixed(0)); text('actual',`${s.energy_wh.toFixed(3)} Wh`); $('actual').title=`${(s.energy_wh/1000).toFixed(6)} kWh`; text('baseline',`${s.baseline_wh.toFixed(3)} Wh`); text('auto-energy',`${s.auto_wh.toFixed(3)} Wh`);
  text('saving',`${(s.baseline_wh-s.energy_wh).toFixed(3)} Wh`); text('saving-percent',`${s.baseline_wh ? ((1-s.energy_wh/s.baseline_wh)*100).toFixed(1) : '0.0'}%`);
  const pending = s.command && s.command.version > s.applied_version;
  text('command-status',pending?'Command pending device acknowledgement':s.alarm?'Alarm active · resolve the hazard':'Device state acknowledged');
  $('auto-mode').classList.toggle('selected',s.mode==='AUTO'); $('manual-mode').classList.toggle('selected',s.mode==='MANUAL');
  text('mode-help',s.mode==='AUTO'?'Automatic rules respond to occupancy and room conditions.':'Manual controls active. Emergency overrides remain enabled.');
  for(const key of ['light1','light2','fan']) { $(key).checked = s[key]; $(key).disabled = s.mode!=='MANUAL'||pending||!s.online||sending; }
  if(document.activeElement!==$('servo')) $('servo').value=s.servo;
  $('servo').disabled = s.mode!=='MANUAL'||pending||!s.online||sending; text('servo-value',`${s.servo}°`);
  $('auto-mode').disabled = $('manual-mode').disabled = $('reset').disabled = pending||!s.online||sending;
  text('ml-class',pretty(s.ml_class)); text('confidence',`${(s.confidence*100).toFixed(1)}%`); $('confidence-bar').style.width=`${s.confidence*100}%`;
  text('ml-runtime',s.source==='esp32'?'Runtime: int8 TensorFlow Lite Micro on ESP32.':'Runtime: NumPy inference using the actual trained neural-network weights.');
  $('lab').querySelectorAll('input,button').forEach(el=>el.disabled=s.source!=='simulator');
}
async function refresh() {
  if(refreshing) return; refreshing=true;
  try {
    const rooms=await api('/api/rooms');
    if(!rooms.length) { text('connection','Waiting for first device telemetry'); return; }
    const previous=room; if(!rooms.some(s=>s.id===room)) room=rooms[0].id;
    $('room').replaceChildren(...rooms.map(s=>Object.assign(document.createElement('option'),{value:s.id,textContent:s.id,selected:s.id===room})));
    current=rooms.find(s=>s.id===room); render(current);
    if(previous!==room) sensorsToForm(current);
    history=await api(`/api/rooms/${encodeURIComponent(room)}/history`); drawChart(); $('error').classList.add('hidden');
  } catch(error) { report(error); text('connection','Connection interrupted · retrying'); } finally { refreshing=false; }
}
function drawChart() {
  const canvas=$('chart'), rect=canvas.getBoundingClientRect(), ratio=window.devicePixelRatio||1;
  canvas.width=rect.width*ratio; canvas.height=230*ratio; const ctx=canvas.getContext('2d'); ctx.scale(ratio,ratio);
  const w=rect.width,h=230,left=42,right=10,top=17,bottom=29,key=$('chart-metric').value;
  text('chart-name',$('chart-metric').selectedOptions[0].textContent);
  if(history.length<2) { ctx.fillStyle='#8a998b'; ctx.font='12px system-ui'; ctx.fillText('Collecting classroom readings…',left,h/2); return; }
  const values=history.map(s=>s[key]); let min=Math.min(...values),max=Math.max(...values); const pad=Math.max((max-min)*.2,key==='energy_wh'?.0001:2); min=Math.max(0,min-pad); max+=pad;
  const x=i=>left+i*(w-left-right)/(values.length-1), y=v=>top+(max-v)*(h-top-bottom)/(max-min);
  ctx.font='10px system-ui'; ctx.lineWidth=1;
  for(let i=0;i<=4;i++) { let val=min+(max-min)*i/4, yy=y(val); ctx.strokeStyle='#edf0e9';ctx.beginPath();ctx.moveTo(left,yy);ctx.lineTo(w-right,yy);ctx.stroke();ctx.fillStyle='#93a090';ctx.fillText(val.toFixed(key==='energy_wh'?3:0),1,yy+3); }
  let grad=ctx.createLinearGradient(0,top,0,h-bottom);grad.addColorStop(0,'#82b68b42');grad.addColorStop(1,'#82b68b03');ctx.fillStyle=grad;ctx.beginPath();ctx.moveTo(x(0),h-bottom);values.forEach((v,i)=>ctx.lineTo(x(i),y(v)));ctx.lineTo(x(values.length-1),h-bottom);ctx.closePath();ctx.fill();
  ctx.strokeStyle='#508768';ctx.lineWidth=2;ctx.beginPath();values.forEach((v,i)=>i?ctx.lineTo(x(i),y(v)):ctx.moveTo(x(i),y(v)));ctx.stroke();ctx.fillStyle='#93a090';
  [0,Math.floor((values.length-1)/2),values.length-1].forEach((i,n)=>{ctx.textAlign=n===0?'left':n===2?'right':'center';ctx.fillText(new Date(history[i].at*1000).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit',second:'2-digit'}),x(i),h-5);});
}
async function command(mode=current.mode, reset=false) {
  if(!current||sending) return; sending=true;
  try { await api(`/api/rooms/${encodeURIComponent(room)}/commands`,{mode,light1:$('light1').checked,light2:$('light2').checked,fan:$('fan').checked,servo:Number($('servo').value),reset_alarm:reset}); await refresh(); } catch(e) { report(e); } finally { sending=false; }
}
const presets={empty:[24,50,65,20,false,true],normal:[24,50,55,20,true,true],dark:[24,50,10,20,true,true],hot:[35,50,55,20,true,true],poor:[24,50,55,70,true,true],danger:[24,50,55,95,true,true],fault:[24,50,55,20,true,false]};
async function applySensors() { try { await api(`/api/rooms/${encodeURIComponent(room)}/sensors`,{temperature:Number($('s-temp').value),humidity:Number($('s-humidity').value),light:Number($('s-light').value),air_quality:Number($('s-air').value),occupancy:$('s-occupied').checked,sensor_valid:$('s-valid').checked}); await refresh(); } catch(e) { report(e); } }
for(const [id,unit] of [['temp',' °C'],['humidity',' %'],['light',' %'],['air','']]) $(`s-${id}`).addEventListener('input',()=>text(`s-${id}-label`,$(`s-${id}`).value+unit));
document.querySelectorAll('[data-preset]').forEach(button=>button.addEventListener('click',()=>{const p=presets[button.dataset.preset];sensorsToForm({temperature:p[0],humidity:p[1],light:p[2],air_quality:p[3],occupancy:p[4],sensor_valid:p[5]});applySensors();}));
$('sensor-form').addEventListener('submit',event=>{event.preventDefault();applySensors();});
$('auto-mode').addEventListener('click',()=>command('AUTO'));$('manual-mode').addEventListener('click',()=>command('MANUAL'));
for(const key of ['light1','light2','fan','servo']) $(key).addEventListener('change',()=>command());
$('servo').addEventListener('input',()=>text('servo-value',`${$('servo').value}°`));$('reset').addEventListener('click',()=>command(current.mode,true));
$('room').addEventListener('change',()=>{room=$('room').value;current=null;refresh().then(()=>{if(current)sensorsToForm(current);});});
$('chart-metric').addEventListener('change',drawChart);window.addEventListener('resize',drawChart);
$('connect').addEventListener('click',()=>$('token-dialog').showModal());
const mobileAccess=Object.assign(document.createElement('button'),{textContent:'Configure access token',className:'quiet mobile-access'});
mobileAccess.addEventListener('click',()=>$('token-dialog').showModal());
document.querySelector('.room-picker').append(mobileAccess);
$('save-token').addEventListener('click',event=>{event.preventDefault();token=$('access-token').value.trim();sessionStorage.setItem('classroom-token',token);$('access-token').value='';$('token-dialog').close();refresh();});
refresh();setInterval(refresh,2000);
