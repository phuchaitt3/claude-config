// Drives a throwaway VS Code over the DevTools protocol and reports where Markdown previews are scrolled.
// Why and results: findings/vscode-markdown-scroll-position-lost.md ("How to test again").
// Run (Windows, node 22+, VS Code user install), from an EMPTY temporary folder: node vscode_scroll_test.mjs <mode> [n]
//   repo       .vscode/settings.json as in the finding (draft.md must be text; a.md must come back to "section 30")
//   assoc      same two settings as user settings, plus edits on disk
//   assocprev  association only, preview tabs left on (expected: position lost)
//   open, lock Open Preview without / with locking. NOT VALID as written: the palette text may run another command.
// n only picks the debugging port (9340+n). A VS Code window appears for about a minute; delete the folder afterwards.
import fs from 'fs'; import path from 'path'; import {spawn} from 'child_process';
const S=process.cwd(), cond=process.argv[2]||'repo', port=9340+Number(process.argv[3]||0);
fs.mkdirSync('ws',{recursive:true});fs.rmSync('ws/.vscode',{recursive:true,force:true});
for(const n of ['a','b','draft']){let t='# file '+n+'\n\n';for(let i=1;i<=60;i++)t+=`## ${n} section ${i}\n\n`+'Some text for the section. '.repeat(20)+'\n\n- one\n- two\n\n';fs.writeFileSync(`ws/${n}.md`,t)}
if(cond==='repo'){fs.mkdirSync('ws/.vscode');fs.writeFileSync('ws/.vscode/settings.json',JSON.stringify({"workbench.editorAssociations":{"*.md":"vscode.markdown.preview.editor","**/{draft,read}.md":"default"},"workbench.editor.enablePreview":false}))}
const assoc={"workbench.editorAssociations":{"*.md":"vscode.markdown.preview.editor"}};
const base={"security.workspace.trust.enabled":false,"workbench.startupEditor":"none","telemetry.telemetryLevel":"off","update.mode":"none","extensions.autoUpdate":false,"chat.disableAIFeatures":true,"workbench.secondarySideBar.defaultVisibility":"hidden","window.restoreWindows":"none"};
const cfg={assoc:{...base,...assoc,"workbench.editor.enablePreview":false}, assocprev:{...base,...assoc}, open:{...base},repo:{...base}, lock:{...base,"workbench.editor.enablePreview":false}}[cond];
const ud=path.join(S,'ud-'+cond); fs.mkdirSync(path.join(ud,'User'),{recursive:true}); fs.writeFileSync(path.join(ud,'User','settings.json'),JSON.stringify(cfg));
const exe=path.join(process.env.LOCALAPPDATA,'Programs','Microsoft VS Code','Code.exe');
const env={...process.env}; for(const k of Object.keys(env)) if(/^(VSCODE_|ELECTRON_)/.test(k)) delete env[k];
const p=spawn(exe,['--user-data-dir',ud,'--extensions-dir',path.join(S,'ext-empty'),'--remote-debugging-port='+port,'--new-window','--skip-welcome','--skip-release-notes','--disable-gpu','--wait',path.join(S,'ws')],{env,stdio:'ignore'});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const list=async()=>{try{return await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()}catch{return []}};
async function conn(url){const w=new WebSocket(url);await new Promise((r,j)=>{w.onopen=r;w.onerror=j});let id=0,m=new Map();w.onmessage=e=>{const d=JSON.parse(e.data);if(d.id&&m.has(d.id)){m.get(d.id)(d);m.delete(d.id)}};
 const send=(method,params={})=>new Promise(r=>{const i=++id;m.set(i,r);w.send(JSON.stringify({id:i,method,params}));setTimeout(()=>r({timeout:1}),8000)});
 return {send,ev:async x=>{const r=await send('Runtime.evaluate',{expression:x,returnByValue:true,awaitPromise:true});return r.result?.result?.value??r.result?.exceptionDetails?.exception?.description},close:()=>w.close()}}
let pg;for(let i=0;i<60;i++){const t=(await list()).find(x=>x.type==='page'&&/workbench/.test(x.url));if(t){pg=await conn(t.webSocketDebuggerUrl);break}await sleep(1000)}
if(!pg){console.log('no page');p.kill();process.exit(1)}
for(let i=0;i<40;i++){if(await pg.ev(`!!document.querySelector('.explorer-folders-view .monaco-list-row')`))break;await sleep(1000)}
await sleep(6000);
async function click(sel,n=1){const r=await pg.ev(`(()=>{const e=${sel};if(!e)return null;const b=e.getBoundingClientRect();return {x:b.x+Math.min(40,b.width/2),y:b.y+b.height/2}})()`);if(!r||!r.x){console.log('no el',sel,r);return}
 for(const t of ['mousePressed','mouseReleased'])await pg.send('Input.dispatchMouseEvent',{type:t,x:r.x,y:r.y,button:'left',clickCount:n});await sleep(3000)}
const explorer=n=>click(`[...document.querySelectorAll('.explorer-folders-view .monaco-list-row')].find(e=>e.textContent.trim().startsWith('${n}.md'))`);
const tab=n=>click(`[...document.querySelectorAll('.tab')].find(e=>${n})`);
const tabs=()=>pg.ev(`[...document.querySelectorAll('.tab')].map(e=>e.getAttribute('aria-label')+(e.classList.contains('active')?' *':'')).join(' | ')`);
async function cmd(t){await pg.send('Input.dispatchKeyEvent',{type:'keyDown',key:'F1',code:'F1',windowsVirtualKeyCode:112});await pg.send('Input.dispatchKeyEvent',{type:'keyUp',key:'F1',code:'F1',windowsVirtualKeyCode:112});await sleep(1500);await pg.send('Input.insertText',{text:t});await sleep(2000);for(const y of ['keyDown','keyUp'])await pg.send('Input.dispatchKeyEvent',{type:y,key:'Enter',code:'Enter',windowsVirtualKeyCode:13});await sleep(3500)}
async function frames(x){const out=[];for(const t of await list()){if(!/vscode-webview/.test(t.url))continue;const c=await conn(t.webSocketDebuggerUrl);const v=await c.ev(`(()=>{const f=document.getElementById('active-frame');if(!f)return null;const w=f.contentWindow;if(!w.document.querySelector('h1'))return null;${x};const hs=[...w.document.querySelectorAll('h2')];const h=hs.find(e=>e.getBoundingClientRect().top>=-5);return {h1:w.document.querySelector('h1').textContent,y:Math.round(w.scrollY),top:h&&h.textContent,vis:w.innerHeight}})()`);if(v&&v.h1)out.push(v);c.close()}return JSON.stringify(out)}
const scroll=h=>frames(`const q=[...w.document.querySelectorAll('h2')].find(e=>e.textContent==='${h}');if(q)q.scrollIntoView()`);
const log=async l=>console.log(l.padEnd(46),await frames(''),'\n     tabs:',await tabs());
if(cond==='repo'){await explorer('draft');await log('draft (want text: no frame)');console.log('textEditor:',await pg.ev("!!document.querySelector('.editor-instance .view-lines')"));await explorer('a');await scroll('a section 30');await sleep(1500);await explorer('draft');await explorer('a');await log('a after draft, want 30');await explorer('b');await log('b');await explorer('a');await log('a, want 30');}else if(cond==='assoc'||cond==='assocprev'){
 await explorer('a');await log('open a');await scroll('a section 30');await sleep(1500);await log('a scrolled to 30');
 await explorer('b');await log('open b');await scroll('b section 12');await sleep(1500);
 await explorer('a');await log('back to a (explorer), want 30');
 await explorer('b');await log('back to b (explorer), want 12');
 await tab(`(e.getAttribute('aria-label')||'').startsWith('a.md')`);await log('back to a (tab), want 30');
 await tab(`(e.getAttribute('aria-label')||'').startsWith('b.md')`);
 fs.appendFileSync('ws/a.md','\nadded while hidden\n');await sleep(2500);
 await tab(`(e.getAttribute('aria-label')||'').startsWith('a.md')`);await log('a after edit on disk, want 30');
 fs.appendFileSync('ws/a.md','\nadded while shown\n');await sleep(3000);await log('a edited while shown, want 30');
 await explorer('b');await explorer('a');await log('a again, want 30');
}else{
 await explorer('a');await cmd('>Markdown: Open Preview');await log('text a + Open Preview');
 if(cond==='lock')await cmd('>Markdown: Toggle Preview Locking');
 await scroll('a section 30');await sleep(1500);await log('a preview scrolled to 30');
 await explorer('b');await log('click b');
 if(cond==='lock'){await cmd('>Markdown: Open Preview');await cmd('>Markdown: Toggle Preview Locking');await scroll('b section 12');await sleep(1500);await log('b preview scrolled to 12');}
 await tab(`/Preview/.test(e.getAttribute('aria-label')||'')`);await log('back to first preview tab, want a 30');
 await explorer('a');await log('click a text');
 await tab(`/Preview/.test(e.getAttribute('aria-label')||'')`);await log('back to first preview tab, want a 30');
}
await pg.send('Runtime.evaluate',{expression:'window.close()'});await sleep(2000);p.kill();process.exit(0);
