import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import axiosClient from '../api/axiosClient';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Input, Select, Textarea } from '../components/ui/FormField';
import { SourceConnections } from '../components/data/SourceConnections';
import { DatasetLibrary } from '../components/data/DatasetLibrary';
import { AutomationPanel } from '../components/data/AutomationPanel';
import { StakeholderReports } from '../components/data/StakeholderReports';

const tabs = ['Brief', 'Prepare', 'Explore', 'Investigate', 'Share', 'Monitor'] as const;
const format = (v: any) => v == null ? '—' : typeof v === 'number' ? v.toLocaleString(undefined, { maximumFractionDigits: 5 }) : typeof v === 'object' ? JSON.stringify(v) : String(v);
const Field: React.FC<{label:string; children:React.ReactNode}> = ({label,children}) => <label className="block space-y-1 text-xs font-medium"><span>{label}</span>{children}</label>;
const Table: React.FC<{rows:any[]}> = ({rows}) => {
  if (!rows?.length) return <p className="text-sm text-neutral-500">No rows to display.</p>;
  const cols = Object.keys(rows[0]);
  return <div className="overflow-auto max-h-96 rounded-xl border border-neutral-200 dark:border-neutral-800"><table className="w-full text-xs text-left"><thead className="sticky top-0 bg-neutral-100 dark:bg-neutral-900"><tr>{cols.map(c=><th className="p-3 whitespace-nowrap" key={c}>{c.replace(/_/g,' ')}</th>)}</tr></thead><tbody>{rows.map((row,i)=><tr className="border-t border-neutral-100 dark:border-neutral-800" key={i}>{cols.map(c=><td className="p-3 max-w-xs break-words" key={c}>{format(row[c])}</td>)}</tr>)}</tbody></table></div>;
};

export const AnalystWorkspacePage: React.FC = () => {
  const {user} = useAuth();
  const writable = ['company admin','company_admin','admin','platform super admin','super_admin','analyst','manager','employee'].includes((user?.role || '').toLowerCase());
  const [tab,setTab] = useState<typeof tabs[number]>(new URLSearchParams(window.location.search).has('report')?'Share':'Brief');
  const [profile,setProfile] = useState<any>(null);
  const [saved,setSaved] = useState<any[]>([]);
  const [busy,setBusy] = useState(false);
  const [message,setMessage] = useState('');
  const [error,setError] = useState('');
  const [brief,setBrief] = useState({title:'Business question',question:'',decision:'',success_measure:'',stakeholders:''});
  const [method,setMethod] = useState('aggregate');
  const [metric,setMetric] = useState('');
  const [dimension,setDimension] = useState('');
  const [dateColumn,setDateColumn] = useState('');
  const [aggregation,setAggregation] = useState('sum');
  const [baseline,setBaseline] = useState('');
  const [comparison,setComparison] = useState('');
  const [split,setSplit] = useState('');
  const [expression,setExpression] = useState('');
  const [result,setResult] = useState<any>(null);
  const [operation,setOperation] = useState('deduplicate');
  const [prepColumn,setPrepColumn] = useState('');
  const [prepValue,setPrepValue] = useState('');
  const [prepTarget,setPrepTarget] = useState('');
  const [filterOperator,setFilterOperator] = useState('eq');
  const [sortDirection,setSortDirection] = useState('asc');
  const [datePart,setDatePart] = useState('month');
  const [steps,setSteps] = useState<any[]>([]);
  const [cardinality,setCardinality] = useState('many_to_one');
  const [horizon,setHorizon] = useState('7');
  const [baselineStart,setBaselineStart] = useState('');
  const [comparisonEnd,setComparisonEnd] = useState('');
  const [drillColumn,setDrillColumn] = useState('');
  const [drillValue,setDrillValue] = useState('');
  const [preview,setPreview] = useState<any>(null);
  const [joinFile,setJoinFile] = useState<File|null>(null);
  const [joinKey,setJoinKey] = useState('');
  const [rightKey,setRightKey] = useState('');
  const [joinHow,setJoinHow] = useState('left');
  const [joinPreview,setJoinPreview] = useState<any>(null);
  const [finding,setFinding] = useState({title:'',text:'',owner:'',status:'Proposed',validation_measure:''});
  const [parent,setParent] = useState('');
  const [comment,setComment] = useState('');
  const [monitor,setMonitor] = useState<any>(null);
  const [ageLimit,setAgeLimit] = useState('24');
  const [missingLimit,setMissingLimit] = useState('10');
  const [metricName,setMetricName] = useState('');
  const [metricTarget,setMetricTarget] = useState('');
  const [metricAggregation,setMetricAggregation] = useState('sum');
  const [metricDirection,setMetricDirection] = useState('at_least');
  const [trackedMetrics,setTrackedMetrics] = useState<any[]>([]);
  const [actionId,setActionId] = useState('');
  const [actionStatus,setActionStatus] = useState('In progress');
  const [actionOutcome,setActionOutcome] = useState('');

  const refresh = async () => {
    const [p, docs] = await Promise.allSettled([axiosClient.get('/analysis/profile'),axiosClient.get('/analysis/records')]);
    if(p.status==='fulfilled') {
      const data=p.value.data;
      setProfile(data);
      setResult((current:any)=>current?{...current,stale:current.dataset_revision!==data.revision}:null);
      setMetric(v=>data.numeric_columns.includes(v)?v:data.numeric_columns[0]||'');
      setDimension(v=>data.columns.some((c:any)=>c.name===v)?v:data.columns.find((c:any)=>!data.numeric_columns.includes(c.name))?.name||data.columns[0]?.name||'');
      setDateColumn(v=>data.columns.some((c:any)=>c.name===v)?v:data.columns.find((c:any)=>/date|time|day/i.test(c.name))?.name||'');
      setPrepColumn(v=>data.columns.some((c:any)=>c.name===v)?v:data.columns[0]?.name||'');
      setJoinKey(v=>data.columns.some((c:any)=>c.name===v)?v:data.columns[0]?.name||'');
    } else { setProfile(null); if(p.reason.response?.status!==404) setError(p.reason.response?.data?.detail||'Could not load data profile.'); }
    if(docs.status==='fulfilled') setSaved(docs.value.data);
    else setError(docs.reason.response?.data?.detail||'Could not load saved workspace records.');
  };
  useEffect(()=>{refresh();},[user?.company_id]);
  useEffect(()=>{setPreview(null);},[operation,prepColumn,prepValue,prepTarget,filterOperator,sortDirection,datePart,steps,profile?.revision]);
  useEffect(()=>{setJoinPreview(null);},[joinFile,joinKey,rightKey,joinHow,cardinality,profile?.revision]);
  useEffect(()=>{
    if(!profile || tab!=='Monitor') return;
    axiosClient.get('/analysis/metrics').then(r=>setTrackedMetrics(r.data)).catch(()=>setError('Could not evaluate saved metric targets.'));
  },[tab,profile?.revision,saved.length]);
  useEffect(()=>{
    if(tab!=='Monitor'||!profile) return;
    let live=true;
    const load=()=>axiosClient.get('/analysis/monitor').then(r=>{if(live)setMonitor(r.data);}).catch(e=>{if(live)setError(e.response?.data?.detail||'Monitor refresh failed.');});
    load(); const timer=window.setInterval(load,60000);
    return ()=>{live=false;window.clearInterval(timer);};
  },[tab,profile?.revision]);

  const perform = async (fn:()=>Promise<void>) => {
    setBusy(true);setError('');setMessage('');
    try {await fn();} catch(e:any){setError(typeof e.response?.data?.detail==='string'?e.response.data.detail:e.message||'Request failed.');} finally {setBusy(false);}
  };
  const save = async (kind:string,title:string,content:any) => {
    await axiosClient.post('/analysis/records',{kind,title,content});
    await refresh();setMessage('Saved to your company workspace.');
  };
  const run = () => perform(async()=>{
    const parameters:any = method==='aggregate'?{metric,dimensions:[dimension],aggregation}:
      method==='formula'?{expression}:method==='compare'?{metric,dimension,baseline,comparison}:
      method==='investigate'?{metric,date_column:dateColumn,dimension,split_date:split,...(baselineStart?{baseline_start_date:baselineStart}:{}),...(comparisonEnd?{comparison_end_date:comparisonEnd}:{}),...(drillColumn?{filters:{[drillColumn]:drillValue}}:{})}:{metric,date_column:dateColumn,horizon:Number(horizon)};
    const r=await axiosClient.post('/analysis/run',{method,title:`${method==='formula'?'Formula':metric} · ${method}`,parameters},{timeout:120000});
    setResult(r.data); await refresh();setMessage('Analysis saved with its method and dataset revision.');
  });
  const preparationStep = () => ({operation,column:prepColumn,value:['in','not_in'].includes(filterOperator)&&operation==='filter'?prepValue.split(',').map(v=>v.trim()):prepValue,
    target:prepTarget,output:prepTarget,expression:prepValue,operator:filterOperator,direction:sortDirection,part:datePart});
  const prepare = (apply:boolean) => perform(async()=>{
    const request=apply?preview?.request:JSON.parse(JSON.stringify({revision:profile.revision,operations:steps.length?steps:[preparationStep()]}));
    if(!request) throw Error('Preview these changes before applying them.');
    const r=await axiosClient.post('/analysis/prepare',{...request,apply},{timeout:120000});
    setPreview({...r.data,request});if(apply){await refresh();setMessage('Preparation applied. The previous dataset is available as a backup under Share.');}
  });
  const join = (apply:boolean) => perform(async()=>{
    const request=apply?joinPreview?.request:{file:joinFile,left_key:joinKey,right_key:rightKey,how:joinHow,cardinality,dataset_revision:profile.revision};
    if(!request?.file) throw Error('Choose a lookup file and preview the join.');
    const data=new FormData();Object.entries(request).forEach(([key,value])=>data.append(key,value as string|Blob));data.append('apply',String(apply));
    const r=await axiosClient.post('/analysis/join',data,{timeout:120000});setJoinPreview({...r.data,request});
    if(apply){await refresh();setMessage('Join applied. A backup of the previous dataset is saved under Share.');}
  });
  const download = (row:any) => perform(async()=>{
    const r=await axiosClient.get(`/analysis/records/${row.id}/download`,{responseType:'blob'});
    const url=URL.createObjectURL(r.data);const a=document.createElement('a');a.href=url;a.download=`datalyze-${row.id}.${row.kind==='backup'?'csv':'html'}`;a.click();window.setTimeout(()=>URL.revokeObjectURL(url),1000);
  });
  const columns=profile?.columns||[];
  const selectColumn=(value:string,change:(v:string)=>void,numeric=false)=><Select value={value} onChange={e=>change(e.target.value)}><option value="">Choose a column</option>{(numeric?profile?.numeric_columns||[]:columns.map((c:any)=>c.name)).map((c:string)=><option key={c}>{c}</option>)}</Select>;
  const output=result?.content?.result;

  return <div className="space-y-5 text-neutral-900 dark:text-neutral-100">
    <header className="flex flex-wrap gap-4 justify-between items-start"><div><p className="text-xs uppercase tracking-widest text-neutral-500">From question to evidence</p><h1 className="text-2xl font-semibold mt-1">Analyst workspace</h1><p className="text-sm text-neutral-500 mt-2">Define the decision, prepare data, test explanations and share findings with your team.</p></div><Link to="/data" className="text-sm underline">Collect or replace data →</Link></header>
    <div className="flex flex-wrap gap-2" role="tablist" aria-label="Analysis workflow">{tabs.map((t,i)=><button role="tab" aria-selected={tab===t} key={t} onClick={()=>{setTab(t);setError('');setMessage('');}} className={`rounded-xl px-4 py-2 text-sm border ${tab===t?'bg-[#6B4226] text-white border-[#6B4226]':'border-neutral-200 dark:border-neutral-800'}`}>{i+1}. {t}</button>)}</div>
    {error&&<p role="alert" className="p-4 rounded-xl bg-red-50 text-red-700">{error}</p>}
    {message&&<p role="status" className="p-4 rounded-xl bg-emerald-50 text-emerald-800">{message}</p>}
    {profile&&<div className="flex flex-wrap justify-between gap-2 text-xs text-neutral-500"><span>{profile.filename} · {profile.rows.toLocaleString()} rows · {columns.length} columns</span><button onClick={()=>perform(refresh)} disabled={busy} className="underline">Refresh source and records</button></div>}
    {tab==='Prepare'&&<><DatasetLibrary revision={profile?.revision||null} columns={columns.map((c:any)=>c.name)} writable={writable} onChanged={refresh}/><SourceConnections onImported={refresh} writable={writable}/></>}
    {tab==='Share'&&<StakeholderReports records={saved} writable={writable}/>}
    {tab==='Monitor'&&<AutomationPanel revision={profile?.revision||null} onChanged={refresh}/>}
    {tab==='Investigate'&&method==='formula'&&profile&&<Card className="p-5 space-y-3"><h2 className="font-semibold">Track this formula against a target</h2><p className="text-sm text-neutral-500">Uses the formula entered below. Saved definitions are recalculated on the active dataset under Monitor.</p><div className="grid md:grid-cols-2 gap-3"><Field label="Metric name"><Input value={metricName} onChange={e=>setMetricName(e.target.value)}/></Field><Field label="Numeric target"><Input type="number" value={metricTarget} onChange={e=>setMetricTarget(e.target.value)}/></Field><Field label="Summarize formula rows"><Select value={metricAggregation} onChange={e=>setMetricAggregation(e.target.value)}><option value="sum">Sum</option><option value="mean">Mean</option></Select></Field><Field label="Target direction"><Select value={metricDirection} onChange={e=>setMetricDirection(e.target.value)}><option value="at_least">At least</option><option value="at_most">At most</option></Select></Field></div><Button disabled={busy||!writable||!metricName.trim()||!expression.trim()||!metricTarget} onClick={()=>perform(()=>save('metric_rule',metricName,{expression,target:Number(metricTarget),aggregation:metricAggregation,direction:metricDirection}))}>Save metric and target</Button></Card>}
    {tab==='Share'&&saved.some(r=>r.kind==='finding')&&<Card className="p-5 space-y-3"><h2 className="font-semibold">Record action progress</h2><p className="text-sm text-neutral-500">Updates retain the original finding and add a dated record of the decision or measured outcome.</p><Field label="Action to update"><Select value={actionId} onChange={e=>setActionId(e.target.value)}><option value="">Choose a finding</option>{saved.filter(r=>r.kind==='finding').map(r=><option key={r.id} value={r.id}>#{r.id} · {r.title}</option>)}</Select></Field><Field label="Updated status"><Select value={actionStatus} onChange={e=>setActionStatus(e.target.value)}>{['Proposed','Approved','In progress','Completed','Rejected'].map(v=><option key={v}>{v}</option>)}</Select></Field><Field label="Outcome or reason"><Textarea value={actionOutcome} onChange={e=>setActionOutcome(e.target.value)}/></Field><Button disabled={busy||!writable||!actionId} onClick={()=>perform(async()=>{await axiosClient.post(`/analysis/records/${actionId}/progress`,{status:actionStatus,outcome:actionOutcome});await refresh();setMessage('Action update recorded.');})}>Save action update</Button></Card>}
    {tab==='Monitor'&&profile&&<Card className="p-5 space-y-3"><h2 className="font-semibold">Formula metrics and targets</h2><Table rows={trackedMetrics}/>{!trackedMetrics.length&&<p className="text-sm text-neutral-500">Save a formula and target under Investigate to track it here.</p>}</Card>}
    {!profile&&tab!=='Brief'&&tab!=='Share'&&<Card className="p-6"><p>Upload a dataset to use this stage.</p><Link className="underline" to="/data">Open data collection</Link></Card>}

    {tab==='Brief'&&<div className="grid lg:grid-cols-2 gap-5"><Card className="p-6 space-y-4"><h2 className="font-semibold">What decision should this analysis support?</h2>{(['title','question','decision','success_measure','stakeholders'] as const).map(key=><Field key={key} label={key.replace(/_/g,' ')}><Textarea value={brief[key]} onChange={e=>setBrief({...brief,[key]:e.target.value})}/></Field>)}<Button disabled={!writable||busy||!brief.question.trim()} onClick={()=>perform(()=>save('brief',brief.title,brief))}>Save business brief</Button></Card><div className="space-y-3"><p className="text-sm text-neutral-500">Include the business question, the decision owner, a measurable target and who needs the result. Saved briefs remain available when data changes.</p>{saved.filter(r=>r.kind==='brief').map(row=><Card key={row.id} className="p-5 space-y-2"><h3 className="font-semibold">{row.title}</h3><p className="text-sm whitespace-pre-wrap">{row.content.question}</p><p className="text-xs text-neutral-500">Success: {row.content.success_measure||'Not defined'}</p><Button size="sm" variant="secondary" onClick={()=>setBrief({...brief,...row.content,title:row.title})}>Use as a starting point</Button></Card>)}</div></div>}

    {tab==='Explore'&&profile&&<div className="space-y-5"><div className="grid sm:grid-cols-3 gap-4">{[['Rows',profile.rows],['Missing cells',profile.missing_cells],['Duplicate rows',profile.duplicates]].map(([name,value])=><Card key={name} className="p-5"><p className="text-sm text-neutral-500">{name}</p><p className="text-2xl font-semibold">{format(value)}</p></Card>)}</div><div className="grid lg:grid-cols-2 gap-4">{columns.map((col:any)=><Card key={col.name} className="p-5 space-y-3"><h3 className="font-semibold">{col.name}</h3><p className="text-xs text-neutral-500">{col.dtype} · {col.missing} missing · {col.unique} distinct</p>{col.histogram&&<ResponsiveContainer width="100%" height={160}><BarChart data={col.histogram.map((x:any)=>({...x,label:`${format(x.from)}–${format(x.to)}`}))}><XAxis dataKey="label" hide/><YAxis/><Tooltip/><Bar dataKey="count" fill="#8C5E3C"/></BarChart></ResponsiveContainer>}{col.statistics&&<Table rows={[col.statistics]}/>}<Table rows={col.top_values}/></Card>)}</div><Card className="p-5 space-y-3"><h2 className="font-semibold">Correlation matrix</h2><p className="text-sm text-neutral-500">Pairwise Pearson correlations, at least three observations per pair. Correlation does not establish cause.</p><Table rows={profile.correlations}/></Card></div>}

    {tab==='Prepare'&&profile&&<div className="space-y-5"><Card className="p-6 space-y-4"><h2 className="font-semibold">Clean and transform</h2><p className="text-sm text-neutral-500">Build a sequence of up to 20 steps and preview their combined effect. Applying the sequence saves a backup and updates the active dataset.</p><div className="grid md:grid-cols-3 gap-4"><Field label="Operation"><Select value={operation} onChange={e=>setOperation(e.target.value)}>{[['deduplicate','Remove duplicate rows'],['trim','Trim surrounding whitespace'],['drop_missing','Remove rows missing this column'],['fill_mean','Fill missing numbers with mean'],['fill_median','Fill missing numbers with median'],['fill_value','Fill missing values with a constant'],['numeric','Convert to numbers'],['date','Convert to dates (UTC)'],['filter_equal','Keep rows equal to a value'],['rename','Rename column'],['drop_column','Remove column'],['sort','Sort rows'],['lower','Lowercase text'],['upper','Uppercase text'],['replace','Replace literal text'],['filter','Filter rows'],['date_part','Extract date part'],['derive','Add calculated column']].map(([v,l])=><option key={v} value={v}>{l}</option>)}</Select></Field><Field label="Column">{selectColumn(prepColumn,setPrepColumn)}</Field><Field label="Value (constant or filter)"><Input value={prepValue} onChange={e=>setPrepValue(e.target.value)}/></Field>{['replace','date_part','derive'].includes(operation)&&<Field label={operation==='replace'?'Replacement text':'New column name'}><Input value={prepTarget} onChange={e=>setPrepTarget(e.target.value)}/></Field>}{operation==='filter'&&<Field label="Comparison"><Select value={filterOperator} onChange={e=>setFilterOperator(e.target.value)}>{['eq','ne','gt','gte','lt','lte','contains','starts_with','ends_with','in','not_in'].map(v=><option key={v}>{v}</option>)}</Select></Field>}{operation==='sort'&&<Field label="Direction"><Select value={sortDirection} onChange={e=>setSortDirection(e.target.value)}><option value="asc">Ascending</option><option value="desc">Descending</option></Select></Field>}{operation==='date_part'&&<Field label="Date part"><Select value={datePart} onChange={e=>setDatePart(e.target.value)}>{['year','quarter','month','week','weekday','day'].map(v=><option key={v}>{v}</option>)}</Select></Field>}</div><p className="text-xs text-neutral-500">For a calculated column, enter the arithmetic formula in Value. For rename, enter the new name in Value. List filters use comma-separated values.</p><div className="flex flex-wrap gap-3"><Button variant="secondary" disabled={busy||!writable||steps.length>=20} onClick={()=>setSteps(v=>[...v,preparationStep()])}>Add step to sequence</Button><Button variant="secondary" disabled={busy||!steps.length} onClick={()=>setSteps([])}>Clear sequence</Button></div>{steps.length>0&&<><p className="text-xs">The preview will use these queued steps:</p><Table rows={steps.map((s,i)=>({step:i+1,operation:s.operation,column:s.column,value:s.value,output:s.output}))}/></>}<p className="text-xs text-neutral-500">Type conversion turns unparseable values into missing values. Numeric imputation applies after numeric conversion; review the preview carefully.</p><div className="flex gap-3"><Button disabled={busy||!writable} onClick={()=>prepare(false)}>Preview change</Button><Button variant="secondary" disabled={busy||!writable||!preview||preview.applied} onClick={()=>prepare(true)}>Apply previewed change</Button></div>{preview&&<><p className="text-sm">{preview.rows_before} → {preview.rows_after} rows · showing the first 30 rows</p><Table rows={preview.preview}/></>}</Card><Card className="p-6 space-y-4"><h2 className="font-semibold">Join a lookup dataset</h2><p className="text-sm text-neutral-500">Combine the active dataset with another file. Choose the expected key relationship. Many-to-many joins can multiply rows; the preview shows the expansion and rejects results above 100,000 rows.</p><Field label="Lookup file"><input type="file" onChange={e=>setJoinFile(e.target.files?.[0]||null)}/></Field><div className="grid md:grid-cols-3 gap-4"><Field label="Active dataset key">{selectColumn(joinKey,setJoinKey)}</Field><Field label="Exact lookup column name"><Input value={rightKey} onChange={e=>setRightKey(e.target.value)}/></Field><Field label="Join type"><Select value={joinHow} onChange={e=>setJoinHow(e.target.value)}><option value="left">Keep all active rows</option><option value="inner">Keep matches only</option><option value="outer">Keep both datasets</option></Select></Field><Field label="Key relationship"><Select value={cardinality} onChange={e=>setCardinality(e.target.value)}>{[["many_to_one","Many to one (lookup)"],["one_to_one","One to one"],["one_to_many","One to many"],["many_to_many","Many to many"]].map(([v,l])=><option value={v} key={v}>{l}</option>)}</Select></Field></div><div className="flex gap-3"><Button disabled={busy||!writable||!joinFile||!rightKey} onClick={()=>join(false)}>Preview join</Button><Button variant="secondary" disabled={busy||!writable||!joinPreview||joinPreview.applied} onClick={()=>join(true)}>Apply previewed join</Button></div>{joinPreview&&<><p className="text-sm">{joinPreview.rows_after} output rows · {joinPreview.matched_rows} matched rows</p><Table rows={joinPreview.preview}/></>}</Card></div>}

    {tab==='Investigate'&&profile&&<div className="space-y-5"><Card className="p-6 space-y-4"><h2 className="font-semibold">Choose an analytical question</h2><Field label="Method"><Select value={method} onChange={e=>{setMethod(e.target.value);setResult(null);}}><option value="aggregate">Compare grouped metrics</option><option value="formula">Calculate a row-level formula</option><option value="compare">Test a difference between two groups</option><option value="investigate">Explain where a period change occurred</option><option value="trend">Analyze daily trends, anomalies and forecast</option></Select></Field><div className="grid md:grid-cols-2 gap-4">{method!=='formula'&&<Field label="Numeric measure">{selectColumn(metric,setMetric,true)}</Field>}{['aggregate','compare','investigate'].includes(method)&&<Field label="Grouping column">{selectColumn(dimension,setDimension)}</Field>}{method==='aggregate'&&<Field label="Aggregation"><Select value={aggregation} onChange={e=>setAggregation(e.target.value)}>{['sum','mean','median','min','max','count'].map(v=><option key={v}>{v}</option>)}</Select></Field>}{method==='formula'&&<Field label="Formula using column names, + − * / and parentheses"><Input placeholder="(revenue - cost) / revenue * 100" value={expression} onChange={e=>setExpression(e.target.value)}/></Field>}{method==='compare'&&<><Field label="Baseline group (exact value)"><Input value={baseline} onChange={e=>setBaseline(e.target.value)}/></Field><Field label="Comparison group (exact value)"><Input value={comparison} onChange={e=>setComparison(e.target.value)}/></Field></>}{['trend','investigate'].includes(method)&&<Field label="Date column">{selectColumn(dateColumn,setDateColumn)}</Field>}{method==='investigate'&&<><Field label="Drilldown column (optional)">{selectColumn(drillColumn,setDrillColumn)}</Field><Field label="Drilldown exact value"><Input value={drillValue} onChange={e=>setDrillValue(e.target.value)}/></Field><Field label="Baseline period starts (optional)"><Input type="date" value={baselineStart} onChange={e=>setBaselineStart(e.target.value)}/></Field><Field label="Comparison period starts"><Input type="date" value={split} onChange={e=>setSplit(e.target.value)}/></Field><Field label="Comparison period ends (optional)"><Input type="date" value={comparisonEnd} onChange={e=>setComparisonEnd(e.target.value)}/></Field></>}{method==='trend'&&<Field label="Forecast days"><Input type="number" min="1" max="30" value={horizon} onChange={e=>setHorizon(e.target.value)}/></Field>}</div><Button disabled={busy||!writable} isLoading={busy} onClick={run}>Run and save evidence</Button></Card>{output&&<Card className="p-6 space-y-4"><h2 className="font-semibold">{output.method}</h2><p className="text-xs text-neutral-500">Saved as {result.title} · {result.stale?'Historical dataset':'Dataset revision captured'}</p>{output.notes?.map((note:string)=><p key={note} className="text-sm text-neutral-500">{note}</p>)}<Table rows={[Object.fromEntries(Object.entries(output).filter(([k,v])=>!['method','notes'].includes(k)&&!Array.isArray(v)&&typeof v!=='object'))]}/>{output.rows&&<Table rows={output.rows}/>}{output.coverage&&<><h3 className="font-medium">Period coverage</h3><Table rows={output.coverage}/></>}{output.validation_by_horizon&&<><h3 className="font-medium">Forecast validation by horizon</h3><Table rows={output.validation_by_horizon}/></>} {output.confidence_interval_95&&<p className="text-sm">95% bootstrap interval for the mean difference: {output.confidence_interval_95.map(format).join(' to ')}</p>}{output.history&&<><ResponsiveContainer width="100%" height={280}><LineChart data={output.history}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="date" tickFormatter={v=>String(v).slice(0,10)}/><YAxis/><Tooltip/><Line dataKey="value" stroke="#8C5E3C" dot={false}/><Line dataKey="moving_average_7" stroke="#059669" dot={false}/></LineChart></ResponsiveContainer><h3 className="font-medium">Forecast and empirical range</h3><Table rows={output.forecast}/><h3 className="font-medium">Validation error by candidate model</h3><Table rows={Object.entries(output.backtest_mae).map(([model,mae])=>({model,mae}))}/><h3 className="font-medium">Anomaly signals</h3><Table rows={output.history.filter((r:any)=>r.anomaly)}/></>}{output.recommended_next_steps?.map((s:string)=><p key={s} className="text-sm">• {s}</p>)}<Button variant="secondary" onClick={()=>download(result)}>Download evidence brief</Button></Card>}</div>}

    {tab==='Share'&&<div className="space-y-5"><Card className="p-6 space-y-4"><h2 className="font-semibold">Turn evidence into a reviewed action</h2><p className="text-sm text-neutral-500">These are team-authored conclusions. Include the evidence, an owner, a proposed action and a measure to validate the outcome. Records are visible only to members of this company.</p><div className="grid md:grid-cols-2 gap-4">{(['title','text','owner','validation_measure'] as const).map(key=><Field key={key} label={key.replace(/_/g,' ')}><Textarea value={finding[key]} onChange={e=>setFinding({...finding,[key]:e.target.value})}/></Field>)}<Field label="Action status"><Select value={finding.status} onChange={e=>setFinding({...finding,status:e.target.value})}>{['Proposed','Approved','In progress','Completed','Rejected'].map(v=><option key={v}>{v}</option>)}</Select></Field></div><Button disabled={busy||!writable||!finding.title.trim()||!finding.text.trim()} onClick={()=>perform(()=>save('finding',finding.title,{...finding,evidence_id:result?.id||null}))}>Save finding and action</Button></Card><Card className="p-6 space-y-4"><h2 className="font-semibold">Team discussion</h2><Field label="Finding or analysis"><Select value={parent} onChange={e=>setParent(e.target.value)}><option value="">Choose a record</option>{saved.filter(r=>['finding','run'].includes(r.kind)).map(r=><option key={r.id} value={r.id}>{r.title} · #{r.id}</option>)}</Select></Field><Field label="Comment"><Textarea value={comment} onChange={e=>setComment(e.target.value)}/></Field><Button disabled={busy||!writable||!parent||!comment.trim()} onClick={()=>perform(async()=>{await save('comment','Discussion',{parent_id:Number(parent),text:comment});setComment('');})}>Post to company discussion</Button></Card><div className="grid lg:grid-cols-2 gap-4">{saved.map(row=><Card className="p-5 space-y-3" key={row.id}><div className="flex gap-2 justify-between"><h3 className="font-semibold">{row.title}</h3><span className="text-xs text-neutral-500">#{row.id} · {row.kind}</span></div><p className="text-xs text-neutral-500">{new Date(row.created_at).toLocaleString()} · Author #{row.user_id}{row.stale?' · Historical dataset':''}</p>{row.content.text&&<p className="text-sm whitespace-pre-wrap">{row.content.text}</p>}{row.content.owner&&<p className="text-sm">Owner: {row.content.owner} · {row.content.status}</p>}{row.content.parent_id&&<p className="text-xs">Related record #{row.content.parent_id}</p>}{row.kind==='action_update'&&<><p className="text-sm">Status: {row.content.status}</p><p className="text-sm whitespace-pre-wrap">{row.content.outcome}</p></>}{row.kind==='run'&&<Button size="sm" variant="secondary" onClick={()=>{setResult(row);setMethod(row.content.method||'aggregate');setMetric(row.content.parameters?.metric||metric);setDimension(row.content.parameters?.dimension||row.content.parameters?.dimensions?.[0]||dimension);setDateColumn(row.content.parameters?.date_column||dateColumn);setSplit(row.content.parameters?.split_date||'');setBaseline(row.content.parameters?.baseline||'');setComparison(row.content.parameters?.comparison||'');setExpression(row.content.parameters?.expression||'');setHorizon(String(row.content.parameters?.horizon||7));setAggregation(row.content.parameters?.aggregation||'sum');setBaselineStart(row.content.parameters?.baseline_start_date||'');setComparisonEnd(row.content.parameters?.comparison_end_date||'');setDrillColumn(Object.keys(row.content.parameters?.filters||{})[0]||'');setDrillValue(String(Object.values(row.content.parameters?.filters||{})[0]??''));setTab('Investigate');}}>View saved evidence</Button>}<Button size="sm" variant="secondary" onClick={()=>download(row)}>Download {row.kind==='backup'?'dataset backup':'brief'}</Button></Card>)}</div><p className="text-xs text-neutral-500">Downloaded HTML briefs can be opened and printed to PDF in your browser. Downloaded files are not protected by workspace login after you share them.</p></div>}

    {tab==='Monitor'&&profile&&<div className="space-y-5"><Card className="p-6 space-y-4"><h2 className="font-semibold">Data readiness checks</h2><p className="text-sm text-neutral-500">{monitor?.mode}</p><Table rows={monitor?.checks||[]}/><p className="text-xs text-neutral-500">Last checked: {monitor?.checked_at?new Date(monitor.checked_at).toLocaleString():'Loading…'}</p><div className="grid md:grid-cols-2 gap-4"><Field label="Maximum hours since upload"><Input type="number" min="1" max="8760" value={ageLimit} onChange={e=>setAgeLimit(e.target.value)}/></Field><Field label="Maximum missing cells (%)"><Input type="number" min="0" max="100" value={missingLimit} onChange={e=>setMissingLimit(e.target.value)}/></Field></div><Button disabled={busy||!writable} onClick={()=>perform(async()=>{await save('monitor','Data readiness rules',{max_age_hours:Number(ageLimit),max_missing_percent:Number(missingLimit)});setMonitor((await axiosClient.get('/analysis/monitor')).data);})}>Save monitoring rules</Button><Link to="/alerts" className="block text-sm underline">Review metric anomaly alerts →</Link></Card></div>}
  </div>;
};
