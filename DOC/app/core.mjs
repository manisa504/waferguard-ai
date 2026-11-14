export function validateGrid(input) {
  const grid = Array.isArray(input) ? input : input?.wafer;
  if (!Array.isArray(grid) || grid.length < 1 || grid.length > 256) throw new Error('Use 1–256 rows.');
  const cols = grid[0]?.length;
  if (!Number.isInteger(cols) || cols < 1 || cols > 256) throw new Error('Use 1–256 columns.');
  let pass = 0, fail = 0, outside = 0;
  for (const row of grid) {
    if (!Array.isArray(row) || row.length !== cols) throw new Error('Every row must have the same number of columns.');
    for (const state of row) {
      if (!Number.isInteger(state) || state < 0 || state > 2) throw new Error('States must be integers: 0 outside, 1 pass, or 2 fail.');
      if (state === 0) outside++; else if (state === 1) pass++; else fail++;
    }
  }
  if (pass + fail === 0) throw new Error('The grid needs at least one inside-wafer cell.');
  return {grid, rows: grid.length, cols, pass, fail, outside, inside: pass + fail};
}
export function syntheticGrid(kind = 'line') {
  return Array.from({length:32},(_,r)=>Array.from({length:32},(_,c)=>{
    const x=c-15.5,y=r-15.5,d=Math.hypot(x,y);
    if(d>14.8)return 0;
    const failed=kind==='ring' ? d>11 && d<12.8 : kind==='scatter' ? (r*31+c*17)%23===0 : Math.abs(x-y*.35)<1.1 && Math.abs(y)<12;
    return failed?2:1;
  }));
}
export function createCase(summary, origin, title, id, now) {
  return {id, origin, title, createdAt: now, status: 'pending',
    summary: {rows:summary.rows,cols:summary.cols,pass:summary.pass,fail:summary.fail,outside:summary.outside}, notes:[]};
}
export function addNote(record, text, category, now) {
  if (typeof text !== 'string' || text.trim().length < 3 || text.trim().length > 1200) throw new Error('Write an observation of 3–1,200 characters.');
  if (!['observation','further-inspection','input-question'].includes(category)) throw new Error('Choose a research note category.');
  return {...record,status:'reviewed',notes:[...record.notes,{text:text.trim(),category,at:now}]};
}
