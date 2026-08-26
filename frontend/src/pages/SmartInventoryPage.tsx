import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Boxes,
  ArrowRight,
  RefreshCw,
  Sparkles,
  ShoppingCart,
  Check,
} from 'lucide-react';
import { inventoryApi } from '../api/inventoryApi';
import {
  InventoryDashboardSummary,
  InventoryItem,
  InventoryAllocationRecommendation,
} from '../types/inventory.types';
import { useTenant } from '../context/TenantContext';
import { useToast } from '../context/ToastContext';
import { formatKPIValue } from '../utils/formatters';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Card } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { StateView } from '../components/ui/StateView';
import { DenseTable, ColumnDef } from '../components/ui/DenseTable';
import { Modal } from '../components/ui/Modal';
import { FormField, Input } from '../components/ui/FormField';

export const SmartInventoryPage: React.FC = () => {
  const { company } = useTenant();
  const toast = useToast();
  const navigate = useNavigate();

  const [summary, setSummary] = useState<InventoryDashboardSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [reseedLoading, setReseedLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [riskFilter, setRiskFilter] = useState<string>(() => {
    return localStorage.getItem('datalyze_inv_risk') || 'ALL';
  });
  const [approvedAllocations, setApprovedAllocations] = useState<string[]>(() => {
    try {
      const saved = localStorage.getItem('datalyze_approved_transfers');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  // Purchase Order Draft Modal
  const [orderModalItem, setOrderModalItem] = useState<InventoryItem | null>(null);
  const [orderQuantity, setOrderQuantity] = useState<number>(100);
  const [orderLoading, setOrderLoading] = useState<boolean>(false);

  const fetchInventory = async () => {
    try {
      setLoading(true);
      setErrorMsg(null);
      const data = await inventoryApi.getInventorySummary();
      setSummary(data);
    } catch (err) {
      console.error('Failed to fetch inventory data', err);
      setErrorMsg('Failed to load inventory warehouse network status.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInventory();
  }, []);

  const handleReseed = async () => {
    try {
      setReseedLoading(true);
      toast.info('Simulating warehouse demand & rebalancing allocation...', 'Inventory Optimizer');
      const data = await inventoryApi.reseedSample();
      setSummary(data);
      setApprovedAllocations([]);
      localStorage.removeItem('datalyze_approved_transfers');
      toast.success('Inventory state rebalanced across fulfillment nodes.', 'Rebalancing Complete');
    } catch (err) {
      console.error('Failed to reseed inventory', err);
      toast.error('Failed to reseed inventory hubs.', 'Error');
    } finally {
      setReseedLoading(false);
    }
  };

  const handleApproveAllocation = async (action: InventoryAllocationRecommendation) => {
    try {
      const res = await inventoryApi.approveTransfer(action.item_id || 1, action.units_to_transfer);
      const updated = [...approvedAllocations, action.id];
      setApprovedAllocations(updated);
      localStorage.setItem('datalyze_approved_transfers', JSON.stringify(updated));
      toast.success(
        res.message || `Approved transfer of ${action.units_to_transfer} units of "${action.product_name}" to ${action.dest_warehouse_name}.`,
        'Transfer Scheduled & Synced'
      );
      await fetchInventory();
    } catch (err) {
      toast.error('Failed to execute transfer.', 'Transfer Error');
    }
  };

  const handleCreatePurchaseOrder = (item: InventoryItem) => {
    const recommendedQty = Math.max(item.reorder_point * 2 - item.current_stock, 50);
    setOrderQuantity(recommendedQty);
    setOrderModalItem(item);
  };

  const handleConfirmPurchaseOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!orderModalItem) return;

    setOrderLoading(true);
    setTimeout(() => {
      setOrderLoading(false);
      toast.success(
        `Draft Purchase Order created for ${orderQuantity} units of SKU "${orderModalItem.sku}".`,
        'PO Generated'
      );
      setOrderModalItem(null);
    }, 600);
  };

  const currency = company?.currency || 'USD';

  const handleRiskFilter = (rf: string) => {
    setRiskFilter(rf);
    localStorage.setItem('datalyze_inv_risk', rf);
  };

  const filteredItems = (summary?.items || []).filter((item) => {
    return riskFilter === 'ALL' || item.stockout_risk.toLowerCase() === riskFilter.toLowerCase();
  });

  const columns: ColumnDef<InventoryItem>[] = [
    {
      key: 'sku',
      header: 'SKU Code',
      sortable: true,
      render: (item) => (
        <span className="font-mono font-bold text-[#6B4226] dark:text-[#8C5E3C]">
          {item.sku}
        </span>
      ),
    },
    {
      key: 'name',
      header: 'Product Name',
      sortable: true,
      render: (item) => (
        <div>
          <p className="font-semibold text-neutral-900 dark:text-neutral-100">{item.name}</p>
          <p className="text-[11px] text-neutral-500">{item.category || item.warehouse_name || 'General'}</p>
        </div>
      ),
    },
    {
      key: 'current_stock',
      header: 'Current Stock',
      sortable: true,
      isNumeric: true,
      render: (item) => (
        <span className="font-bold text-neutral-900 dark:text-neutral-100">
          {item.current_stock.toLocaleString()} units
        </span>
      ),
    },
    {
      key: 'reorder_point',
      header: 'Safety Stock Limit',
      sortable: true,
      isNumeric: true,
      render: (item) => (
        <span className="text-neutral-500">
          {item.reorder_point.toLocaleString()} units
        </span>
      ),
    },
    {
      key: 'projected_days_left',
      header: 'Runway (Days)',
      sortable: true,
      isNumeric: true,
      render: (item) => {
        const isLow = item.projected_days_left <= 5;
        return (
          <span className={`font-bold ${isLow ? 'text-red-600' : 'text-neutral-800 dark:text-neutral-200'}`}>
            {item.projected_days_left} days
          </span>
        );
      },
    },
    {
      key: 'stockout_risk',
      header: 'Stockout Risk',
      align: 'center',
      sortable: true,
      render: (item) => {
        if (item.stockout_risk === 'critical') {
          return <Badge variant="critical" dot pulse>Critical</Badge>;
        }
        if (item.stockout_risk === 'medium') {
          return <Badge variant="warning" dot>Medium</Badge>;
        }
        return <Badge variant="healthy">Healthy</Badge>;
      },
    },
    {
      key: 'actions',
      header: 'Action',
      align: 'right',
      render: (item) => (
        <Button
          variant="outline"
          size="xs"
          onClick={(e) => {
            e.stopPropagation();
            handleCreatePurchaseOrder(item);
          }}
          leftIcon={<ShoppingCart className="w-3 h-3 text-[#6B4226] dark:text-[#8C5E3C]" />}
        >
          Draft PO
        </Button>
      ),
    },
  ];

  const totalItems = summary?.total_items || summary?.items?.length || 0;
  const lowStock = summary?.critical_stock_count || 0;

  const dynamicEyebrow =
    totalItems > 0
      ? `${totalItems} Tracked SKU${totalItems === 1 ? '' : 's'}${lowStock > 0 ? ` • ${lowStock} Low Stock Reorders` : ' • Healthy Stock Levels'}`
      : 'Inventory Engine Ready • Awaiting Catalog';

  return (
    <div className="space-y-6 sm:space-y-8 animate-fade-in">
      {/* Header with Dynamic Contextual Eyebrow */}
      <PageHeader
        stage={dynamicEyebrow}
        stageIcon={<Boxes className="w-4 h-4 text-[#6B4226] dark:text-[#D5B79F]" />}
        title="Smart Inventory"
        description="Track stock levels, prevent items from running out, and transfer units between locations."
        actions={
          <Button
            variant="primary"
            size="sm"
            isLoading={reseedLoading}
            onClick={handleReseed}
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            Refresh Stock Numbers
          </Button>
        }
      />

      <StateView
        isLoading={loading}
        isError={!!errorMsg}
        errorMessage={errorMsg || undefined}
        onRetry={fetchInventory}
        loadingSkeleton="table"
        isEmpty={!summary || summary.items.length === 0}
        emptyIcon={Boxes}
        emptyTitle="No Inventory Records Uploaded"
        emptyDescription="Upload your inventory spreadsheet or warehouse catalog in the Data Pipeline to monitor stock levels, runway, and risk."
        emptyAction={
          <Button
            variant="primary"
            size="sm"
            onClick={() => navigate('/data')}
            leftIcon={<Boxes className="w-3.5 h-3.5" />}
          >
            Go to Data Pipeline to Upload File
          </Button>
        }
      >
        {summary && (
          <div className="space-y-6 sm:space-y-8">
            {/* Overview Metric Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card className="p-4">
                <span className="text-xs font-medium text-neutral-500 font-mono block uppercase">
                  Total Products
                </span>
                <p className="text-2xl font-extrabold text-neutral-900 dark:text-neutral-100 font-mono mt-1">
                  {summary.total_items || summary.items.length}
                </p>
                <p className="text-[11px] text-neutral-400 mt-1 font-sans">Across {summary.total_warehouses || 4} locations</p>
              </Card>

              <Card className="p-4 border-l-2 border-l-red-500">
                <span className="text-xs font-medium text-neutral-500 font-mono block uppercase">
                  Low Stock Warning
                </span>
                <p className="text-2xl font-extrabold text-red-600 dark:text-red-400 font-mono mt-1">
                  {summary.critical_stock_count || 0}
                </p>
                <p className="text-[11px] text-neutral-400 mt-1 font-sans">Running low within 3 days</p>
              </Card>

              <Card className="p-4 border-l-2 border-l-amber-500">
                <span className="text-xs font-medium text-neutral-500 font-mono block uppercase">
                  Storage Space Used
                </span>
                <p className="text-2xl font-extrabold text-amber-600 dark:text-amber-400 font-mono mt-1">
                  {summary.average_capacity_utilization?.toFixed(1) || '72.5'}%
                </p>
                <p className="text-[11px] text-neutral-400 mt-1 font-sans">Average across warehouses</p>
              </Card>

              <Card className="p-4">
                <span className="text-xs font-medium text-neutral-500 font-mono block uppercase">
                  Total Stock Value
                </span>
                <p className="text-2xl font-extrabold text-[#6B4226] dark:text-[#8C5E3C] font-mono mt-1">
                  {formatKPIValue(summary.total_inventory_value || 0, 'currency', currency)}
                </p>
                <p className="text-[11px] text-neutral-400 mt-1 font-sans">Total value on hand</p>
              </Card>
            </div>

            {/* Regional Fulfillment Hub Capacity Gauges */}
            {summary.warehouses && summary.warehouses.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-xs font-bold text-neutral-500 font-mono uppercase tracking-wider">
                  Storage Locations ({summary.warehouses.length})
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  {summary.warehouses.map((wh) => (
                    <Card key={wh.id} className="p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-xs text-neutral-900 dark:text-neutral-100 font-mono truncate mr-2" title={wh.name}>
                          {wh.name}
                        </span>
                        <Badge variant="brand" size="xs">
                          {wh.region}
                        </Badge>
                      </div>
                      <div>
                        <div className="flex items-center justify-between text-xs font-mono">
                          <span className="text-neutral-500">Utilization:</span>
                          <span className="font-bold text-neutral-900 dark:text-neutral-100">
                            {wh.current_utilization}%
                          </span>
                        </div>
                        <div className="w-full bg-neutral-200 dark:bg-neutral-700 h-2 rounded-full overflow-hidden mt-1.5">
                          <div
                            className={`h-full rounded-full transition-all duration-300 ${
                              wh.current_utilization > 90
                                ? 'bg-red-500'
                                : wh.current_utilization > 75
                                ? 'bg-amber-500'
                                : 'bg-emerald-500'
                            }`}
                            style={{ width: `${Math.min(100, wh.current_utilization)}%` }}
                          />
                        </div>
                      </div>
                      <div className="flex items-center justify-between text-[11px] text-neutral-400 font-mono pt-1">
                        <span>Max: {wh.capacity.toLocaleString()}</span>
                        <span>SKUs: {wh.item_count}</span>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            )}

            {/* Recommended Rebalance Actions */}
            {summary.allocations && summary.allocations.length > 0 && (
              <div className="space-y-3">
                <div className="flex items-center space-x-2">
                  <Sparkles className="w-4 h-4 text-amber-500" />
                  <h3 className="text-sm font-bold text-neutral-900 dark:text-neutral-100 tracking-tight">
                    Recommended Inter-Hub Stock Transfers ({summary.allocations.length})
                  </h3>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {summary.allocations.map((act) => {
                    const isApproved = approvedAllocations.includes(act.id);

                    return (
                      <Card key={act.id} className="p-4 sm:p-5 flex flex-col justify-between space-y-4">
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="font-mono text-xs font-bold text-[#6B4226] dark:text-[#8C5E3C]">
                              SKU: {act.sku} • {act.product_name}
                            </span>
                            <Badge variant={isApproved ? 'healthy' : 'warning'}>
                              {isApproved ? 'Approved' : 'Recommended'}
                            </Badge>
                          </div>

                          <div className="flex items-center space-x-2 text-xs font-medium text-neutral-800 dark:text-neutral-200">
                            <span className="px-2 py-1 bg-neutral-100 dark:bg-neutral-800 rounded-lg">
                              {act.source_warehouse_name}
                            </span>
                            <ArrowRight className="w-3.5 h-3.5 text-neutral-400 shrink-0" />
                            <span className="px-2 py-1 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 rounded-lg">
                              {act.dest_warehouse_name}
                            </span>
                          </div>

                          <p className="text-xs text-neutral-500 leading-relaxed">
                            {act.reason}
                          </p>
                        </div>

                        <div className="flex items-center justify-between pt-2 border-t border-neutral-100 dark:border-neutral-800">
                          <span className="text-xs font-mono font-bold text-neutral-900 dark:text-neutral-100">
                            Transfer: {act.units_to_transfer.toLocaleString()} units
                          </span>

                          <Button
                            variant={isApproved ? 'secondary' : 'primary'}
                            size="xs"
                            disabled={isApproved}
                            onClick={() => handleApproveAllocation(act)}
                            leftIcon={isApproved ? <Check className="w-3 h-3" /> : undefined}
                          >
                            {isApproved ? 'Transfer Scheduled' : 'Approve Transfer'}
                          </Button>
                        </div>
                      </Card>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Inventory SKU Directory Table */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-neutral-900 dark:text-neutral-100 tracking-tight">
                  Tracked SKU Inventory Directory
                </h3>
              </div>

              <DenseTable
                columns={columns}
                data={filteredItems}
                keyField="id"
                searchPlaceholder="Search SKU, product title, or warehouse..."
                pageSize={10}
                headerSlot={
                  <div className="flex items-center space-x-1.5 overflow-x-auto">
                    {['ALL', 'critical', 'medium', 'low'].map((r) => (
                      <button
                        key={r}
                        onClick={() => handleRiskFilter(r)}
                        className={`px-3 py-1 text-xs font-semibold rounded-lg uppercase tracking-wider transition-colors cursor-pointer ${
                          riskFilter === r
                            ? 'bg-[#6B4226] dark:bg-[#7A4B2C] text-white shadow-xs'
                            : 'bg-white dark:bg-neutral-900 text-neutral-600 dark:text-neutral-300 hover:text-neutral-900 border border-neutral-200 dark:border-neutral-700'
                        }`}
                      >
                        {r}
                      </button>
                    ))}
                  </div>
                }
              />
            </div>
          </div>
        )}
      </StateView>

      {/* Draft Purchase Order Modal */}
      <Modal
        isOpen={!!orderModalItem}
        onClose={() => setOrderModalItem(null)}
        title={`Draft Purchase Order: ${orderModalItem?.name}`}
        description={`SKU: ${orderModalItem?.sku} • Current Stock: ${orderModalItem?.current_stock} units`}
        icon={<ShoppingCart className="w-5 h-5" />}
      >
        {orderModalItem && (
          <form onSubmit={handleConfirmPurchaseOrder} className="space-y-4">
            <div className="p-3.5 rounded-xl bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 grid grid-cols-2 gap-3 text-xs">
              <div>
                <span className="text-neutral-400 font-mono">Safety Reorder Point:</span>
                <p className="font-bold text-neutral-900 dark:text-neutral-100">
                  {orderModalItem.reorder_point} units
                </p>
              </div>
              <div>
                <span className="text-neutral-400 font-mono">Cost Price:</span>
                <p className="font-bold text-neutral-900 dark:text-neutral-100">
                  {formatKPIValue(orderModalItem.cost_price || 25, 'currency', currency)}
                </p>
              </div>
            </div>

            <FormField
              label="Order Quantity (Units)"
              required
              helperText="Recommended based on projected depletion rate"
            >
              <Input
                type="number"
                min="1"
                required
                value={orderQuantity}
                onChange={(e) => setOrderQuantity(parseInt(e.target.value, 10) || 0)}
              />
            </FormField>

            <div className="flex items-center justify-end space-x-2.5 pt-3 border-t border-neutral-100 dark:border-neutral-800">
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => setOrderModalItem(null)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                size="sm"
                isLoading={orderLoading}
                leftIcon={<ShoppingCart className="w-3.5 h-3.5" />}
              >
                Generate PO Draft
              </Button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
};
