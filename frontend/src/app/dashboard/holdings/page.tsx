'use client';

import { useEffect, useState, useRef, useMemo, useCallback } from 'react';
import Layout from '@/components/Layout';
import api from '@/lib/api';
import { NetworkError } from '@/lib/network-monitor';
import { ArrowUp, ArrowDown, RefreshCw, Trash2, Edit, Plus, X, Check, AlertTriangle, ChevronUp, ChevronDown, XCircle } from 'lucide-react';

interface Holding {
  id: number;
  symbol: string;
  exchange: string;
  asset_type: 'stock' | 'mutual_fund' | 'sgb' | 'etf' | 'reit';
  quantity: number;
  average_price: number;
  current_price: number;
  current_value: number;
  pnl: number;
  pnl_percentage: number;
  platform_account: {
    platform: string;
    nickname: string;
    client_id: string;
  };
}

type SortField = 'symbol' | 'platform' | 'account_id' | 'quantity' | 'average_price' | 'current_price' | 'current_value' | 'pnl';
type SortDirection = 'asc' | 'desc';

export default function HoldingsPage() {
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [updating, setUpdating] = useState(false);
  const [updateProgress, setUpdateProgress] = useState<string>('');
  const [filter, setFilter] = useState<'all' | 'stocks' | 'etfs' | 'mutual_funds' | 'sgb' | 'reit'>('all');
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState({ quantity: 0, average_price: 0 });
  const [editErrors, setEditErrors] = useState({ quantity: '', average_price: '' });
  const [deleting, setDeleting] = useState<number | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [bulkDeleting, setBulkDeleting] = useState(false);
  const [sortField, setSortField] = useState<SortField>('symbol');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(20);
  const [deletedHoldings, setDeletedHoldings] = useState<Holding[]>([]);
  const [showUndoNotification, setShowUndoNotification] = useState(false);
  const [undoTimeLeft, setUndoTimeLeft] = useState(10);
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
  const undoTimerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    fetchHoldings();
  }, []);

  const fetchHoldings = async () => {
    try {
      setError('');
      console.log('Fetching holdings...');
      const response = await api.get('/portfolios/holdings');
      console.log('Holdings response:', response.data);
      // Sort by symbol A-Z by default
      const sortedData = response.data.sort((a: Holding, b: Holding) => 
        a.symbol.localeCompare(b.symbol)
      );
      setHoldings(sortedData);
    } catch (error: any) {
      console.error('Failed to fetch holdings:', error);
      if (error instanceof NetworkError) {
        setError('Network error: Please check your internet connection and try again.');
      } else if (error.response?.status === 401) {
        setError('Session expired. Please login again.');
        // Don't redirect here, let the interceptor handle it
      } else {
        setError(error.response?.data?.detail || 'Failed to load holdings. Please try again.');
      }
      setHoldings([]); // Clear holdings on error
    } finally {
      setLoading(false);
    }
  };

  const updatePrices = async () => {
    setUpdating(true);
    setUpdateProgress('Fetching latest market prices...');
    
    try {
      const totalHoldings = holdings.length;
      setUpdateProgress(`Updating prices for ${totalHoldings} holdings...`);
      
      const response = await api.post('/market/update-holdings-prices');
      const updatedCount = response.data.updated_count || 0;
      
      setUpdateProgress(`Successfully updated ${updatedCount} of ${totalHoldings} holdings`);
      await fetchHoldings();
      
      // Clear progress message after 3 seconds
      setTimeout(() => setUpdateProgress(''), 3000);
    } catch (error: any) {
      console.error('Failed to update prices:', error);
      if (error instanceof NetworkError) {
        setUpdateProgress(error.message);
      } else {
        setUpdateProgress('Failed to update prices. Please try again.');
      }
      setTimeout(() => setUpdateProgress(''), 5000);
    } finally {
      setUpdating(false);
    }
  };

  const deleteHolding = async (id: number) => {
    setDeleting(id);
    try {
      await api.delete(`/portfolios/holdings/${id}`);
      await fetchHoldings();
    } catch (error) {
      console.error('Failed to delete holding:', error);
    } finally {
      setDeleting(null);
    }
  };

  const startEdit = (holding: Holding) => {
    setEditingId(holding.id);
    setEditForm({
      quantity: holding.quantity,
      average_price: holding.average_price
    });
    setEditErrors({ quantity: '', average_price: '' });
  };

  const validateEditForm = () => {
    const errors = { quantity: '', average_price: '' };
    let isValid = true;

    if (editForm.quantity <= 0 || isNaN(editForm.quantity)) {
      errors.quantity = 'Quantity must be greater than 0';
      isValid = false;
    }

    if (editForm.average_price < 0 || isNaN(editForm.average_price)) {
      errors.average_price = 'Price must be 0 or greater';
      isValid = false;
    }

    setEditErrors(errors);
    return isValid;
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditForm({ quantity: 0, average_price: 0 });
  };

  const saveEdit = async (id: number) => {
    if (!validateEditForm()) {
      return;
    }
    
    try {
      await api.put(`/portfolios/holdings/${id}`, editForm);
      await fetchHoldings();
      setEditingId(null);
      setEditErrors({ quantity: '', average_price: '' });
    } catch (error: any) {
      console.error('Failed to update holding:', error);
      alert(error.response?.data?.detail || 'Failed to update holding. Please try again.');
    }
  };

  const toggleSelection = (id: number) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIds(newSelected);
  };

  const toggleSelectAll = () => {
    const currentPageIds = new Set(paginatedHoldings.map(h => h.id));
    const allSelected = paginatedHoldings.every(h => selectedIds.has(h.id));
    
    if (allSelected) {
      // Deselect all on current page
      const newSelected = new Set(selectedIds);
      currentPageIds.forEach(id => newSelected.delete(id));
      setSelectedIds(newSelected);
    } else {
      // Select all on current page
      const newSelected = new Set(selectedIds);
      currentPageIds.forEach(id => newSelected.add(id));
      setSelectedIds(newSelected);
    }
  };

  const bulkDelete = async () => {
    if (selectedIds.size === 0) return;
    setShowDeleteConfirmation(true);
  };

  const confirmBulkDelete = async () => {
    setBulkDeleting(true);
    setShowDeleteConfirmation(false);
    
    // Store deleted holdings for undo
    const toDelete = holdings.filter(h => selectedIds.has(h.id));
    setDeletedHoldings(toDelete);
    
    // Remove from UI immediately for better UX
    setHoldings(holdings.filter(h => !selectedIds.has(h.id)));
    setSelectedIds(new Set());
    setBulkDeleting(false);
    
    // Show undo notification
    setShowUndoNotification(true);
    setUndoTimeLeft(10);
    
    // Clear any existing timer
    if (undoTimerRef.current) {
      clearInterval(undoTimerRef.current);
    }
    
    // Start countdown
    undoTimerRef.current = setInterval(() => {
      setUndoTimeLeft(prev => {
        if (prev <= 1) {
          if (undoTimerRef.current) {
            clearInterval(undoTimerRef.current);
            undoTimerRef.current = null;
          }
          // Perform actual deletion after timeout
          performActualDeletion(toDelete);
          setShowUndoNotification(false);
          return 10;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const performActualDeletion = async (holdingsToDelete: Holding[]) => {
    try {
      for (const holding of holdingsToDelete) {
        await api.delete(`/portfolios/holdings/${holding.id}`);
      }
      setDeletedHoldings([]);
    } catch (error) {
      console.error('Failed to delete holdings:', error);
      // Restore holdings on error
      await fetchHoldings();
    }
  };

  const undoDelete = () => {
    // Clear timer
    if (undoTimerRef.current) {
      clearInterval(undoTimerRef.current);
      undoTimerRef.current = null;
    }
    
    // Restore deleted holdings
    setHoldings([...holdings, ...deletedHoldings]);
    setDeletedHoldings([]);
    setShowUndoNotification(false);
    setUndoTimeLeft(10);
  };

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (undoTimerRef.current) {
        clearInterval(undoTimerRef.current);
      }
    };
  }, []);

  const formatCurrency = useCallback((value: number | null | undefined) => {
    if (value === null || value === undefined) {
      value = 0;
    }
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  }, []);

  const handleSort = useCallback((field: SortField) => {
    if (sortField === field) {
      // Toggle direction if clicking the same field
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      // Set new field with ascending order
      setSortField(field);
      setSortDirection('asc');
    }
  }, [sortField, sortDirection]);

  const sortHoldings = useCallback((holdings: Holding[]) => {
    return [...holdings].sort((a, b) => {
      let aValue: any;
      let bValue: any;

      switch (sortField) {
        case 'symbol':
          aValue = a.symbol;
          bValue = b.symbol;
          break;
        case 'platform':
          aValue = a.platform_account.platform;
          bValue = b.platform_account.platform;
          break;
        case 'account_id':
          aValue = a.platform_account.client_id;
          bValue = b.platform_account.client_id;
          break;
        case 'quantity':
          aValue = a.quantity;
          bValue = b.quantity;
          break;
        case 'average_price':
          aValue = a.average_price;
          bValue = b.average_price;
          break;
        case 'current_price':
          aValue = a.current_price;
          bValue = b.current_price;
          break;
        case 'current_value':
          aValue = a.current_value;
          bValue = b.current_value;
          break;
        case 'pnl':
          aValue = a.pnl || 0;
          bValue = b.pnl || 0;
          break;
        default:
          return 0;
      }

      // Handle string comparison
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortDirection === 'asc' 
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }

      // Handle number comparison
      if (sortDirection === 'asc') {
        return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
      } else {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
      }
    });
  }, [sortField, sortDirection]);

  const filteredHoldings = useMemo(() => {
    const filtered = holdings.filter(holding => {
      if (filter === 'all') return true;
      if (filter === 'stocks') return holding.asset_type === 'stock';
      if (filter === 'etfs') return holding.asset_type === 'etf';
      if (filter === 'mutual_funds') return holding.asset_type === 'mutual_fund';
      if (filter === 'sgb') return holding.asset_type === 'sgb';
      if (filter === 'reit') return holding.asset_type === 'reit';
      return true;
    });
    return sortHoldings(filtered);
  }, [holdings, filter, sortHoldings]);

  // Pagination calculations
  const { totalPages, startIndex, endIndex, paginatedHoldings } = useMemo(() => {
    const total = Math.ceil(filteredHoldings.length / itemsPerPage);
    const start = (currentPage - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    const paginated = filteredHoldings.slice(start, end);
    return { totalPages: total, startIndex: start, endIndex: end, paginatedHoldings: paginated };
  }, [filteredHoldings, currentPage, itemsPerPage]);

  // Reset to page 1 when filter changes
  useEffect(() => {
    setCurrentPage(1);
  }, [filter]);

  const goToPage = (page: number) => {
    setCurrentPage(page);
    // Scroll to top of table
    document.querySelector('.overflow-x-auto')?.scrollIntoView({ behavior: 'smooth' });
  };

  // Calculate counts for each asset type
  const assetCounts = useMemo(() => ({
    all: holdings.length,
    stocks: holdings.filter(h => h.asset_type === 'stock').length,
    etfs: holdings.filter(h => h.asset_type === 'etf').length,
    mutual_funds: holdings.filter(h => h.asset_type === 'mutual_fund').length,
    sgb: holdings.filter(h => h.asset_type === 'sgb').length,
    reit: holdings.filter(h => h.asset_type === 'reit').length
  }), [holdings]);

  if (loading) {
    return (
      <Layout>
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <div className="h-8 bg-gray-200 rounded w-32 animate-pulse"></div>
            <div className="h-10 bg-gray-200 rounded w-36 animate-pulse"></div>
          </div>
          
          {/* Skeleton for filter tabs */}
          <div className="border-b border-gray-200">
            <div className="flex space-x-8">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div key={i} className="h-10 w-20 bg-gray-200 rounded animate-pulse"></div>
              ))}
            </div>
          </div>
          
          {/* Skeleton for table */}
          <div className="bg-white shadow rounded-lg p-4">
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="flex items-center space-x-4">
                  <div className="h-4 w-4 bg-gray-200 rounded"></div>
                  <div className="h-12 bg-gray-200 rounded flex-1"></div>
                  <div className="h-12 bg-gray-200 rounded w-24"></div>
                  <div className="h-12 bg-gray-200 rounded w-24"></div>
                  <div className="h-12 bg-gray-200 rounded w-32"></div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  if (error && holdings.length === 0) {
    return (
      <Layout>
        <div className="flex flex-col justify-center items-center h-64 space-y-4">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
            <div className="flex items-start">
              <XCircle className="h-5 w-5 text-red-400 mt-0.5" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error loading holdings</h3>
                <p className="mt-2 text-sm text-red-700">{error}</p>
                <button
                  onClick={() => {
                    setLoading(true);
                    fetchHoldings();
                  }}
                  className="mt-3 text-sm font-medium text-red-600 hover:text-red-500 focus:outline-none focus:underline"
                >
                  Try again
                </button>
              </div>
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      {/* Delete Confirmation Modal */}
      {showDeleteConfirmation && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <AlertTriangle className="h-6 w-6 text-red-600" />
              </div>
              <div className="ml-3">
                <h3 className="text-lg font-medium text-gray-900">
                  Delete {selectedIds.size} holding{selectedIds.size > 1 ? 's' : ''}?
                </h3>
                <div className="mt-2">
                  <p className="text-sm text-gray-500">
                    This will delete the following holdings:
                  </p>
                  <ul className="mt-2 text-sm text-gray-600 max-h-32 overflow-y-auto">
                    {holdings
                      .filter(h => selectedIds.has(h.id))
                      .slice(0, 5)
                      .map(h => (
                        <li key={h.id} className="py-1">
                          • {h.symbol} ({h.quantity} shares)
                        </li>
                      ))}
                    {selectedIds.size > 5 && (
                      <li className="py-1 text-gray-500">
                        ...and {selectedIds.size - 5} more
                      </li>
                    )}
                  </ul>
                </div>
              </div>
            </div>
            <div className="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
              <button
                type="button"
                onClick={confirmBulkDelete}
                disabled={bulkDeleting}
                className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-red-600 text-base font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 sm:ml-3 sm:w-auto sm:text-sm"
              >
                Delete
              </button>
              <button
                type="button"
                onClick={() => setShowDeleteConfirmation(false)}
                className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:w-auto sm:text-sm"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Undo Notification */}
      {showUndoNotification && (
        <div className="fixed bottom-4 right-4 bg-gray-800 text-white p-4 rounded-lg shadow-lg z-50 flex items-center space-x-4">
          <div>
            <p className="font-medium">
              {deletedHoldings.length} holding{deletedHoldings.length > 1 ? 's' : ''} deleted
            </p>
            <p className="text-sm text-gray-300">
              Undo available for {undoTimeLeft} seconds
            </p>
          </div>
          <button
            onClick={undoDelete}
            className="px-4 py-2 bg-white text-gray-800 rounded hover:bg-gray-100 font-medium"
          >
            Undo
          </button>
        </div>
      )}
      
      <div className="space-y-6">
        {/* Error Banner */}
        {error && holdings.length > 0 && (
          <div className="bg-red-50 border-l-4 border-red-400 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <XCircle className="h-5 w-5 text-red-400" />
              </div>
              <div className="ml-3 flex-1">
                <p className="text-sm text-red-700">{error}</p>
              </div>
              <button
                onClick={() => {
                  setError('');
                  fetchHoldings();
                }}
                className="ml-3 text-sm font-medium text-red-600 hover:text-red-500 focus:outline-none focus:underline"
              >
                Retry
              </button>
            </div>
          </div>
        )}
        
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-semibold text-gray-900">Holdings</h1>
          <div className="space-x-3">
            {selectedIds.size > 0 && (
              <button
                onClick={bulkDelete}
                disabled={bulkDeleting}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
              >
                <Trash2 className={`mr-2 h-4 w-4 ${bulkDeleting ? 'animate-spin' : ''}`} />
                Delete Selected ({selectedIds.size})
              </button>
            )}
            <button
              onClick={updatePrices}
              disabled={updating}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              <RefreshCw className={`mr-2 h-4 w-4 ${updating ? 'animate-spin' : ''}`} />
              Update Prices
            </button>
          </div>
        </div>

        {/* Warning Banner for Holdings with Missing Data */}
        {holdings.some(h => h.quantity === 1 || h.average_price === 0) && (
          <div className="bg-amber-50 border-l-4 border-amber-400 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <AlertTriangle className="h-5 w-5 text-amber-400" />
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-amber-800">
                  Some holdings have missing data
                </h3>
                <div className="mt-2 text-sm text-amber-700">
                  <p>The following issues were detected in your holdings:</p>
                  <ul className="list-disc list-inside mt-1">
                    {holdings.some(h => h.quantity === 1) && (
                      <li>Holdings with quantity = 1 (likely missing from CSV upload)</li>
                    )}
                    {holdings.some(h => h.average_price === 0) && (
                      <li>Holdings with no average price</li>
                    )}
                  </ul>
                  <p className="mt-2">Look for the <AlertTriangle className="inline h-4 w-4 text-amber-500" /> icon next to affected values and click edit to update them.</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Update Progress Message */}
        {updateProgress && (
          <div className={`rounded-md p-4 ${
            updateProgress.includes('Failed') ? 'bg-red-50 text-red-800' : 
            updateProgress.includes('Successfully') ? 'bg-green-50 text-green-800' : 
            'bg-blue-50 text-blue-800'
          }`}>
            <div className="flex">
              <div className="flex-shrink-0">
                {updating && (
                  <RefreshCw className="h-5 w-5 animate-spin" />
                )}
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium">{updateProgress}</p>
              </div>
            </div>
          </div>
        )}

        {/* Filter Tabs */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {[
              { name: 'All', value: 'all' },
              { name: 'Stocks', value: 'stocks' },
              { name: 'ETFs', value: 'etfs' },
              { name: 'Mutual Funds', value: 'mutual_funds' },
              { name: 'SGBs', value: 'sgb' },
              { name: 'REITs', value: 'reit' }
            ].map((tab) => (
              <button
                key={tab.value}
                onClick={() => setFilter(tab.value as any)}
                className={`
                  whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm
                  ${filter === tab.value
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                {tab.name}
                <span className={`ml-2 text-xs px-2 py-0.5 rounded-full ${
                  filter === tab.value
                    ? 'bg-indigo-100 text-indigo-600'
                    : 'bg-gray-100 text-gray-600'
                }`}>
                  {assetCounts[tab.value as keyof typeof assetCounts]}
                </span>
              </button>
            ))}
          </nav>
        </div>

        {/* Holdings Table - Desktop */}
        <div className="hidden md:block bg-white shadow overflow-x-auto sm:rounded-lg">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 py-3 w-10">
                  <input
                    type="checkbox"
                    checked={paginatedHoldings.length > 0 && paginatedHoldings.every(h => selectedIds.has(h.id))}
                    onChange={toggleSelectAll}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                </th>
                <th 
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider min-w-[150px] cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('symbol')}
                >
                  <div className="flex items-center">
                    Symbol
                    {sortField === 'symbol' && (
                      sortDirection === 'asc' ? <ChevronUp className="ml-1 h-4 w-4" /> : <ChevronDown className="ml-1 h-4 w-4" />
                    )}
                  </div>
                </th>
                <th 
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider min-w-[120px] cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('platform')}
                >
                  <div className="flex items-center">
                    Platform
                    {sortField === 'platform' && (
                      sortDirection === 'asc' ? <ChevronUp className="ml-1 h-4 w-4" /> : <ChevronDown className="ml-1 h-4 w-4" />
                    )}
                  </div>
                </th>
                <th 
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider min-w-[100px] cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('account_id')}
                >
                  <div className="flex items-center">
                    Account ID
                    {sortField === 'account_id' && (
                      sortDirection === 'asc' ? <ChevronUp className="ml-1 h-4 w-4" /> : <ChevronDown className="ml-1 h-4 w-4" />
                    )}
                  </div>
                </th>
                <th 
                  className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider min-w-[100px] cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('quantity')}
                >
                  <div className="flex items-center justify-end">
                    Quantity
                    {sortField === 'quantity' && (
                      sortDirection === 'asc' ? <ChevronUp className="ml-1 h-4 w-4" /> : <ChevronDown className="ml-1 h-4 w-4" />
                    )}
                  </div>
                </th>
                <th 
                  className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider min-w-[120px] cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('average_price')}
                >
                  <div className="flex items-center justify-end">
                    Avg Price
                    {sortField === 'average_price' && (
                      sortDirection === 'asc' ? <ChevronUp className="ml-1 h-4 w-4" /> : <ChevronDown className="ml-1 h-4 w-4" />
                    )}
                  </div>
                </th>
                <th 
                  className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider min-w-[120px] cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('current_price')}
                >
                  <div className="flex items-center justify-end">
                    Current Price
                    {sortField === 'current_price' && (
                      sortDirection === 'asc' ? <ChevronUp className="ml-1 h-4 w-4" /> : <ChevronDown className="ml-1 h-4 w-4" />
                    )}
                  </div>
                </th>
                <th 
                  className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider min-w-[130px] cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('current_value')}
                >
                  <div className="flex items-center justify-end">
                    Current Value
                    {sortField === 'current_value' && (
                      sortDirection === 'asc' ? <ChevronUp className="ml-1 h-4 w-4" /> : <ChevronDown className="ml-1 h-4 w-4" />
                    )}
                  </div>
                </th>
                <th 
                  className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider min-w-[150px] cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('pnl')}
                >
                  <div className="flex items-center justify-end">
                    P&L
                    {sortField === 'pnl' && (
                      sortDirection === 'asc' ? <ChevronUp className="ml-1 h-4 w-4" /> : <ChevronDown className="ml-1 h-4 w-4" />
                    )}
                  </div>
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider min-w-[100px]">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {paginatedHoldings.map((holding) => (
                <tr 
                  key={holding.id}
                  className={holding.quantity === 1 || holding.average_price === 0 ? 'bg-amber-50' : ''}
                >
                  <td className="px-3 py-4">
                    <input
                      type="checkbox"
                      checked={selectedIds.has(holding.id)}
                      onChange={() => toggleSelection(holding.id)}
                      className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                    />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{holding.symbol}</div>
                      <div className="text-sm text-gray-500">{holding.exchange}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {holding.platform_account.platform}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 font-medium">
                    {holding.platform_account.client_id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                    {editingId === holding.id ? (
                      <div>
                        <input
                          type="number"
                          value={editForm.quantity}
                          onChange={(e) => setEditForm({ ...editForm, quantity: parseFloat(e.target.value) || 0 })}
                          className={`w-24 px-2 py-1 border rounded text-right ${editErrors.quantity ? 'border-red-500' : ''}`}
                          step="0.01"
                          min="0.01"
                          aria-invalid={!!editErrors.quantity}
                          aria-describedby={editErrors.quantity ? `quantity-error-${holding.id}` : undefined}
                        />
                        {editErrors.quantity && (
                          <p id={`quantity-error-${holding.id}`} className="text-red-500 text-xs mt-1">{editErrors.quantity}</p>
                        )}
                      </div>
                    ) : (
                      <div className="flex items-center justify-end gap-1">
                        {holding.quantity}
                        {holding.quantity === 1 && (
                          <div className="relative group">
                            <AlertTriangle 
                              className="h-4 w-4 text-amber-500" 
                              tabIndex={0}
                              role="img"
                              aria-label="Warning: Default quantity applied"
                            />
                            <div className="absolute right-0 top-6 invisible group-hover:visible group-focus-within:visible opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity duration-200 z-20 w-48 p-2 bg-gray-900 text-white text-xs rounded shadow-lg pointer-events-none">
                              <div className="absolute -top-1 right-4 w-2 h-2 bg-gray-900 transform rotate-45"></div>
                              Missing quantity in upload. Default value applied. Click edit to update.
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                    {editingId === holding.id ? (
                      <div>
                        <input
                          type="number"
                          value={editForm.average_price}
                          onChange={(e) => setEditForm({ ...editForm, average_price: parseFloat(e.target.value) || 0 })}
                          className={`w-28 px-2 py-1 border rounded text-right ${editErrors.average_price ? 'border-red-500' : ''}`}
                          step="0.01"
                          min="0"
                          aria-invalid={!!editErrors.average_price}
                          aria-describedby={editErrors.average_price ? `price-error-${holding.id}` : undefined}
                        />
                        {editErrors.average_price && (
                          <p id={`price-error-${holding.id}`} className="text-red-500 text-xs mt-1">{editErrors.average_price}</p>
                        )}
                      </div>
                    ) : (
                      <div className="flex items-center justify-end gap-1">
                        {formatCurrency(holding.average_price)}
                        {holding.average_price === 0 && (
                          <div className="relative group">
                            <AlertTriangle 
                              className="h-4 w-4 text-amber-500" 
                              tabIndex={0}
                              role="img"
                              aria-label="Warning: Missing average price"
                            />
                            <div className="absolute right-0 top-6 invisible group-hover:visible group-focus-within:visible opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity duration-200 z-20 w-48 p-2 bg-gray-900 text-white text-xs rounded shadow-lg pointer-events-none">
                              <div className="absolute -top-1 right-4 w-2 h-2 bg-gray-900 transform rotate-45"></div>
                              Missing price in upload. Click edit to update.
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                    {formatCurrency(holding.current_price)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                    {formatCurrency(holding.current_value)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                    <div className={(holding.pnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'}>
                      <div className="flex items-center justify-end">
                        {(holding.pnl || 0) >= 0 ? (
                          <ArrowUp className="h-4 w-4 mr-1" />
                        ) : (
                          <ArrowDown className="h-4 w-4 mr-1" />
                        )}
                        {formatCurrency(Math.abs(holding.pnl || 0))}
                      </div>
                      <div className="text-xs">
                        ({holding.pnl_percentage ? holding.pnl_percentage.toFixed(2) : '0.00'}%)
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <div className="flex items-center justify-center space-x-2">
                      {editingId === holding.id ? (
                        <>
                          <button
                            onClick={() => saveEdit(holding.id)}
                            className="text-green-600 hover:text-green-900"
                            title="Save"
                          >
                            <Check className="h-4 w-4" />
                          </button>
                          <button
                            onClick={cancelEdit}
                            className="text-gray-600 hover:text-gray-900"
                            title="Cancel"
                          >
                            <X className="h-4 w-4" />
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            onClick={() => startEdit(holding)}
                            className="text-indigo-600 hover:text-indigo-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 rounded"
                            title="Edit holding"
                            aria-label={`Edit ${holding.symbol}`}
                          >
                            <Edit className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => {
                              if (confirm(`Are you sure you want to delete ${holding.symbol}?`)) {
                                deleteHolding(holding.id);
                              }
                            }}
                            disabled={deleting === holding.id}
                            className="text-red-600 hover:text-red-900 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 rounded"
                            title="Delete holding"
                            aria-label={`Delete ${holding.symbol}`}
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          
          {filteredHoldings.length === 0 && (
            <div className="text-center py-12">
              <p className="text-gray-500">No holdings found</p>
            </div>
          )}
        </div>

        {/* Holdings Cards - Mobile */}
        <div className="md:hidden space-y-4">
          {paginatedHoldings.map((holding) => (
            <div 
              key={holding.id}
              className={`bg-white shadow rounded-lg p-4 ${holding.quantity === 1 || holding.average_price === 0 ? 'bg-amber-50' : ''}`}
            >
              <div className="flex justify-between items-start mb-3">
                <div className="flex items-start">
                  <input
                    type="checkbox"
                    checked={selectedIds.has(holding.id)}
                    onChange={() => toggleSelection(holding.id)}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded mt-1 mr-3"
                  />
                  <div>
                    <h3 className="text-lg font-medium text-gray-900">{holding.symbol}</h3>
                    <p className="text-sm text-gray-500">
                      {holding.exchange} • {holding.platform_account.platform}
                    </p>
                  </div>
                </div>
                <div className="flex space-x-2">
                  {editingId === holding.id ? (
                    <>
                      <button
                        onClick={() => saveEdit(holding.id)}
                        className="text-green-600 hover:text-green-900 p-1"
                        aria-label="Save"
                      >
                        <Check className="h-5 w-5" />
                      </button>
                      <button
                        onClick={cancelEdit}
                        className="text-gray-600 hover:text-gray-900 p-1"
                        aria-label="Cancel"
                      >
                        <X className="h-5 w-5" />
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        onClick={() => startEdit(holding)}
                        className="text-indigo-600 hover:text-indigo-900 p-1"
                        aria-label="Edit holding"
                      >
                        <Edit className="h-5 w-5" />
                      </button>
                      <button
                        onClick={() => {
                          if (confirm(`Are you sure you want to delete ${holding.symbol}?`)) {
                            deleteHolding(holding.id);
                          }
                        }}
                        disabled={deleting === holding.id}
                        className="text-red-600 hover:text-red-900 disabled:opacity-50 p-1"
                        aria-label="Delete holding"
                      >
                        <Trash2 className="h-5 w-5" />
                      </button>
                    </>
                  )}
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-gray-500">Quantity</p>
                  {editingId === holding.id ? (
                    <div>
                      <input
                        type="number"
                        value={editForm.quantity}
                        onChange={(e) => setEditForm({ ...editForm, quantity: parseFloat(e.target.value) || 0 })}
                        className={`mt-1 w-full px-2 py-1 border rounded ${editErrors.quantity ? 'border-red-500' : ''}`}
                        step="0.01"
                        min="0.01"
                      />
                      {editErrors.quantity && (
                        <p className="text-red-500 text-xs mt-1">{editErrors.quantity}</p>
                      )}
                    </div>
                  ) : (
                    <p className="font-medium flex items-center gap-1">
                      {holding.quantity}
                      {holding.quantity === 1 && (
                        <span className="relative group">
                          <AlertTriangle className="h-4 w-4 text-amber-500" aria-label="Default quantity applied" />
                          <span className="sr-only">Default quantity of 1 applied during import</span>
                        </span>
                      )}
                    </p>
                  )}
                </div>
                
                <div>
                  <p className="text-gray-500">Avg Price</p>
                  {editingId === holding.id ? (
                    <div>
                      <input
                        type="number"
                        value={editForm.average_price}
                        onChange={(e) => setEditForm({ ...editForm, average_price: parseFloat(e.target.value) || 0 })}
                        className={`mt-1 w-full px-2 py-1 border rounded ${editErrors.average_price ? 'border-red-500' : ''}`}
                        step="0.01"
                        min="0"
                      />
                      {editErrors.average_price && (
                        <p className="text-red-500 text-xs mt-1">{editErrors.average_price}</p>
                      )}
                    </div>
                  ) : (
                    <p className="font-medium flex items-center gap-1">
                      {formatCurrency(holding.average_price)}
                      {holding.average_price === 0 && (
                        <span className="relative group">
                          <AlertTriangle className="h-4 w-4 text-amber-500" aria-label="Missing average price" />
                          <span className="sr-only">Average price is missing</span>
                        </span>
                      )}
                    </p>
                  )}
                </div>
                
                <div>
                  <p className="text-gray-500">Current Price</p>
                  <p className="font-medium">{formatCurrency(holding.current_price)}</p>
                </div>
                
                <div>
                  <p className="text-gray-500">Current Value</p>
                  <p className="font-medium">{formatCurrency(holding.current_value)}</p>
                </div>
              </div>
              
              <div className="mt-3 pt-3 border-t">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500">P&L</span>
                  <div className={`text-right ${(holding.pnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    <div className="flex items-center">
                      {(holding.pnl || 0) >= 0 ? (
                        <ArrowUp className="h-4 w-4 mr-1" />
                      ) : (
                        <ArrowDown className="h-4 w-4 mr-1" />
                      )}
                      <span className="font-medium">{formatCurrency(Math.abs(holding.pnl || 0))}</span>
                    </div>
                    <p className="text-xs">
                      ({holding.pnl_percentage ? holding.pnl_percentage.toFixed(2) : '0.00'}%)
                    </p>
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          {filteredHoldings.length === 0 && (
            <div className="text-center py-12 bg-white rounded-lg">
              <p className="text-gray-500">No holdings found</p>
            </div>
          )}
        </div>

        {/* Pagination Controls */}
        {totalPages > 1 && (
          <div className="mt-4 flex items-center justify-between">
            <div className="text-sm text-gray-700">
              Showing {startIndex + 1} to {Math.min(endIndex, filteredHoldings.length)} of{' '}
              {filteredHoldings.length} holdings
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={() => goToPage(currentPage - 1)}
                disabled={currentPage === 1}
                className="px-3 py-1 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              
              {/* Page numbers */}
              <div className="flex space-x-1">
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let pageNum;
                  if (totalPages <= 5) {
                    pageNum = i + 1;
                  } else if (currentPage <= 3) {
                    pageNum = i + 1;
                  } else if (currentPage >= totalPages - 2) {
                    pageNum = totalPages - 4 + i;
                  } else {
                    pageNum = currentPage - 2 + i;
                  }
                  
                  return (
                    <button
                      key={pageNum}
                      onClick={() => goToPage(pageNum)}
                      className={`px-3 py-1 text-sm font-medium rounded-md ${
                        currentPage === pageNum
                          ? 'bg-indigo-600 text-white'
                          : 'text-gray-700 bg-white border border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      {pageNum}
                    </button>
                  );
                })}
              </div>
              
              <button
                onClick={() => goToPage(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="px-3 py-1 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}