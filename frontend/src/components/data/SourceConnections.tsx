import React, {useEffect, useState} from 'react';
import axiosClient from '../../api/axiosClient';
import {Button} from '../ui/Button';
import {Card} from '../ui/Card';

export const SourceConnections:React.FC<{onImported:()=>Promise<void>;writable:boolean}>=({onImported,writable})=>{
  const [sources,setSources]=useState<any[]>([]);
  const [preview,setPreview]=useState<any>(null);
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState('');
  useEffect(()=>{axiosClient.get('/sources').then(r=>setSources(r.data)).catch(()=>setError('Could not load configured sources.'));},[]);
  const run=async(fn:()=>Promise<void>)=>{setBusy(true);setError('');try{await fn();}catch(e:any){setError(e.response?.data?.detail||'Connection failed.');}finally{setBusy(false);}};
  return <Card className="p-6 space-y-4"><h2 className="font-semibold">Database and API connections</h2>
    <p className="text-sm text-neutral-500">Import a snapshot from an approved company source. Preview the exact data before replacing the active dataset.</p>
    {!sources.length&&<p className="text-sm">No connections configured. Your administrator can add a read-only database table or HTTPS API source to this company.</p>}
    {sources.map(s=><div key={s.id} className="flex gap-3 justify-between items-center"><span className="text-sm">{s.name} · {s.type}</span><Button disabled={busy||!writable} variant="secondary" onClick={()=>run(async()=>{setPreview(null);setPreview((await axiosClient.post(`/sources/${encodeURIComponent(s.id)}/preview`,null,{timeout:120000})).data);})}>Preview source</Button></div>)}
    {error&&<p role="alert" className="text-sm text-red-600">{error}</p>}
    {preview&&<div className="space-y-3"><p className="text-sm">{preview.rows.toLocaleString()} rows · {preview.columns.length} columns · First 30 rows below</p><div className="max-h-72 overflow-auto"><table className="w-full text-xs text-left"><thead><tr>{preview.columns.map((c:string)=><th className="p-2" key={c}>{c}</th>)}</tr></thead><tbody>{preview.preview.map((r:any,i:number)=><tr key={i}>{preview.columns.map((c:string)=><td className="p-2 border-t" key={c}>{r[c]==null?'—':String(r[c])}</td>)}</tr>)}</tbody></table></div><p className="text-xs text-neutral-500">Import replaces the active dataset. A backup of the current dataset is saved under Share.</p><Button disabled={busy||!writable} onClick={()=>run(async()=>{await axiosClient.post('/sources/apply',{preview_id:preview.preview_id},{timeout:120000});setPreview(null);await onImported();})}>Import previewed snapshot</Button></div>}
  </Card>;
};
