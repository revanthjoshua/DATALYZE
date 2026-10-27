import React, {useEffect, useRef, useState} from 'react';
import axiosClient from '../../api/axiosClient';
import { checkUploadSize, getDataCapabilities } from '../../api/dataCapabilities';
import { formatByteLimit, type DataCapabilities } from '../../utils/payloadLimits';
import {Button} from '../ui/Button';
import {Card} from '../ui/Card';

type SavedDataset = {id:number;name:string;description:string;filename:string;rows:number;columns:string[];created_at:string;archived:boolean;version:number};
type SnapshotPreview = SavedDataset & {preview:Record<string,unknown>[]};
type JoinSettings = {revision:string;left_key:string[];right_key:string[];how:string;cardinality:string};
const fieldClass = 'w-full rounded-lg border border-neutral-200 bg-white p-2 text-sm text-neutral-900';

function PreviewTable({columns,rows}:{columns:string[];rows:Record<string,unknown>[]}) {
  return <div className="max-h-64 overflow-auto rounded-lg border border-neutral-200"><table className="w-full text-left text-xs"><thead><tr>{columns.map(column=><th key={column} className="p-2 whitespace-nowrap">{column}</th>)}</tr></thead><tbody>{rows.map((row,i)=><tr key={i}>{columns.map(column=><td className="border-t p-2" key={column}>{row[column]==null?'—':String(row[column])}</td>)}</tr>)}</tbody></table></div>;
}

export const DatasetLibrary:React.FC<{revision:string|null;onChanged:()=>Promise<void>;writable:boolean;columns:string[]}>=({revision,onChanged,writable,columns})=>{
  const [capabilities,setCapabilities]=useState<DataCapabilities|null>(null);
  const [datasets,setDatasets]=useState<SavedDataset[]>([]);
  const [name,setName]=useState('');
  const [description,setDescription]=useState('');
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState('');
  const [notice,setNotice]=useState('');
  const [showArchived,setShowArchived]=useState(false);
  const [selected,setSelected]=useState<SnapshotPreview|null>(null);
  const [joining,setJoining]=useState(false);
  const [keys,setKeys]=useState<{left:string;right:string}[]>([{left:'',right:''}]);
  const [how,setHow]=useState('left');
  const [cardinality,setCardinality]=useState('many_to_one');
  const [joinPreview,setJoinPreview]=useState<{result:any;settings:JoinSettings;datasetId:number}|null>(null);
  const uploadRef=useRef<HTMLInputElement>(null);
  const load=async()=>{setDatasets((await axiosClient.get('/datasets',{params:{include_archived:true}})).data);};
  useEffect(()=>{let active=true;load().catch(()=>{if(active)setError('Could not load saved datasets. Refresh the page to try again.');});getDataCapabilities().then(value=>{if(active)setCapabilities(value);}).catch(()=>{if(active)setCapabilities(null);});return()=>{active=false;};},[]);
  useEffect(()=>{setJoinPreview(null);},[revision,keys,how,cardinality,selected?.id]);
  const run=async(action:()=>Promise<void>)=>{
    setBusy(true);setError('');setNotice('');
    try{await action();}catch(err:any){const detail=err.response?.data?.detail;setError(typeof detail==='string'?detail:err.message||'The dataset operation could not be completed. Review the fields and try again.');}finally{setBusy(false);}
  };
  const show=async(dataset:SavedDataset)=>{setSelected((await axiosClient.get(`/datasets/${dataset.id}/preview`)).data);setJoining(false);setJoinPreview(null);setKeys([{left:columns[0]||'',right:dataset.columns[0]||''}]);};
  const saveActive=()=>run(async()=>{await axiosClient.post('/datasets/save',{name:name.trim(),description,revision});await load();setNotice('Active dataset saved as an immutable snapshot.');setName('');setDescription('');});
  const upload=async(file:File)=>run(async()=>{await checkUploadSize(file);const form=new FormData();form.append('file',file);form.append('name',name.trim()||file.name);form.append('description',description);await axiosClient.post('/datasets/upload',form,{timeout:120000});await load();setNotice('Dataset added to the library. The active dataset has not changed.');setName('');setDescription('');});
  const changeState=(dataset:SavedDataset)=>run(async()=>{const updated=(await axiosClient.post(`/datasets/${dataset.id}/state`,{archived:!dataset.archived,version:dataset.version})).data;await load();if(selected?.id===dataset.id){setSelected({...selected,...updated});setJoining(false);}setNotice(updated.archived?'Snapshot archived. You can restore it from Show archived.':'Snapshot restored.');});
  const activate=(dataset:SavedDataset)=>run(async()=>{await axiosClient.post(`/datasets/${dataset.id}/activate`,{revision:revision||''},{timeout:120000});await onChanged();await load();setJoinPreview(null);setNotice(`“${dataset.name}” is now active. The previous active source was backed up.`);});
  const download=(dataset:SavedDataset)=>run(async()=>{const response=await axiosClient.get(`/datasets/${dataset.id}/download`,{responseType:'blob'});const url=URL.createObjectURL(response.data);const link=document.createElement('a');link.href=url;link.download=`saved-dataset-${dataset.id}.csv`;link.click();window.setTimeout(()=>URL.revokeObjectURL(url),1000);setNotice('CSV downloaded. Formula-like text is escaped for spreadsheet safety.');});
  const previewJoin=()=>run(async()=>{if(!selected||!revision)return;const settings={revision,left_key:keys.map(key=>key.left),right_key:keys.map(key=>key.right),how,cardinality};const result=(await axiosClient.post(`/datasets/${selected.id}/join`,{...settings,apply:false},{timeout:120000})).data;setJoinPreview({result,settings,datasetId:selected.id});});
  const applyJoin=()=>run(async()=>{if(!joinPreview)return;await axiosClient.post(`/datasets/${joinPreview.datasetId}/join`,{...joinPreview.settings,apply:true},{timeout:120000});setJoinPreview(null);await onChanged();setNotice('Join applied. The previous active dataset was backed up; the saved lookup remains unchanged.');});
  return <Card className="p-6 space-y-4">
    <div><h2 className="font-semibold">Saved dataset library</h2><p className="mt-1 text-sm text-neutral-500">Keep named snapshots, switch the active source, and combine datasets with validated joins. Saved snapshots remain unchanged when you edit the active source.</p></div>
    {writable&&<div className="space-y-3 rounded-xl bg-neutral-50 p-4">
      <div className="grid gap-3 md:grid-cols-2"><label className="text-sm">Snapshot name<input aria-label="Snapshot name" className={fieldClass} value={name} maxLength={200} placeholder="For example, September sales" onChange={event=>setName(event.target.value)}/></label><label className="text-sm">Description (optional)<input aria-label="Snapshot description" className={fieldClass} value={description} maxLength={2000} onChange={event=>setDescription(event.target.value)}/></label></div>
      <div className="flex flex-wrap gap-2"><Button disabled={busy||!revision||!name.trim()} onClick={saveActive}>Save active dataset</Button><Button variant="secondary" disabled={busy} onClick={()=>uploadRef.current?.click()}>Add another file to library</Button></div>
      <input ref={uploadRef} type="file" className="hidden" aria-label="Upload saved dataset" accept=".csv,.tsv,.txt,.json,.jsonl,.xlsx,.xls,.parquet,.pq,.docx,.pdf" onChange={event=>{const file=event.target.files?.[0];if(file)void upload(file);event.target.value='';}}/>
      <p className="text-xs text-neutral-500">Up to 100 snapshots and 200 MB per company, including archived snapshots; 20 MB and 100,000 rows per stored snapshot.{capabilities&&<> Uploaded files are limited to {formatByteLimit(capabilities.max_upload_bytes)}{capabilities.max_response_bytes!==null?`; downloads must fit within ${formatByteLimit(capabilities.max_response_bytes)}`:''}.</>} Additional files enter the library without replacing the active source.</p>
    </div>}
    {error&&<p role="alert" className="text-sm text-red-600">{error}</p>}{notice&&<p role="status" className="text-sm text-emerald-700">{notice}</p>}
    <label className="inline-flex items-center gap-2 text-sm"><input type="checkbox" checked={showArchived} onChange={event=>setShowArchived(event.target.checked)}/>Show archived snapshots</label>
    {!datasets.filter(dataset=>showArchived||!dataset.archived).length&&<p className="text-sm text-neutral-500">No saved snapshots to show.</p>}
    <div className="space-y-3">{datasets.filter(dataset=>showArchived||!dataset.archived).map(dataset=><div key={dataset.id} className="rounded-lg border border-neutral-200 p-3"><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="font-medium">{dataset.name}{dataset.archived?' · Archived':''}</p><p className="text-xs text-neutral-500">{dataset.rows.toLocaleString()} rows · {dataset.columns.length} columns · {new Date(dataset.created_at).toLocaleString()}</p>{dataset.description&&<p className="mt-1 text-sm text-neutral-600">{dataset.description}</p>}</div><div className="flex flex-wrap gap-2"><Button variant="secondary" disabled={busy} onClick={()=>run(()=>show(dataset))}>Preview</Button><Button variant="secondary" disabled={busy} onClick={()=>download(dataset)}>Download CSV</Button>{writable&&<Button variant="secondary" disabled={busy} onClick={()=>changeState(dataset)}>{dataset.archived?'Restore':'Archive'}</Button>}</div></div></div>)}</div>
    {selected&&<div className="space-y-3 rounded-xl border border-neutral-200 p-4">
      <h3 className="font-medium">Preview: {selected.name}</h3><p className="text-xs text-neutral-500">First 30 of {selected.rows.toLocaleString()} rows.</p><PreviewTable columns={selected.columns} rows={selected.preview}/>
      {writable&&!selected.archived&&<><p className="text-sm text-neutral-500">Activation replaces the active dataset and recalculates its metrics. The previous active source is backed up; saved analyses retain their original source revision.</p><div className="flex flex-wrap gap-2"><Button disabled={busy} onClick={()=>activate(selected)}>Activate this snapshot</Button><Button variant="secondary" disabled={busy||!revision} onClick={()=>{setJoining(!joining);setJoinPreview(null);}}>Join with active dataset</Button></div></>}
      {joining&&writable&&!selected.archived&&<div className="space-y-3 border-t pt-4"><h3 className="font-medium">Join active data with {selected.name}</h3>{keys.map((key,index)=><div key={index} className="grid gap-2 sm:grid-cols-2"><label className="text-sm">Active key {index+1}<select className={fieldClass} value={key.left} aria-label={`Active join key ${index+1}`} onChange={event=>setKeys(keys.map((item,i)=>i===index?{...item,left:event.target.value}:item))}>{columns.map(column=><option key={column}>{column}</option>)}</select></label><label className="text-sm">Saved key {index+1}<select className={fieldClass} value={key.right} aria-label={`Saved join key ${index+1}`} onChange={event=>setKeys(keys.map((item,i)=>i===index?{...item,right:event.target.value}:item))}>{selected.columns.map(column=><option key={column}>{column}</option>)}</select></label></div>)}
        <div className="flex gap-2"><Button variant="secondary" disabled={busy||keys.length>=3} onClick={()=>setKeys([...keys,{left:columns[0]||'',right:selected.columns[0]||''}])}>Add key pair</Button>{keys.length>1&&<Button variant="secondary" disabled={busy} onClick={()=>setKeys(keys.slice(0,-1))}>Remove last pair</Button>}</div>
        <div className="grid gap-3 sm:grid-cols-2"><label className="text-sm">Join type<select className={fieldClass} aria-label="Saved dataset join type" value={how} onChange={event=>setHow(event.target.value)}><option value="left">Keep all active rows (left)</option><option value="inner">Keep matching rows (inner)</option><option value="outer">Keep rows from both sources (outer)</option></select></label><label className="text-sm">Expected relationship<select className={fieldClass} aria-label="Join relationship" value={cardinality} onChange={event=>setCardinality(event.target.value)}><option value="many_to_one">Many active rows to one saved row</option><option value="one_to_one">One active row to one saved row</option><option value="one_to_many">One active row to many saved rows</option></select></label></div>
        <p className="text-xs text-neutral-500">Key uniqueness is validated against the selected relationship. Review changed row counts before applying a join.</p><Button variant="secondary" disabled={busy||keys.some(key=>!key.left||!key.right)} onClick={previewJoin}>Preview saved dataset join</Button>
        {joinPreview&&<div className="space-y-3"><p className="text-sm">{joinPreview.result.rows_before?.toLocaleString()} → {joinPreview.result.rows_after?.toLocaleString()} rows · {joinPreview.result.matched_rows?.toLocaleString()} matching output rows</p>{joinPreview.result.notes?.map((note:string,index:number)=><p key={index} className="text-xs text-neutral-500">{note}</p>)}<PreviewTable columns={joinPreview.result.columns} rows={joinPreview.result.preview}/><Button disabled={busy} onClick={applyJoin}>Apply previewed join</Button></div>}
      </div>}
    </div>}
  </Card>;
};
