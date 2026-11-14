import test from 'node:test';
import assert from 'node:assert/strict';
import {validateGrid,syntheticGrid,createCase,addNote} from '../../DOC/app/core.mjs';
test('grid contract counts categorical states without predicting labels',()=>{
 const result=validateGrid({wafer:[[0,1,2],[1,1,0]]});
 assert.deepEqual({rows:result.rows,cols:result.cols,pass:result.pass,fail:result.fail,outside:result.outside},{rows:2,cols:3,pass:3,fail:1,outside:2});
 assert.equal(result.inside,4);
});
test('rejects malformed, oversized, noncategorical, and all-outside input',()=>{
 for(const invalid of [[],[[0]],[[1],[1,2]],[[true]],[[1.5]],[[null]],[[3]],[[NaN]],Array.from({length:257},()=>[1]),[Array(257).fill(1)],{wafer:'grid'}])assert.throws(()=>validateGrid(invalid));
 assert.equal(validateGrid([[2]]).fail,1);
});
test('synthetic examples are deterministic valid grids, not benchmark cases',()=>{
 for(const kind of ['line','ring','scatter']){assert.deepEqual(syntheticGrid(kind),syntheticGrid(kind));const result=validateGrid(syntheticGrid(kind));assert.equal(result.rows,32);assert.ok(result.fail>0);assert.ok(result.pass>0);assert.ok(result.outside>0);}
});
test('notebook cases contain summaries, never raw grid cells',()=>{
 const summary=validateGrid(syntheticGrid());const record=createCase(summary,'synthetic','Line pattern','case-1','2026-11-14T12:00:00Z');
 assert.equal(record.origin,'synthetic');assert.equal(record.status,'pending');assert.deepEqual(record.notes,[]);assert.equal(record.grid,undefined);assert.equal(record.summary.grid,undefined);assert.equal(record.summary.wafer,undefined);
});
test('research observations append immutably and preserve provenance',()=>{
 const original=createCase(validateGrid([[1,2]]),'imported','Imported grid','case-2','2026-11-14T12:00:00Z');
 const updated=addNote(original,'Inspect the line structure.','further-inspection','2026-11-14T12:01:00Z');
 assert.equal(original.notes.length,0);assert.equal(original.status,'pending');assert.equal(updated.notes.length,1);assert.equal(updated.status,'reviewed');assert.equal(updated.origin,'imported');assert.equal(updated.createdAt,original.createdAt);assert.equal(updated.approved,undefined);
 assert.throws(()=>addNote(updated,'ab','observation','now'));
 assert.throws(()=>addNote(updated,'A valid observation.','approve','now'));
 assert.throws(()=>addNote(updated,'x'.repeat(1201),'observation','now'));
});
