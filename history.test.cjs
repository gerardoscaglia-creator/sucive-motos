const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const html=fs.readFileSync('index.html','utf8');
const start=html.indexOf('function historyYears(');
const end=html.indexOf('function renderHist()',start);
assert.ok(start>=0,'calendar helper exists');
const ctx=vm.createContext({});vm.runInContext(html.slice(start,end),ctx);
const data={'2026-09':{total_pais:90},'2025-12':{total_pais:0},'2026-07':{total_pais:70}};
test('real sparse unordered snapshots produce twelve ordered months',()=>{
 const rows=ctx.historyMonths(data,2026,'2026-10');
 assert.equal(rows.length,12);assert.equal(rows[0].period,'2026-01');assert.equal(rows[11].period,'2026-12');
 assert.equal(rows[7].status,'Sin datos capturados');assert.equal(rows[8].data.total_pais,90);assert.equal(rows[10].status,'Mes futuro');
});
test('year changes preserve true zero and exclude other years',()=>{
 const rows=ctx.historyMonths(data,2025,'2026-10');assert.equal(rows[11].data.total_pais,0);assert.equal(rows[8].data,null);
});
test('year selector rolls forward automatically and includes next year',()=>{
 assert.equal(JSON.stringify(ctx.historyYears(data,2026)),JSON.stringify(['2025','2026','2027']));
 assert.ok(ctx.historyYears(data,2027).includes('2028'));
 assert.equal(ctx.historyMonths(data,2027,'2026-12').every(r=>r.status==='Mes futuro'),true);
 assert.equal(ctx.historyMonths(data,2027,'2027-01')[0].status,'Mes en curso');
 assert.equal(ctx.historyMonths(data,2027,'2027-02')[0].status,'Sin datos capturados');
 assert.equal(ctx.historyMonths(data,2026,'2026-10')[9].status,'Mes en curso');
});
test('comparison requires consecutive valid months and positive denominator',()=>{
 assert.equal(ctx.historyChange(90,null),null);assert.equal(ctx.historyChange(null,70),null);assert.equal(ctx.historyChange(10,0),null);
 assert.equal(ctx.historyChange(0,10).pct,-100);assert.equal(ctx.historyChange(15,10).pct,50);
});
test('actual renderer keeps gaps, filters and calendar comparisons',()=>{
 const code=html.slice(html.indexOf('let histYear=null;'),html.indexOf('/* ===== MI EMPRESA'));
 const el={innerHTML:''},configs=[];
 const ds={latest:'2026-09',prev:'2026-07',periods:['2026-09','2026-07'],track:['YUMBO'],by_period:{
  '2026-07':{total_pais:70,nac_marcas:{YUMBO:7},deptos:{Soriano:{total:10,marcas:{YUMBO:0}}}},
  '2026-09':{total_pais:90,nac_marcas:{YUMBO:9},deptos:{Soriano:{total:20,marcas:{YUMBO:2}}}}}};
 const sandbox={DS:ds,focus:'Soriano',PAIS:'País',fname:x=>x,fmt:String,pct:(a,b)=>a/b*100,COL:{YUMBO:'red'},
  document:{getElementById:()=>el},destroyCharts:()=>{},charts:[],hMarca:{},hTotal:{},hShare:{},Chart:function(_,c){configs.push(c);}};
 vm.runInNewContext(code+';renderHist();',sandbox);
 assert.equal((el.innerHTML.match(/<tr><td>2026-/g)||[]).length,12);
 assert.ok(el.innerHTML.includes('Sin datos<'));
 assert.ok(!el.innerHTML.includes('28.6%'));
 assert.equal(configs[0].data.datasets[0].data[6],0);
 assert.equal(configs[0].data.datasets[0].data[7],null);
 assert.equal(configs[0].data.datasets[0].spanGaps,false);
 assert.equal(configs[1].data.datasets[1].data[8],90);
});
test('banner compares the latest month with the calendar month before it',()=>{
 const code=html.slice(html.indexOf('let histYear=null;'),html.indexOf('/* ===== MI EMPRESA'));
 const render=(byPeriod,latest)=>{const el={innerHTML:''};
  vm.runInNewContext(code+';renderHist();',{DS:{latest,prev:null,periods:Object.keys(byPeriod).sort(),track:['YUMBO'],by_period:byPeriod},focus:'Soriano',PAIS:'País',fname:x=>x,fmt:String,pct:(a,b)=>a/b*100,COL:{YUMBO:'red'},
   document:{getElementById:()=>el},destroyCharts:()=>{},charts:[],hMarca:{},hTotal:{},hShare:{},Chart:function(){}});return el.innerHTML;};
 const s=(t,y)=>({total_pais:t,nac_marcas:{YUMBO:y},deptos:{Soriano:{total:t,marcas:{YUMBO:y}}}});
 const conAgosto=render({'2026-07':s(226,54),'2026-08':s(156,40),'2026-09':s(238,57)},'2026-09');
 assert.ok(conAgosto.includes('SUBIERON 52.6%'));assert.ok(conAgosto.includes('2026-09 vs 2026-08'));
 assert.ok(conAgosto.includes('▲ +53%'));assert.ok(conAgosto.includes('actual'));
 const sinAgosto=render({'2026-07':s(226,54),'2026-09':s(238,57)},'2026-09');
 assert.ok(!sinAgosto.includes('SUBIERON'));assert.ok(!sinAgosto.includes('vs 2026-07'));
});
