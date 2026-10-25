// Coletor da apuração presidencial 2026 (2º turno, eleição 6258) para rodar no Console do navegador,
// com a aba de resultados do TSE aberta (resultados.tse.jus.br). Lê Brasil, 27 UFs e Exterior, uma de cada vez.
// Se o Chrome bloquear a colagem, digite "allow pasting" e Enter antes. Depois de terminar, digite copy(__res).
(async()=>{
  const dec=t=>{t=t.trim();try{return JSON.parse(t)}catch(e){const b=t.split('.')[1].replace(/-/g,'+').replace(/_/g,'/');return JSON.parse(decodeURIComponent(escape(atob(b+'='.repeat((4-b.length%4)%4)))))}};
  const ufs=['br','ac','al','am','ap','ba','ce','df','es','go','ma','mg','ms','mt','pa','pb','pe','pi','pr','rj','rn','ro','rr','rs','sc','se','sp','to','zz'];
  const rows=['uf;hora;secoes_total;secoes_totalizadas;lula;flavio'];
  for(const uf of ufs){
    try{
      const j=dec(await(await fetch(`https://resultados.tse.jus.br/oficial/ele2026/6258/dados/${uf}/${uf}-c0001-e006258-u.jws`)).text());
      const c=[];const w=o=>{if(Array.isArray(o))o.forEach(w);else if(o&&typeof o==='object'){if(o.cand)o.cand.forEach(x=>c.push(x));Object.values(o).forEach(w)}};w(j);
      const v=n=>(c.find(x=>x.n===n)||{}).vap||0;
      rows.push([uf,j.dt+' '+j.ht,j.s.ts,j.s.st,v('13'),v('22')].join(';'));
    }catch(e){rows.push(uf+';erro;'+e)}
    await new Promise(r=>setTimeout(r,700));
  }
  window.__res=rows.join('\n');console.log(window.__res);
})()
