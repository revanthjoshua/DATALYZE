import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Upload,
  Sparkles,
  Database,
  RefreshCw,
  Table as TableIcon,
  Activity,
  FileCode,
  Zap,
  ChevronLeft,
  ChevronRight,
  Search,
  BarChart3,
  Calendar,
  Tag,
  Hash,
  CheckCircle2,
  AlertCircle,
  FileSpreadsheet,
  Eye,
  Edit3,
  Download,
  Plus,
  Trash2,
  Save,
  Check,
  Columns,
  ListFilter,
  DollarSign,
  Percent,
  Clock,
  CheckSquare,
} from 'lucide-react';
import { dataApi } from '../api/dataApi';
import { IngestionResponse } from '../types/data.types';
import { useTenant } from '../context/TenantContext';
import { useToast } from '../context/ToastContext';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { StateView } from '../components/ui/StateView';
import { Modal } from '../components/ui/Modal';
import { FormField, Input, Select, Textarea } from '../components/ui/FormField';

export const DataPage: React.FC = () => {
  const { company } = useTenant();
  const toast = useToast();
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [dragActive, setDragActive] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [sampleLoading, setSampleLoading] = useState<boolean>(false);
  const [response, setResponse] = useState<IngestionResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [inputMode, setInputMode] = useState<'upload' | 'paste'>('upload');
  const [rawText, setRawText] = useState<string>('');
  const [pasteLoading, setPasteLoading] = useState<boolean>(false);

  // Active In-Memory Dataset State
  const [datasetInfo, setDatasetInfo] = useState<any>(null);
  const [datasetPreview, setDatasetPreview] = useState<any>(null);
  const [previewLoading, setPreviewLoading] = useState<boolean>(false);
  const [previewPage, setPreviewPage] = useState<number>(0);
  const [previewLimit, setPreviewLimit] = useState<number>(15);
  const [tableSearch, setTableSearch] = useState<string>('');

  // Interactive Query Runner State
  const [selectedGroupBy, setSelectedGroupBy] = useState<string>('');
  const [selectedAggCol, setSelectedAggCol] = useState<string>('');
  const [selectedAggFunc, setSelectedAggFunc] = useState<string>('sum');
  const [queryRunning, setQueryRunning] = useState<boolean>(false);
  const [queryResults, setQueryResults] = useState<any>(null);

  // Dataset Live Spreadsheet Editor Modal State
  const [isEditorOpen, setIsEditorOpen] = useState<boolean>(false);
  const [editorRows, setEditorRows] = useState<any[]>([]);
  const [editorCols, setEditorCols] = useState<string[]>([]);
  const [editorLoading, setEditorLoading] = useState<boolean>(false);
  const [editorSaving, setEditorSaving] = useState<boolean>(false);
  const [editorSearch, setEditorSearch] = useState<string>('');

  const fetchActiveDataset = async (page: number = 0, limit: number = previewLimit) => {
    try {
      setPreviewLoading(true);
      const info = await dataApi.getDatasetInfo();
      if (info && info.has_dataset) {
        setDatasetInfo(info);
        const prev = await dataApi.getDatasetPreview(limit, page * limit);
        setDatasetPreview(prev);

        if (info.categorical_columns && info.categorical_columns.length > 0 && !selectedGroupBy) {
          setSelectedGroupBy(info.categorical_columns[0]);
        }
        if (info.numeric_columns && info.numeric_columns.length > 0 && !selectedAggCol) {
          setSelectedAggCol(info.numeric_columns[0]);
        }
      } else {
        setDatasetInfo(null);
        setDatasetPreview(null);
      }
    } catch (err) {
      console.error('Failed to load dataset info', err);
    } finally {
      setPreviewLoading(false);
    }
  };

  useEffect(() => {
    fetchActiveDataset(0, previewLimit);
  }, []);

  const handleFileUpload = async (file: File) => {
    if (!file) return;
    setErrorMsg(null);
    setLoading(true);
    try {
      toast.info(`Parsing columns & detecting dynamic data types for "${file.name}"...`, 'File Ingestion');
      const result = await dataApi.uploadFile(file);
      setResponse(result);
      toast.success(
        `Successfully ingested ${result.processed_rows || result.total_rows || 'all'} rows! Dynamic schema updated.`,
        'Ingestion Complete'
      );
      await fetchActiveDataset(0, previewLimit);
    } catch (err: any) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        'Failed to upload and process file. Please check file format.';
      setErrorMsg(typeof msg === 'string' ? msg : JSON.stringify(msg));
      toast.error(typeof msg === 'string' ? msg : 'Upload failed', 'Ingestion Error');
    } finally {
      setLoading(false);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleLoadSample = async () => {
    setSampleLoading(true);
    setErrorMsg(null);
    try {
      toast.info('Generating domain-specific business data with continuous history...', 'Data Ingestion');
      const result = await dataApi.loadSampleDataset();
      setResponse(result);
      toast.success(
        `Loaded ${result.processed_rows} sample records across 30 days.`,
        'Sample Loaded'
      );
      await fetchActiveDataset(0, previewLimit);
    } catch (err: any) {
      toast.error('Failed to load sample dataset.', 'Sample Error');
    } finally {
      setSampleLoading(false);
    }
  };

  const handlePasteSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rawText.trim()) {
      setErrorMsg('Please paste raw CSV or JSON data.');
      return;
    }
    setPasteLoading(true);
    setErrorMsg(null);
    try {
      let payload: any = { raw_data: rawText.trim() };
      try {
        const parsed = JSON.parse(rawText.trim());
        payload = parsed;
      } catch {
        const lines = rawText.trim().split('\n');
        if (lines.length >= 2) {
          const headers = lines[0].split(',').map((h) => h.trim().replace(/^["']|["']$/g, ''));
          const records = [];
          for (let i = 1; i < lines.length; i++) {
            const currentLine = lines[i].trim();
            if (!currentLine) continue;
            const values = currentLine.split(',').map((v) => v.trim().replace(/^["']|["']$/g, ''));
            const record: Record<string, any> = {};
            headers.forEach((h, idx) => {
              const val = values[idx];
              const num = Number(val);
              record[h] = !isNaN(num) && val !== '' ? num : val;
            });
            records.push(record);
          }
          payload = { records };
        }
      }

      const result = await dataApi.ingestRawData(payload);
      setResponse(result);
      toast.success(
        `Pasted text parsed successfully (${result.processed_rows || 0} rows). Schema updated.`,
        'Ingestion Complete'
      );
      await fetchActiveDataset(0, previewLimit);
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Failed to parse pasted data.';
      setErrorMsg(typeof msg === 'string' ? msg : JSON.stringify(msg));
      toast.error('Failed to process pasted content.', 'Ingestion Error');
    } finally {
      setPasteLoading(false);
    }
  };

  const handleRunQuery = async () => {
    if (!selectedGroupBy || !selectedAggCol) return;
    setQueryRunning(true);
    try {
      const res = await dataApi.runInteractiveQuery({
        group_by: selectedGroupBy,
        agg_col: selectedAggCol,
        agg_func: selectedAggFunc,
      });
      setQueryResults(res);
      toast.success(`Computed ${selectedAggFunc.toUpperCase()} of ${selectedAggCol} grouped by ${selectedGroupBy}.`, 'Query Finished');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to execute aggregation query.', 'Query Error');
    } finally {
      setQueryRunning(false);
    }
  };

  // Open Full Dataset Spreadsheet Editor Modal
  const handleOpenEditor = async () => {
    setEditorLoading(true);
    setIsEditorOpen(true);
    try {
      const preview = await dataApi.getDatasetPreview(200, 0);
      if (preview && preview.records) {
        setEditorRows(JSON.parse(JSON.stringify(preview.records)));
        setEditorCols(preview.columns || []);
      } else if (preview && preview.rows) {
        setEditorRows(JSON.parse(JSON.stringify(preview.rows)));
        setEditorCols(preview.columns || []);
      }
    } catch (err) {
      toast.error('Failed to load dataset records for editing.', 'Editor Error');
    } finally {
      setEditorLoading(false);
    }
  };

  const handleCellChange = (rowIndex: number, colName: string, value: string) => {
    setEditorRows((prev) => {
      const updated = [...prev];
      const numVal = Number(value);
      updated[rowIndex] = {
        ...updated[rowIndex],
        [colName]: !isNaN(numVal) && value.trim() !== '' ? numVal : value,
      };
      return updated;
    });
  };

  const handleAddRow = () => {
    setEditorRows((prev) => {
      const emptyRow: Record<string, any> = {};
      editorCols.forEach((col) => {
        emptyRow[col] = '';
      });
      return [emptyRow, ...prev];
    });
    toast.info('New row added at the top. Enter cell values and click Save.', 'Row Added');
  };

  const handleDeleteRow = (rowIndex: number) => {
    setEditorRows((prev) => prev.filter((_, idx) => idx !== rowIndex));
  };

  const handleSaveEditor = async () => {
    if (editorRows.length === 0) {
      toast.error('Dataset cannot be empty.', 'Save Error');
      return;
    }
    setEditorSaving(true);
    try {
      const filename = datasetInfo?.filename || 'edited_dataset.csv';
      const result = await dataApi.updateDataset(editorRows, filename);
      toast.success(
        `Updated ${result.processed_rows} rows! Continuous KPIs, detections, and predictions re-analyzed.`,
        'Dataset Saved & Synced'
      );
      setIsEditorOpen(false);
      await fetchActiveDataset(0, previewLimit);
    } catch (err: any) {
      toast.error('Failed to save dataset edits.', 'Save Failed');
    } finally {
      setEditorSaving(false);
    }
  };

  const handleDownloadCsv = () => {
    window.open(dataApi.getDatasetDownloadUrl(), '_blank');
  };

  // Helper to render styled badge for auto-detected data types
  const renderDataTypeBadge = (dataType: string) => {
    switch (dataType) {
      case 'Currency':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
            💰 Currency
          </span>
        );
      case 'Percentage':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-100 dark:bg-purple-950/60 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800">
            % Percentage
          </span>
        );
      case 'Date':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
            📅 Date
          </span>
        );
      case 'Date & Time':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-100 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
            ⏰ Date & Time
          </span>
        );
      case 'Integer':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
            🔢 Integer
          </span>
        );
      case 'Decimal':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-cyan-100 dark:bg-cyan-950/60 text-cyan-700 dark:text-cyan-300 border border-cyan-200 dark:border-cyan-800">
            0.00 Decimal
          </span>
        );
      case 'Boolean':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-sky-100 dark:bg-sky-950/60 text-sky-700 dark:text-sky-300 border border-sky-200 dark:border-sky-800">
            ✓/✗ Boolean
          </span>
        );
      case 'Categorical':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-teal-100 dark:bg-teal-950/60 text-teal-700 dark:text-teal-300 border border-teal-200 dark:border-teal-800">
            🏷️ Categorical
          </span>
        );
      case 'Identifier':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-700 font-mono">
            # ID / Code
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 border border-neutral-200 dark:border-neutral-700">
            📝 Text
          </span>
        );
    }
  };

  const rowCount = datasetInfo?.row_count || 0;
  const colCount = datasetInfo?.columns?.length || 0;
  const dynamicEyebrow =
    datasetInfo?.has_dataset && rowCount > 0
      ? `${rowCount.toLocaleString()} Records Indexed • ${colCount} Detected Columns`
      : 'Data Pipeline Ready • Dynamic Data Type Detection';

  const detectedSchemaList: any[] = datasetInfo?.schema || [];

  return (
    <div className="space-y-6 sm:space-y-8 animate-fade-in">
      {/* Header with Dynamic Contextual Eyebrow */}
      <PageHeader
        stage={dynamicEyebrow}
        stageIcon={<Database className="w-4 h-4 text-[#6B4226] dark:text-[#D5B79F]" />}
        title="Upload & Connect Data"
        description="Upload your spreadsheets. Column types, currencies, and timestamps are automatically detected dynamically per file."
        actions={
          <div className="flex items-center space-x-2">
            {datasetInfo && datasetInfo.has_dataset ? (
              <Button
                variant="secondary"
                size="sm"
                onClick={handleOpenEditor}
                leftIcon={<Eye className="w-3.5 h-3.5 text-[#6B4226] dark:text-[#D5B79F]" />}
              >
                View & Edit File
              </Button>
            ) : (
              <Button
                variant="outline"
                size="sm"
                isLoading={sampleLoading}
                onClick={handleLoadSample}
                leftIcon={<Sparkles className="w-3.5 h-3.5" />}
              >
                Load Sample Data
              </Button>
            )}
          </div>
        }
      />

      {/* Upload Modes & Input Panel */}
      <Card className="p-6">
        <div className="flex items-center justify-between border-b border-neutral-100 dark:border-neutral-800 pb-4 mb-4 flex-wrap gap-2">
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setInputMode('upload')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors cursor-pointer ${
                inputMode === 'upload'
                  ? 'bg-[#6B4226] dark:bg-[#7A4B2C] text-white shadow-xs'
                  : 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800'
              }`}
            >
              Upload File (.xlsx, .csv, .docx, .json)
            </button>
            <button
              onClick={() => setInputMode('paste')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors cursor-pointer ${
                inputMode === 'paste'
                  ? 'bg-[#6B4226] dark:bg-[#7A4B2C] text-white shadow-xs'
                  : 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800'
              }`}
            >
              Paste Raw CSV Text
            </button>
          </div>

          <span className="text-xs text-neutral-400 font-mono hidden sm:inline">
            Dynamic schema discovery adapts to each unique file
          </span>
        </div>

        {errorMsg && (
          <div className="mb-4 p-3.5 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 text-red-600 dark:text-red-400 text-xs flex items-center space-x-2 font-medium">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {inputMode === 'upload' ? (
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center transition-all ${
              dragActive
                ? 'border-[#6B4226] dark:border-[#8C5E3C] bg-[#F4ECE4]/30 dark:bg-[#271910]/30'
                : 'border-neutral-200 dark:border-neutral-800 hover:border-neutral-300 dark:hover:border-neutral-700 bg-neutral-50/50 dark:bg-neutral-900/30'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.tsv,.txt,.xlsx,.xls,.xlsm,.xlsb,.docx,.json,.jsonl,.parquet,.pdf"
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  handleFileUpload(e.target.files[0]);
                }
              }}
              className="hidden"
            />
            <div className="mx-auto w-12 h-12 rounded-2xl bg-[#F4ECE4] dark:bg-[#271910] text-[#6B4226] dark:text-[#8C5E3C] flex items-center justify-center mb-3">
              <Upload className="w-6 h-6" />
            </div>
            <h4 className="text-sm sm:text-base font-bold text-neutral-900 dark:text-neutral-100">
              Drag & Drop Your Business File Here
            </h4>
            <p className="text-xs text-neutral-500 max-w-sm mx-auto mt-1 mb-4">
              Excel (.xlsx), CSV, TSV, Word table (.docx), or JSON. Schema and types adapt automatically.
            </p>
            <div className="flex items-center justify-center space-x-3">
              <Button
                variant="primary"
                size="sm"
                isLoading={loading}
                onClick={() => fileInputRef.current?.click()}
                leftIcon={<Upload className="w-3.5 h-3.5" />}
              >
                Browse Files
              </Button>
              {datasetInfo && datasetInfo.has_dataset && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleOpenEditor}
                  leftIcon={<Eye className="w-3.5 h-3.5" />}
                >
                  Inspect Active File
                </Button>
              )}
            </div>
          </div>
        ) : (
          <form onSubmit={handlePasteSubmit} className="space-y-4">
            <FormField
              label="Paste Delimited Records or JSON Array"
              helperText="Include header row on first line (e.g. order_date, quantity, unit_price, customer_name)"
            >
              <Textarea
                rows={6}
                value={rawText}
                onChange={(e) => setRawText(e.target.value)}
                placeholder="order_date,quantity,unit_price,customer_name,region&#10;2026-08-10,4,$290.00,Acme Corp,North&#10;2026-08-11,6,$380.00,Global Retail,West"
                className="font-mono text-xs"
              />
            </FormField>
            <div className="flex justify-end">
              <Button
                type="submit"
                variant="primary"
                size="sm"
                isLoading={pasteLoading}
                leftIcon={<CheckCircle2 className="w-3.5 h-3.5" />}
              >
                Parse & Sync to Dashboard
              </Button>
            </div>
          </form>
        )}
      </Card>

      {/* Active Dataset Inspection & Schema Viewer */}
      {datasetInfo && datasetInfo.has_dataset && (
        <div className="space-y-6">
          {/* Dataset Statistics Card */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Card className="p-5 flex flex-col justify-between border-l-4 border-l-[#6B4226]">
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-neutral-500 font-mono block uppercase font-semibold">
                    Active File Records
                  </span>
                  <button
                    onClick={handleOpenEditor}
                    className="p-1.5 rounded-lg bg-neutral-100 dark:bg-neutral-800 text-[#6B4226] dark:text-[#D5B79F] hover:bg-[#F4ECE4] transition-colors cursor-pointer flex items-center space-x-1 text-xs font-semibold"
                    title="View & Edit File"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>View / Edit</span>
                  </button>
                </div>
                <p className="text-2xl font-extrabold text-neutral-900 dark:text-neutral-100 font-mono mt-2">
                  {(datasetInfo.row_count || 0).toLocaleString()} rows
                </p>
                <p className="text-xs text-neutral-500 mt-1 font-sans">
                  Source: <strong className="text-neutral-800 dark:text-neutral-200">{datasetInfo.filename || 'uploaded document'}</strong>
                </p>
              </div>

              <div className="pt-3 mt-3 border-t border-neutral-100 dark:border-neutral-800 flex items-center justify-between">
                <span className="text-[11px] text-neutral-400 font-mono">
                  {datasetInfo.col_count || datasetInfo.columns?.length || 0} detected columns
                </span>
                <button
                  onClick={handleDownloadCsv}
                  className="text-xs text-[#6B4226] dark:text-[#D5B79F] hover:underline font-semibold flex items-center space-x-1 cursor-pointer"
                >
                  <Download className="w-3 h-3" />
                  <span>Download CSV</span>
                </button>
              </div>
            </Card>

            <Card className="p-5">
              <span className="text-xs text-neutral-500 font-mono block uppercase font-semibold">
                Numeric Value Metrics ({datasetInfo.numeric_columns?.length || 0})
              </span>
              <div className="flex flex-wrap gap-1.5 mt-2.5 max-h-24 overflow-y-auto">
                {(datasetInfo.numeric_columns || []).map((col: string) => (
                  <Badge key={col} variant="healthy" size="xs">
                    {col.replace(/_/g, ' ')}
                  </Badge>
                ))}
              </div>
            </Card>

            <Card className="p-5">
              <span className="text-xs text-neutral-500 font-mono block uppercase font-semibold">
                Categorical Dimensions ({datasetInfo.categorical_columns?.length || 0})
              </span>
              <div className="flex flex-wrap gap-1.5 mt-2.5 max-h-24 overflow-y-auto">
                {(datasetInfo.categorical_columns || []).map((col: string) => (
                  <Badge key={col} variant="brand" size="xs">
                    {col.replace(/_/g, ' ')}
                  </Badge>
                ))}
              </div>
            </Card>
          </div>

          {/* DYNAMIC SCHEMA & AUTO-DETECTED COLUMN TYPES PANEL */}
          {detectedSchemaList.length > 0 && (
            <Card className="p-5 space-y-4 border">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-neutral-100 dark:border-neutral-800 pb-3">
                <div className="flex items-center space-x-2">
                  <div className="p-1.5 rounded-lg bg-[#F4ECE4] dark:bg-[#271910] text-[#6B4226] dark:text-[#D5B79F]">
                    <Columns className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-neutral-900 dark:text-neutral-100">
                      Auto-Detected Dataset Schema & Column Types
                    </h3>
                    <p className="text-xs text-neutral-500">
                      Inferred dynamically from actual values in "{datasetInfo.filename || 'uploaded file'}". Schema replaces automatically upon new uploads.
                    </p>
                  </div>
                </div>

                <Badge variant="healthy" size="xs" dot>
                  {detectedSchemaList.length} Columns Classified
                </Badge>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse font-mono">
                  <thead>
                    <tr className="bg-neutral-50 dark:bg-neutral-900 border-b border-neutral-200 dark:border-neutral-800 text-neutral-600 dark:text-neutral-400">
                      <th className="py-2.5 px-3 font-semibold">#</th>
                      <th className="py-2.5 px-3 font-semibold">Column Name</th>
                      <th className="py-2.5 px-3 font-semibold">Detected Data Type</th>
                      <th className="py-2.5 px-3 font-semibold text-right">Populated / Total</th>
                      <th className="py-2.5 px-3 font-semibold text-right">Unique Values</th>
                      <th className="py-2.5 px-3 font-semibold">Sample Values from File</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-100 dark:divide-neutral-800/80">
                    {detectedSchemaList.map((col: any, idx: number) => (
                      <tr key={col.name || idx} className="hover:bg-neutral-50/70 dark:hover:bg-neutral-900/40">
                        <td className="py-2 px-3 text-neutral-400 font-sans text-[11px]">{idx + 1}</td>
                        <td className="py-2 px-3 font-sans font-bold text-neutral-900 dark:text-neutral-100">
                          {col.name}
                        </td>
                        <td className="py-2 px-3">
                          {renderDataTypeBadge(col.data_type)}
                        </td>
                        <td className="py-2 px-3 text-right text-neutral-700 dark:text-neutral-300">
                          {col.non_null_count?.toLocaleString()} / {col.total_count?.toLocaleString()}
                        </td>
                        <td className="py-2 px-3 text-right text-neutral-600 dark:text-neutral-400">
                          {col.unique_count?.toLocaleString()}
                        </td>
                        <td className="py-2 px-3">
                          <div className="flex items-center space-x-1.5 overflow-x-auto max-w-xs">
                            {(col.sample_values || []).map((sVal: string, sIdx: number) => (
                              <span
                                key={sIdx}
                                className="px-1.5 py-0.5 rounded bg-neutral-100 dark:bg-neutral-800 text-[10px] text-neutral-700 dark:text-neutral-300 whitespace-nowrap border border-neutral-200 dark:border-neutral-700"
                              >
                                {sVal}
                              </span>
                            ))}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}

          {/* Interactive Multi-Dimensional Query Tool */}
          <Card className="p-5 border space-y-4">
            <div className="flex items-center space-x-2">
              <Zap className="w-4 h-4 text-amber-500" />
              <h3 className="text-sm font-bold text-neutral-900 dark:text-neutral-100 tracking-tight">
                Interactive Group-By Query Sandbox
              </h3>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs">
              <FormField label="Group By Dimension">
                <Select
                  value={selectedGroupBy}
                  onChange={(e) => setSelectedGroupBy(e.target.value)}
                >
                  {(datasetInfo.categorical_columns || []).map((c: string) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </Select>
              </FormField>

              <FormField label="Metric Column">
                <Select
                  value={selectedAggCol}
                  onChange={(e) => setSelectedAggCol(e.target.value)}
                >
                  {(datasetInfo.numeric_columns || []).map((c: string) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </Select>
              </FormField>

              <FormField label="Aggregation Function">
                <Select
                  value={selectedAggFunc}
                  onChange={(e) => setSelectedAggFunc(e.target.value)}
                >
                  <option value="sum">SUM (Total)</option>
                  <option value="mean">MEAN (Average)</option>
                  <option value="min">MIN (Lowest)</option>
                  <option value="max">MAX (Highest)</option>
                  <option value="count">COUNT (Frequency)</option>
                </Select>
              </FormField>

              <div className="flex items-end">
                <Button
                  variant="primary"
                  size="md"
                  className="w-full"
                  isLoading={queryRunning}
                  onClick={handleRunQuery}
                >
                  Execute Query
                </Button>
              </div>
            </div>

            {queryResults && (
              <div className="mt-3 p-4 bg-neutral-50 dark:bg-neutral-900/60 rounded-xl border border-neutral-200 dark:border-neutral-800 space-y-2">
                <span className="text-xs font-semibold text-neutral-700 dark:text-neutral-300 font-mono">
                  Query Output:
                </span>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs font-mono">
                    <thead>
                      <tr className="border-b border-neutral-200 dark:border-neutral-700 text-neutral-500">
                        <th className="py-1 px-2 text-left">{selectedGroupBy}</th>
                        <th className="py-1 px-2 text-right">
                          {selectedAggFunc.toUpperCase()}({selectedAggCol})
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-neutral-200/60 dark:divide-neutral-800">
                      {Object.entries(queryResults).map(([k, v]: [string, any]) => (
                        <tr key={k}>
                          <td className="py-1 px-2 font-sans font-medium text-neutral-800 dark:text-neutral-200">
                            {k}
                          </td>
                          <td className="py-1 px-2 text-right font-bold text-[#6B4226] dark:text-[#8C5E3C]">
                            {typeof v === 'number' ? v.toLocaleString(undefined, { maximumFractionDigits: 2 }) : String(v)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </Card>

          {/* Dataset Preview Table */}
          {datasetPreview && (datasetPreview.records || datasetPreview.rows) && (
            <Card className="overflow-hidden space-y-0">
              <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <div className="flex items-center space-x-2">
                    <CardTitle>Ingested Tabular Preview</CardTitle>
                    <Badge variant="healthy" size="xs">
                      {datasetInfo.row_count || datasetInfo.total_rows || (datasetPreview.records || datasetPreview.rows).length} ROWS
                    </Badge>
                  </div>
                  <p className="text-xs text-neutral-500">
                    Live raw records currently loaded in the continuous analysis engine
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <Button
                    variant="primary"
                    size="xs"
                    onClick={handleOpenEditor}
                    leftIcon={<Eye className="w-3.5 h-3.5" />}
                  >
                    View & Edit File
                  </Button>
                  <Button
                    variant="outline"
                    size="xs"
                    onClick={() => fetchActiveDataset(previewPage, previewLimit)}
                    leftIcon={<RefreshCw className="w-3 h-3" />}
                  >
                    Reload Table
                  </Button>
                </div>
              </CardHeader>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse font-mono">
                  <thead>
                    <tr className="bg-neutral-50 dark:bg-neutral-900 border-b border-neutral-200 dark:border-neutral-800">
                      <th className="py-2.5 px-3 w-10 text-neutral-400 font-semibold">#</th>
                      {datasetPreview.columns.map((col: string) => (
                        <th
                          key={col}
                          className="py-2.5 px-3 font-semibold text-[11px] text-neutral-600 dark:text-neutral-300 uppercase tracking-wider whitespace-nowrap"
                        >
                          {col.replace(/_/g, ' ')}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-100 dark:divide-neutral-800/60">
                    {(datasetPreview.records || datasetPreview.rows).map((row: any, rIdx: number) => (
                      <tr key={rIdx} className="hover:bg-neutral-50/80 dark:hover:bg-neutral-900/40">
                        <td className="py-2 px-3 text-neutral-400">{previewPage * previewLimit + rIdx + 1}</td>
                        {datasetPreview.columns.map((col: string) => (
                          <td
                            key={col}
                            className="py-2 px-3 text-neutral-800 dark:text-neutral-200 whitespace-nowrap"
                          >
                            {row[col] !== null && row[col] !== undefined
                              ? typeof row[col] === 'number'
                                ? row[col].toLocaleString(undefined, { maximumFractionDigits: 2 })
                                : String(row[col])
                              : '—'}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination controls for preview */}
              <div className="p-3 border-t border-neutral-100 dark:border-neutral-800/80 flex items-center justify-between text-xs text-neutral-500 bg-neutral-50/40 dark:bg-neutral-900/30">
                <span>
                  Page {previewPage + 1} of {Math.ceil((datasetInfo.row_count || datasetInfo.total_rows || 1) / previewLimit)}
                </span>
                <div className="flex items-center space-x-1.5">
                  <Button
                    variant="outline"
                    size="xs"
                    disabled={previewPage === 0}
                    onClick={() => {
                      const next = previewPage - 1;
                      setPreviewPage(next);
                      fetchActiveDataset(next, previewLimit);
                    }}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="xs"
                    disabled={(previewPage + 1) * previewLimit >= (datasetInfo.row_count || datasetInfo.total_rows || 0)}
                    onClick={() => {
                      const next = previewPage + 1;
                      setPreviewPage(next);
                      fetchActiveDataset(next, previewLimit);
                    }}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </Card>
          )}
        </div>
      )}

      {/* FULL-SCREEN INTERACTIVE SPREADSHEET EDITOR MODAL */}
      <Modal
        isOpen={isEditorOpen}
        onClose={() => setIsEditorOpen(false)}
        maxWidth="full"
        title={`Active Document Editor: ${datasetInfo?.filename || 'Uploaded File'}`}
        description="Inspect and edit individual cells, add or remove records, and sync changes instantly across all dashboard metrics."
        icon={<Eye className="w-5 h-5 text-[#6B4226]" />}
      >
        <div className="space-y-4">
          {/* Editor Action Toolbar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-neutral-200 dark:border-neutral-800">
            <div className="flex items-center space-x-2">
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400" />
                <input
                  type="text"
                  value={editorSearch}
                  onChange={(e) => setEditorSearch(e.target.value)}
                  placeholder="Filter records in sheet..."
                  className="pl-8 pr-3 py-1.5 text-xs rounded-xl bg-neutral-100 dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 text-neutral-900 dark:text-neutral-100 focus:outline-none focus:ring-1 focus:ring-[#6B4226] w-60"
                />
              </div>
              <Button
                variant="outline"
                size="xs"
                onClick={handleAddRow}
                leftIcon={<Plus className="w-3.5 h-3.5" />}
              >
                Add Row
              </Button>
              <Button
                variant="outline"
                size="xs"
                onClick={handleDownloadCsv}
                leftIcon={<Download className="w-3.5 h-3.5" />}
              >
                Export CSV
              </Button>
            </div>

            <div className="flex items-center space-x-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setIsEditorOpen(false)}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                isLoading={editorSaving}
                onClick={handleSaveEditor}
                leftIcon={<Save className="w-3.5 h-3.5" />}
              >
                Save Changes & Re-Analyze
              </Button>
            </div>
          </div>

          {/* Interactive Editable Table */}
          {editorLoading ? (
            <div className="py-16 text-center text-xs text-neutral-400 font-mono animate-pulse">
              Loading dataset grid...
            </div>
          ) : (
            <div className="overflow-x-auto max-h-[65vh] border border-neutral-200 dark:border-neutral-800 rounded-xl bg-white dark:bg-[#15171C] shadow-inner">
              <table className="w-full min-w-max text-xs text-left border-collapse font-mono">
                <thead className="sticky top-0 bg-neutral-100 dark:bg-neutral-900 z-10 border-b border-neutral-200 dark:border-neutral-800 text-neutral-700 dark:text-neutral-300">
                  <tr>
                    <th className="py-2.5 px-3 w-12 text-neutral-400 font-bold bg-neutral-100 dark:bg-neutral-900">#</th>
                    {editorCols.map((col) => (
                      <th
                        key={col}
                        className="py-2.5 px-3 font-bold uppercase tracking-wider whitespace-nowrap min-w-[140px]"
                      >
                        {col.replace(/_/g, ' ')}
                      </th>
                    ))}
                    <th className="py-2.5 px-3 w-16 text-right font-bold bg-neutral-100 dark:bg-neutral-900">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-100 dark:divide-neutral-800/80 bg-white dark:bg-[#15171C]">
                  {editorRows
                    .map((row, originalIdx) => ({ row, originalIdx }))
                    .filter(({ row }) =>
                      !editorSearch
                        ? true
                        : Object.values(row).some((v) =>
                            String(v).toLowerCase().includes(editorSearch.toLowerCase())
                          )
                    )
                    .map(({ row, originalIdx }) => (
                      <tr
                        key={originalIdx}
                        className="hover:bg-neutral-50 dark:hover:bg-neutral-900/50 transition-colors"
                      >
                        <td className="py-1 px-3 text-neutral-400 text-[11px] font-bold">
                          {originalIdx + 1}
                        </td>
                        {editorCols.map((col) => (
                          <td key={col} className="p-1 min-w-[140px]">
                            <input
                              type="text"
                              value={row[col] !== undefined && row[col] !== null ? String(row[col]) : ''}
                              onChange={(e) => handleCellChange(originalIdx, col, e.target.value)}
                              className="w-full px-2.5 py-1 text-xs rounded bg-neutral-50/50 dark:bg-neutral-900/50 hover:bg-neutral-100 dark:hover:bg-neutral-800 focus:bg-white dark:focus:bg-neutral-900 border border-neutral-200 dark:border-neutral-700/80 focus:border-[#6B4226] text-neutral-900 dark:text-neutral-100 focus:outline-none transition-colors"
                            />
                          </td>
                        ))}
                        <td className="py-1 px-3 text-right">
                          <button
                            onClick={() => handleDeleteRow(originalIdx)}
                            className="p-1 rounded text-red-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/40 transition-colors cursor-pointer"
                            title="Delete row"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Editor Footer Summary */}
          <div className="flex items-center justify-between text-xs text-neutral-500 pt-2 font-mono">
            <span>Total: {editorRows.length} records • {editorCols.length} columns</span>
            <span>Edits update all metric sparklines, detections & forecasts across DATALYZE</span>
          </div>
        </div>
      </Modal>
    </div>
  );
};
