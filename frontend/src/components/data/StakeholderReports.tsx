import React,{useEffect,useState} from 'react';
import axiosClient from '../../api/axiosClient';
import {Button} from '../ui/Button';
import {Card} from '../ui/Card';
import {Input,Textarea,Select} from '../ui/FormField';

export const StakeholderReports:React.FC<{records:any[];writable:boolean}>=({records,writable})=>{
  const [reports,setReports]=useState<any[]>([]),[selected,setSelected]=useState<number[]>([]);
  const [title,setTitle]=useState(''),[summary,setSummary]=useState(''),[detail,setDetail]=useState<any>(null);
  const [decision,setDecision]=useState('Reviewed'),[comment,setComment]=useState('');
  const [busy,setBusy]=useState(false),[error,setError]=useState(''),[message,setMessage]=useState('');
  const refresh=async()=>setReports((await axiosClient.get('/stakeholder-reports')).data);
  const load=async(id:number)=>setDetail((await axiosClient.get(`/stakeholder-reports/${id}`)).data);
  const run=async(fn:()=>Promise<void>)=>{setBusy(true);setError('');setMessage('');try{await fn();}catch(e:any){setError(typeof e.response?.data?.detail==='string'?e.response.data.detail:'Could not complete the report action.');}finally{setBusy(false);}};
  useEffect(()=>{run(async()=>{await refresh();const id=Number(new URLSearchParams(window.location.search).get('report'));if(id>0)await load(id);});},[]);
  const eligible=records.filter(r=>['brief','run','finding','comment','action_update','preparation'].includes(r.kind));
  return <Card className="p-6 space-y-4"><h2 className="font-semibold">Stakeholder reports</h2>
    <p className="text-sm text-neutral-500">Combine selected evidence into an immutable report with an executive summary and recorded reviews. Workspace links require company membership. Invite external stakeholders as Viewers in Company Settings.</p>
    {error&&<p role="alert" className="text-red-600">{error}</p>}{message&&<p role="status" className="text-emerald-700">{message}</p>}
    {writable&&<><label className="block text-sm">Report title<Input value={title} onChange={e=>setTitle(e.target.value)}/></label><label className="block text-sm">Executive summary<Textarea value={summary} onChange={e=>setSummary(e.target.value)}/></label>
    <fieldset className="max-h-48 overflow-auto space-y-2 border rounded-xl p-3"><legend className="text-sm px-2">Include evidence (up to 20 records)</legend>{eligible.map(r=><label className="flex gap-2 text-sm" key={r.id}><input type="checkbox" checked={selected.includes(r.id)} onChange={e=>setSelected(v=>e.target.checked?[...v,r.id]:v.filter(i=>i!==r.id))}/>{r.title} · {r.kind}{r.stale?' · historical':''}</label>)}{!eligible.length&&<p className="text-sm">Save a brief, analysis or finding first.</p>}</fieldset>
    <Button disabled={busy||!title.trim()||!summary.trim()||!selected.length||selected.length>20} onClick={()=>run(async()=>{const r=await axiosClient.post('/stakeholder-reports',{title,summary,record_ids:selected});await refresh();await load(r.data.id);setMessage('Report snapshot saved. Later analysis changes do not alter this report.');})}>Create report snapshot</Button></>}
    <div className="space-y-2">{reports.map(r=><div key={r.id} className="flex gap-3 justify-between border-t pt-3"><div><p className="font-medium">{r.title}</p><p className="text-xs text-neutral-500">{r.record_count} records · {r.historical?'Includes historical evidence':'Current source'} · {new Date(r.created_at).toLocaleString()}</p></div><Button size="sm" variant="secondary" disabled={busy} onClick={()=>run(()=>load(r.id))}>Open report</Button></div>)}</div>
    {detail&&<section className="rounded-xl border p-4 space-y-3"><h3 className="font-semibold">{detail.title}</h3><p className="whitespace-pre-wrap text-sm">{detail.summary}</p><p className="text-xs">Evidence: {detail.content.evidence.map((e:any)=>e.title).join('; ')}</p>
      <label className="block text-xs">Company-only report link<Input readOnly value={`${window.location.origin}/analysis?report=${detail.id}`}/></label>
      <Button variant="secondary" disabled={busy} onClick={()=>run(async()=>{const r=await axiosClient.get(`/stakeholder-reports/${detail.id}/download`,{responseType:'blob'});const url=URL.createObjectURL(r.data);const a=document.createElement('a');a.href=url;a.download=`datalyze-report-${detail.id}.html`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);})}>Download printable report</Button>
      <p className="text-xs text-neutral-500">Downloaded reports can be printed to PDF. Files you distribute are no longer protected by workspace login.</p>
      <h4 className="font-medium">Review history</h4>{detail.reviews.length?detail.reviews.map((r:any)=><p key={r.id} className="text-sm whitespace-pre-wrap">{r.decision} · Member #{r.author_id} · {new Date(r.created_at).toLocaleString()}<br/>{r.comment}</p>):<p className="text-sm text-neutral-500">No reviews recorded.</p>}
      {writable&&<><label className="block text-sm">Review decision<Select value={decision} onChange={e=>setDecision(e.target.value)}>{['Reviewed','Changes requested','Approved'].map(v=><option key={v}>{v}</option>)}</Select></label><label className="block text-sm">Review notes<Textarea value={comment} onChange={e=>setComment(e.target.value)}/></label><Button disabled={busy||!comment.trim()} onClick={()=>run(async()=>{await axiosClient.post(`/stakeholder-reports/${detail.id}/reviews`,{decision,comment});setComment('');await load(detail.id);})}>Record review</Button></>}
    </section>}
  </Card>;
};
