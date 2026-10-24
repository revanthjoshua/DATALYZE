import React, {useCallback, useEffect, useState} from 'react';
import axiosClient from '../../api/axiosClient';
import {useAuth} from '../../context/AuthContext';
import {Card} from '../ui/Card';
import {Button} from '../ui/Button';

type Schedule = {source_id:string;enabled:boolean;interval_seconds:number;status:string;last_run_at:string|null;next_run_at:string;last_error:string|null};
type Status = {schedule:Schedule|null;worker_enabled:boolean;execution?:{mode:string;configured:boolean;minimum_interval_seconds:number;description:string};configuration_error:string|null;destinations:{id:string;name:string;type:string}[];notifications:{id:number;event:string;destination_id:string;status:string;attempts:number;created_at:string;last_error:string|null}[]};
const timestamp=(value:string|null)=>value?new Date(/Z$|[+-]\d\d:\d\d$/.test(value)?value:value+'Z').toLocaleString():'Not checked yet';

export const AutomationPanel:React.FC<{revision:string|null;onChanged?:()=>Promise<void>}>=({revision,onChanged})=>{
  const {user}=useAuth();
  const admin=['company admin','company_admin','admin','platform super admin','super_admin'].includes((user?.role||'').toLowerCase());
  const [status,setStatus]=useState<Status|null>(null);
  const [sources,setSources]=useState<{id:string;name:string;allow_refresh:boolean}[]>([]);
  const [sourceId,setSourceId]=useState('');
  const [minutes,setMinutes]=useState(60);
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState('');
  const [notice,setNotice]=useState('');
  const load=useCallback(async()=>{
    const [state,connections]=await Promise.all([axiosClient.get('/sources/automation/status'),axiosClient.get('/sources')]);
    setStatus(state.data);setSources(connections.data);
    if(state.data.execution?.mode==='vercel_daily') setMinutes(1440);
    else if(state.data.schedule) setMinutes(state.data.schedule.interval_seconds/60);
    setSourceId(current=>current||state.data.schedule?.source_id||connections.data.find((s:any)=>s.allow_refresh)?.id||'');
  },[]);
  useEffect(()=>{let mounted=true;load().catch(()=>{if(mounted)setError('Could not load automation status.');});return()=>{mounted=false;};},[load]);
  const run=async(fn:()=>Promise<void>)=>{setBusy(true);setError('');setNotice('');try{await fn();}catch(e:any){setError(e.response?.data?.detail||'Automation request failed.');}finally{setBusy(false);}};
  const save=async(enabled:boolean)=>{await axiosClient.put(`/sources/${encodeURIComponent(enabled?sourceId:status?.schedule?.source_id||sourceId)}/schedule`,{enabled,interval_seconds:Math.round(minutes*60),expected_revision:revision});await load();setNotice(enabled?'Refresh schedule saved. See scheduling availability and last check below for actual execution.':'Automatic refresh is disabled.');await onChanged?.();};
  return <Card className="p-6 space-y-4">
    <div className="flex flex-wrap justify-between gap-3"><h2 className="font-semibold">Automatic refresh and notifications</h2><Button variant="secondary" disabled={busy} onClick={()=>run(load)}>Refresh status</Button></div>
    <p className="text-sm text-neutral-500">Refresh reads your approved source on a schedule. It pauses when someone replaces or edits the active dataset so their work is preserved.</p>
    {status&&<p className="text-sm">{status.execution?.description||'Unattended scheduling availability is not reported by this server.'}</p>}
    {status?.schedule&&<div className="rounded-lg border border-neutral-200 p-3 text-sm space-y-1"><p>Source: {sources.find(s=>s.id===status.schedule?.source_id)?.name||status.schedule.source_id} · Status: <strong>{status.schedule.status}</strong></p><p>Last check: {timestamp(status.schedule.last_run_at)} · Requested interval: {status.schedule.interval_seconds/60} minutes</p>{status.schedule.enabled&&<p>Next eligible check: {timestamp(status.schedule.next_run_at)}</p>}{status.schedule.last_error&&<p role="status" className="text-amber-700">{status.schedule.last_error}</p>}</div>}
    {admin&&<div className="space-y-3"><div className="flex flex-wrap gap-3"><label className="text-sm">Approved source<select aria-label="Scheduled source" className="block border rounded p-2 mt-1" value={sourceId} onChange={e=>setSourceId(e.target.value)}><option value="">Choose a source</option>{sources.filter(s=>s.allow_refresh).map(s=><option key={s.id} value={s.id}>{s.name}</option>)}</select></label><label className="text-sm">{status?.execution?.mode==='vercel_daily'?'Daily interval (minutes)':'Check every (minutes)'}<input aria-label="Refresh interval minutes" className="block border rounded p-2 mt-1 w-40" type="number" min={status?.execution?.minimum_interval_seconds?status.execution.minimum_interval_seconds/60:5} max={1440} disabled={status?.execution?.mode==='vercel_daily'} value={minutes} onChange={e=>setMinutes(Number(e.target.value))}/></label></div>
      <p className="text-xs text-neutral-500">First import and review this source in Prepare. Enabling refresh authorizes this source to replace the active dataset; previous data is backed up in Share. One schedule is allowed per company.</p>
      <div className="flex flex-wrap gap-2"><Button disabled={busy||!sourceId||!revision||minutes<(status?.execution?.minimum_interval_seconds||300)/60||minutes>1440} onClick={()=>run(()=>save(true))}>Enable or resume refresh</Button>{status?.schedule?.enabled&&<Button variant="secondary" disabled={busy} onClick={()=>run(()=>save(false))}>Disable refresh</Button>}</div>
      {!sources.some(s=>s.allow_refresh)&&<p className="text-sm">No connection is approved for automatic refresh yet.</p>}
    </div>}
    <div className="border-t pt-4 space-y-2"><h3 className="font-medium text-sm">Notification delivery</h3><p className="text-sm text-neutral-500">Alerts, recoveries and refresh failures are queued for the destinations your administrator explicitly enables. Provider acceptance does not confirm inbox delivery.</p>
      {status?.configuration_error&&<p role="alert" className="text-red-600 text-sm">{status.configuration_error}</p>}
      {status&&!status.destinations.length&&<p className="text-sm">No notification destinations enabled.</p>}
      {status?.destinations.map(d=><p key={d.id} className="text-sm">{d.name} · {d.type}</p>)}
      {!!status?.notifications.length&&<div className="overflow-auto"><table className="w-full text-xs text-left"><thead><tr><th className="p-2">Event</th><th className="p-2">Destination</th><th className="p-2">Status</th><th className="p-2">Attempts</th></tr></thead><tbody>{status.notifications.map(n=><tr key={n.id}><td className="p-2 border-t">{n.event?.replace(/_/g,' ')}</td><td className="p-2 border-t">{status.destinations.find(d=>d.id===n.destination_id)?.name||n.destination_id}</td><td className="p-2 border-t">{n.status}{n.last_error&&<p className="text-amber-700 max-w-xs">{n.last_error}</p>}</td><td className="p-2 border-t">{n.attempts}</td></tr>)}</tbody></table></div>}
    </div>
    {error&&<p role="alert" className="text-sm text-red-600">{error}</p>}{notice&&<p role="status" className="text-sm text-green-700">{notice}</p>}
  </Card>;
};
