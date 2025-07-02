'use client';

import { useState, useCallback, useEffect, useRef, useMemo } from 'react';
import Layout from '@/components/Layout';
import api from '@/lib/api';
import { Upload, FileText, CheckCircle, XCircle, AlertCircle, X, Info } from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import { useRouter } from 'next/navigation';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import type { UploadHistoryItem, UploadWarning, UploadResponse } from '@/types/upload';

interface PlatformAccount {
  id: number;
  platform: string;
  nickname?: string;
  client_id: string;
}

const REDIRECT_TIMEOUT_MS = 3000; // Configurable redirect timeout

export default function UploadPage() {
  const router = useRouter();
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');
  const [selectedAccount, setSelectedAccount] = useState('');
  const [uploadType, setUploadType] = useState<'holdings' | 'transactions'>('holdings');
  const [sourceType, setSourceType] = useState<'zerodha' | 'generic'>('zerodha');
  const [uploadProgress, setUploadProgress] = useState<string>('');
  const [uploadPercentage, setUploadPercentage] = useState<number>(0);
  const [platformAccounts, setPlatformAccounts] = useState<PlatformAccount[]>([]);
  const [accountsLoading, setAccountsLoading] = useState(true);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadHistory, setUploadHistory] = useState<UploadHistoryItem[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [uploadWarnings, setUploadWarnings] = useState<UploadWarning[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [accountError, setAccountError] = useState<string>('');
  const abortControllerRef = useRef<AbortController | null>(null);
  const redirectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    fetchPlatformAccounts();
    fetchUploadHistory();
  }, []);

  const fetchPlatformAccounts = async () => {
    try {
      setAccountError('');
      const response = await api.get('/portfolios/platform-accounts');
      setPlatformAccounts(response.data);
      if (response.data.length === 1) {
        setSelectedAccount(response.data[0].id.toString());
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to load platform accounts. Please refresh the page or contact support.';
      setAccountError(errorMessage);
      if (process.env.NODE_ENV === 'development') {
        console.error('Failed to fetch platform accounts:', error);
      }
    } finally {
      setAccountsLoading(false);
    }
  };
  
  const fetchUploadHistory = async () => {
    setHistoryLoading(true);
    try {
      const response = await api.get<UploadHistoryItem[]>('/uploads/import-history?limit=5');
      setUploadHistory(response.data);
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Failed to fetch upload history:', error);
      }
    } finally {
      setHistoryLoading(false);
    }
  };

  const validateFile = useCallback((file: File): string | null => {
    // Check file type
    const fileName = file.name.toLowerCase();
    if (!fileName.endsWith('.csv') && !fileName.endsWith('.xlsx') && !fileName.endsWith('.xls') && !fileName.endsWith('.pdf')) {
      return 'Please upload a CSV, Excel, or PDF file';
    }
    
    // Check file size (max 10MB)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      return 'File size must be less than 10MB';
    }
    
    // Check if file is empty
    if (file.size === 0) {
      return 'File is empty';
    }
    
    return null;
  }, []);

  const onDrop = useCallback(async (acceptedFiles: File[], rejectedFiles: any[]) => {
    if (rejectedFiles.length > 0) {
      setUploadStatus('error');
      setMessage('Invalid file type. Please upload a CSV, Excel, or PDF file.');
      return;
    }
    
    if (acceptedFiles.length === 0) return;
    
    const file = acceptedFiles[0];
    const validationError = validateFile(file);
    
    if (validationError) {
      setUploadStatus('error');
      setMessage(validationError);
      return;
    }
    
    setSelectedFile(file);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('platform_account_id', selectedAccount);

    setUploadStatus('uploading');
    setMessage('');
    setUploadProgress('Uploading file...');
    setUploadPercentage(20);
    setUploadWarnings([]); // Clear previous warnings
    
    // Create new abort controller for this upload
    abortControllerRef.current = new AbortController();

    try {
      let endpoint = '';
      const isExcelFile = file.name.toLowerCase().endsWith('.xlsx') || file.name.toLowerCase().endsWith('.xls');
      const isPDFFile = file.name.toLowerCase().endsWith('.pdf');
      
      if (isPDFFile) {
        // Use PDF endpoint for PDF files
        endpoint = '/uploads/pdf/holdings';
      } else if (isExcelFile) {
        // Use Excel endpoint for Excel files
        endpoint = '/uploads/excel/holdings';
      } else if (sourceType === 'zerodha') {
        endpoint = uploadType === 'holdings' 
          ? '/uploads/zerodha/holdings' 
          : '/uploads/zerodha/transactions';
      } else {
        endpoint = '/uploads/generic/holdings';  // Generic only supports holdings for now
      }
      
      if (process.env.NODE_ENV === 'development') {
        console.log('Upload endpoint:', endpoint);
        console.log('Source type:', sourceType);
        console.log('File type:', isPDFFile ? 'PDF' : isExcelFile ? 'Excel' : 'CSV');
      }
        
      setUploadProgress(isPDFFile ? 'Processing PDF document...' : isExcelFile ? 'Processing Excel sheets...' : 'Processing CSV data...');
      setUploadPercentage(50);
      const response = await api.post<UploadResponse>(endpoint, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        signal: abortControllerRef.current.signal
      });
      
      if (uploadType === 'holdings' && response.data.prices_updated !== undefined) {
        setUploadProgress(`Imported ${response.data.imported_count} holdings. Updated ${response.data.prices_updated} prices.`);
        setUploadPercentage(90);
      }
      
      setUploadStatus('success');
      setMessage(response.data.message);
      setUploadPercentage(100);
      
      // Store warnings if any
      if (response.data.warnings && response.data.warnings.length > 0) {
        setUploadWarnings(response.data.warnings);
      }
      
      // Handle duplicate holdings
      if (response.data.has_duplicates && response.data.duplicate_holdings) {
        const duplicateWarnings: UploadWarning[] = response.data.duplicate_holdings.map((dup) => ({
          type: 'duplicate',
          symbol: dup.symbol,
          message: `${dup.symbol}: Updated quantity from ${dup.old_quantity} to ${dup.new_quantity}, avg price from ₹${dup.old_avg_price} to ₹${dup.new_avg_price}`,
          old_quantity: dup.old_quantity,
          new_quantity: dup.new_quantity,
          old_avg_price: dup.old_avg_price,
          new_avg_price: dup.new_avg_price
        }));
        setUploadWarnings(prev => [...prev, ...duplicateWarnings]);
      }
      
      // Add sheet summary info to message if it's Excel
      if (response.data.sheet_summaries) {
        const sheetInfo = response.data.sheet_summaries.map((s) => 
          `${s.sheet}: ${s.imported} imported, ${s.updated} updated`
        ).join('; ');
        setMessage(response.data.message + ` (${sheetInfo})`);
      }
      
      // Clear progress after 3 seconds
      // Reset form after success
      setSelectedFile(null);
      // Refresh upload history
      fetchUploadHistory();
      
      redirectTimeoutRef.current = setTimeout(() => {
        setUploadProgress('');
        setUploadPercentage(0);
        // Navigate to holdings page after successful upload
        if (uploadType === 'holdings') {
          router.push('/dashboard/holdings');
        }
      }, REDIRECT_TIMEOUT_MS);
    } catch (error: any) {
      if (error.name === 'CanceledError') {
        setUploadStatus('idle');
        setMessage('Upload cancelled');
      } else {
        setUploadStatus('error');
        setMessage(error.response?.data?.detail || 'Upload failed');
      }
      setUploadProgress('');
      setUploadPercentage(0);
    }
  }, [selectedAccount, uploadType, sourceType, router]);

  const dropzoneConfig = useMemo(() => ({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'application/pdf': ['.pdf']
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
    disabled: !selectedAccount || uploadStatus === 'uploading',
    multiple: false,
    onDragEnter: () => {},
    onDragLeave: () => {},
    validator: (file: File) => {
      const validationError = validateFile(file);
      if (validationError) {
        return {
          code: 'file-invalid',
          message: validationError
        };
      }
      return null;
    }
  }), [onDrop, selectedAccount, uploadStatus, validateFile]);

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone(dropzoneConfig);
  
  // Add keyboard shortcut for upload (Ctrl/Cmd + U)
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'u' && selectedFile && selectedAccount) {
        e.preventDefault();
        onDrop([selectedFile], []);
      }
    };
    
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [selectedFile, selectedAccount, onDrop]);
  
  const cancelUpload = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setUploadStatus('idle');
      setMessage('Upload cancelled');
      setUploadProgress('');
    }
  };

  // Cleanup abort controller and timeout on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (redirectTimeoutRef.current) {
        clearTimeout(redirectTimeoutRef.current);
      }
    };
  }, []);

  return (
    <ErrorBoundary>
      <Layout>
      <div className="space-y-6">
        <div className="sr-only">
          <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-indigo-600 text-white px-4 py-2 rounded-md">
            Skip to main content
          </a>
        </div>
        <h1 className="text-2xl font-semibold text-gray-900" id="main-content">Upload Portfolio Data</h1>

        {/* Instructions */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 sm:p-6">
          <div className="flex items-start">
            <Info className="h-5 w-5 text-blue-400 mt-0.5 flex-shrink-0" />
            <div className="ml-3 flex-1">
              <h2 className="text-base sm:text-lg font-medium text-blue-900">How to export portfolio data</h2>
          
              {selectedAccount && platformAccounts.find(acc => acc.id.toString() === selectedAccount) && (
                <div className="mt-3 space-y-4">
                  {platformAccounts.find(acc => acc.id.toString() === selectedAccount)?.platform.toLowerCase() === 'zerodha' && (
                    <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-2">Zerodha Console</h3>
                  <ol className="list-decimal list-inside space-y-1 text-xs sm:text-sm text-gray-600">
                    <li>Login to <a href="https://console.zerodha.com" target="_blank" rel="noopener noreferrer" className="text-blue-700 hover:text-blue-800 underline inline-flex items-center" aria-label="Open Zerodha Console in new tab">
                      console.zerodha.com
                      <svg className="h-3 w-3 ml-1" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                        <path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z"/>
                        <path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z"/>
                      </svg>
                    </a></li>
                    <li>For Holdings: Go to Portfolio → Holdings → Download (CSV)</li>
                    <li>For Transactions: Go to Reports → Tradebook → Select date range → Download</li>
                  </ol>
                </div>
              )}
              
              {platformAccounts.find(acc => acc.id.toString() === selectedAccount)?.platform.toLowerCase() === 'groww' && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-2">Groww</h3>
                  <ol className="list-decimal list-inside space-y-1 text-sm text-gray-600">
                    <li>Login to Groww app or website</li>
                    <li>Go to Investments → Stocks</li>
                    <li>Click on Download/Export option</li>
                  </ol>
                </div>
              )}
              
              {platformAccounts.find(acc => acc.id.toString() === selectedAccount)?.platform.toLowerCase() === 'upstox' && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-2">Upstox</h3>
                  <ol className="list-decimal list-inside space-y-1 text-sm text-gray-600">
                    <li>Login to Upstox Pro Web</li>
                    <li>Go to Reports → Holdings Report</li>
                    <li>Export as CSV</li>
                  </ol>
                </div>
                  )}
                </div>
              )}
              
              {!selectedAccount && (
                <p className="text-sm text-blue-700 mt-2">Select a platform account above to see specific export instructions</p>
              )}
            </div>
          </div>
        </div>

        {/* Account Selection */}
        <div className="bg-white shadow rounded-lg p-4 sm:p-6">
          <h2 className="text-base sm:text-lg font-medium text-gray-900 mb-4">Select Account</h2>
          <div className="space-y-4">
            <div>
              <label htmlFor="platform-account-select" className="block text-sm font-medium text-gray-700">Platform Account</label>
              {accountsLoading ? (
                <div className="mt-1">
                  <div className="animate-pulse">
                    <div className="h-10 bg-gray-200 rounded-md w-full"></div>
                  </div>
                  <p className="mt-2 text-xs text-gray-500 flex items-center">
                    <LoadingSpinner size="sm" className="mr-2" />
                    Loading platform accounts...
                  </p>
                </div>
              ) : accountError ? (
                <div className="mt-1 border border-red-300 rounded-md bg-red-50 p-3">
                  <div className="flex">
                    <XCircle className="h-5 w-5 text-red-400 flex-shrink-0" />
                    <div className="ml-3">
                      <p className="text-sm text-red-800">{accountError}</p>
                      <button
                        onClick={() => {
                          setAccountsLoading(true);
                          fetchPlatformAccounts();
                        }}
                        className="mt-2 text-sm font-medium text-red-600 hover:text-red-500 focus:outline-none focus:underline"
                      >
                        Try again
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <select
                  id="platform-account-select"
                  value={selectedAccount}
                  onChange={(e) => setSelectedAccount(e.target.value)}
                  className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                  disabled={accountsLoading}
                  aria-label="Select platform account"
                  aria-required="true"
                  aria-invalid={!selectedAccount && uploadStatus === 'error'}
                  aria-describedby={!selectedAccount ? "account-required-message" : undefined}
                >
                  <option value="">Select an account</option>
                  {platformAccounts.map(account => (
                    <option key={account.id} value={account.id}>
                      {account.nickname || `${account.platform} - ${account.client_id}`}
                    </option>
                  ))}
                </select>
              )}
              
              {platformAccounts.length === 0 && !accountsLoading && (
                <p className="mt-2 text-sm text-amber-600">
                  No platform accounts found. Please add an account in Settings.
                </p>
              )}
            </div>

            {selectedAccount && platformAccounts.find(acc => acc.id.toString() === selectedAccount)?.platform.toLowerCase() === 'zerodha' && (
              <div>
                <label className="block text-sm font-medium text-gray-700">File Format</label>
                <div className="mt-2 space-y-3">
                  <label className="flex items-start cursor-pointer hover:bg-gray-50 p-3 rounded-lg border border-gray-200 transition-colors">
                    <input
                      type="radio"
                      value="zerodha"
                      checked={sourceType === 'zerodha'}
                      onChange={(e) => setSourceType(e.target.value as 'zerodha')}
                      className="form-radio h-4 w-4 text-indigo-600 focus:ring-indigo-500 focus:ring-2 mt-0.5"
                    />
                    <div className="ml-3">
                      <span className="font-medium text-gray-900">Zerodha Console Format</span>
                      <p className="text-xs text-gray-500 mt-1">Direct export from Zerodha Console (Holdings/Tradebook)</p>
                    </div>
                  </label>
                  <label className="flex items-start cursor-pointer hover:bg-gray-50 p-3 rounded-lg border border-gray-200 transition-colors">
                    <input
                      type="radio"
                      value="generic"
                      checked={sourceType === 'generic'}
                      onChange={(e) => setSourceType(e.target.value as 'generic')}
                      className="form-radio h-4 w-4 text-indigo-600 focus:ring-indigo-500 focus:ring-2 mt-0.5"
                    />
                    <div className="ml-3">
                      <span className="font-medium text-gray-900">Custom Format</span>
                      <p className="text-xs text-gray-500 mt-1">Generic CSV with flexible column names (Stock Name, Price, etc.)</p>
                    </div>
                  </label>
                </div>
              </div>
            )}
            
            {sourceType === 'zerodha' && (
              <div>
                <label className="block text-sm font-medium text-gray-700">Upload Type</label>
                <div className="mt-2 space-x-4">
                  <label className="inline-flex items-center">
                    <input
                      type="radio"
                      value="holdings"
                      checked={uploadType === 'holdings'}
                      onChange={(e) => setUploadType(e.target.value as 'holdings')}
                      className="form-radio h-4 w-4 text-indigo-600 focus:ring-indigo-500 focus:ring-2"
                    />
                    <span className="ml-2">Holdings</span>
                  </label>
                  <label className="inline-flex items-center">
                    <input
                      type="radio"
                      value="transactions"
                      checked={uploadType === 'transactions'}
                      onChange={(e) => setUploadType(e.target.value as 'transactions')}
                      className="form-radio h-4 w-4 text-indigo-600 focus:ring-indigo-500 focus:ring-2"
                    />
                    <span className="ml-2">Transactions</span>
                  </label>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Upload Area */}
        <div className="bg-white shadow rounded-lg p-4 sm:p-6">
          <h2 className="text-base sm:text-lg font-medium text-gray-900 mb-4">Upload Portfolio File</h2>
          
          <div
            {...getRootProps()}
            className={`mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-dashed rounded-md transition-all duration-200
              ${!selectedAccount || uploadStatus === 'uploading' ? 'cursor-not-allowed' : 'cursor-pointer'}
              ${isDragReject ? 'border-red-400 bg-red-50' : isDragActive ? 'border-indigo-400 bg-indigo-50' : 
                !selectedAccount ? 'border-gray-300 bg-gray-100' : 'border-gray-300 hover:border-gray-400'}
              ${uploadStatus === 'uploading' ? 'opacity-75 pointer-events-none' : ''}
              focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2
            `}
            role="button"
            aria-label={!selectedAccount ? "Drop zone for file upload. Please select an account first." : "Drop zone for file upload. Click or drag and drop a file here."}
            aria-disabled={!selectedAccount || uploadStatus === 'uploading'}
            tabIndex={!selectedAccount || uploadStatus === 'uploading' ? -1 : 0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                const input = document.querySelector('input[type="file"]') as HTMLInputElement;
                input?.click();
              }
            }}
          >
            <div className="space-y-1 text-center">
              <Upload className={`mx-auto h-12 w-12 ${isDragReject ? 'text-red-400' : !selectedAccount ? 'text-gray-300' : 'text-gray-400'}`} />
              {isDragReject ? (
                <p className="text-sm text-red-600">Invalid file type or size</p>
              ) : (
                <>
                  <div className="flex flex-wrap justify-center text-sm text-gray-600">
                    <label className={`relative rounded-md font-medium ${!selectedAccount ? 'cursor-not-allowed text-gray-400' : 'cursor-pointer text-indigo-600 hover:text-indigo-500'}`}>
                      <span>Upload a file</span>
                      <input {...getInputProps()} aria-label="File input" disabled={!selectedAccount || uploadStatus === 'uploading'} />
                    </label>
                    <p className={`pl-1 ${!selectedAccount ? 'text-gray-400' : ''}`}>or drag and drop</p>
                  </div>
                  <p className={`text-xs ${!selectedAccount ? 'text-gray-400' : 'text-gray-500'}`}>CSV, Excel, or PDF files (max 10MB)</p>
                </>
              )}
            </div>
          </div>

          {!selectedAccount && (
            <p id="account-required-message" className="mt-2 text-sm text-red-600" role="alert">Please select an account first</p>
          )}
          
          {selectedFile && (
            <div className="mt-3 flex items-center justify-between bg-gray-50 px-3 py-2 rounded-md">
              <div className="flex items-center min-w-0">
                <FileText className="h-5 w-5 text-gray-400 mr-2 flex-shrink-0" />
                <div className="min-w-0">
                  <p className="text-sm text-gray-700 truncate" title={selectedFile.name}>
                    {selectedFile.name}
                  </p>
                  <p className="text-xs text-gray-500">
                    {selectedFile.size < 1024 * 1024 
                      ? `${(selectedFile.size / 1024).toFixed(1)} KB`
                      : `${(selectedFile.size / (1024 * 1024)).toFixed(2)} MB`
                    }
                  </p>
                </div>
              </div>
              <button
                onClick={() => {
                  setSelectedFile(null);
                  setUploadStatus('idle');
                  setMessage('');
                  setUploadProgress('');
                }}
                className="text-sm text-red-600 hover:text-red-500 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 rounded px-2 py-1"
                aria-label="Remove selected file"
              >
                Remove
              </button>
            </div>
          )}
        </div>

        {/* Upload Status */}
        {uploadStatus !== 'idle' && (
          <div className={`rounded-md p-4 ${
            uploadStatus === 'success' ? 'bg-green-50' : 
            uploadStatus === 'error' ? 'bg-red-50' : 
            'bg-blue-50'
          }`}
            role="status"
            aria-live="polite"
            aria-atomic="true"
          >
            <div className="flex">
              <div className="flex-shrink-0">
                {uploadStatus === 'uploading' && <LoadingSpinner size="sm" />}
                {uploadStatus === 'success' && <CheckCircle className="h-5 w-5 text-green-400" />}
                {uploadStatus === 'error' && <XCircle className="h-5 w-5 text-red-400" />}
              </div>
              <div className="ml-3 flex-1">
                <p className={`text-sm font-medium ${
                  uploadStatus === 'success' ? 'text-green-800' : 
                  uploadStatus === 'error' ? 'text-red-800' : 
                  'text-blue-800'
                }`}>
                  {uploadStatus === 'uploading' && uploadProgress ? uploadProgress : 
                   uploadStatus === 'uploading' ? 'Uploading...' : message}
                </p>
                {uploadStatus === 'uploading' && (
                  <div className="mt-2">
                    <div className="flex items-center">
                      <div className="flex-1 mr-4">
                        <div className="bg-blue-200 rounded-full overflow-hidden h-2">
                          <div 
                            className="bg-blue-600 h-full transition-all duration-300 ease-out"
                            style={{ width: `${uploadPercentage}%` }}
                            role="progressbar"
                            aria-valuenow={uploadPercentage}
                            aria-valuemin={0}
                            aria-valuemax={100}
                          />
                        </div>
                      </div>
                      <span className="text-xs text-blue-700 font-medium">{uploadPercentage}%</span>
                    </div>
                  </div>
                )}
                {uploadProgress && uploadStatus === 'success' && (
                  <p className="text-sm text-green-600 mt-1">{uploadProgress}</p>
                )}
              </div>
              {uploadStatus === 'uploading' && (
                <button
                  onClick={cancelUpload}
                  className="ml-auto flex-shrink-0 p-1 rounded-md hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  aria-label="Cancel upload"
                >
                  <X className="h-4 w-4 text-blue-600" />
                </button>
              )}
            </div>
          </div>
        )}
        
        {/* Upload Warnings */}
        {uploadWarnings.length > 0 && uploadStatus === 'success' && (
          <div className="rounded-md bg-amber-50 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <AlertCircle className="h-5 w-5 text-amber-400" />
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-amber-800">
                  Upload completed with warnings
                </h3>
                <div className="mt-2 text-sm text-amber-700">
                  {uploadWarnings.some(w => w.type === 'duplicate') && (
                    <>
                      <p className="mb-2 font-medium">Duplicate holdings were updated:</p>
                      <ul className="space-y-1 mb-4">
                        {uploadWarnings.filter(w => w.type === 'duplicate').map((warning, index) => (
                          <li key={`dup-${index}`} className="text-sm">
                            • {warning.message}
                          </li>
                        ))}
                      </ul>
                    </>
                  )}
                  
                  {uploadWarnings.some(w => w.type !== 'duplicate') && (
                    <>
                      <p className="mb-2">Some stocks had missing fields. Default values were applied:</p>
                      <ul className="space-y-1" role="list">
                        {uploadWarnings.filter(w => w.type !== 'duplicate').map((warning, index) => (
                          <li key={`warning-${index}`} className="flex items-start">
                            <span className="font-medium">{warning.symbol}</span>
                            <span className="mx-1" aria-hidden="true">-</span>
                            <span>Row {warning.row_number}: Missing {warning.missing_fields?.join(', ')}</span>
                            {warning.missing_fields?.includes('quantity') && (
                              <span className="ml-1 text-amber-600">(defaulted to 1)</span>
                            )}
                          </li>
                        ))}
                      </ul>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* File Format Example */}
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <div className="flex flex-col sm:flex-row sm:justify-between items-start">
            <div className="mb-2 sm:mb-0">
              <h3 className="text-sm font-medium text-gray-900 flex items-center">
                <Info className="h-4 w-4 mr-1 flex-shrink-0" aria-hidden="true" />
                <span>Expected File Format</span>
              </h3>
            </div>
            <div className="text-xs text-gray-500 hidden sm:block">
              <span className="sr-only">Keyboard shortcut:</span>
              <kbd className="px-2 py-1 bg-gray-100 rounded" title="Control key">Ctrl</kbd>
              <span className="mx-1" aria-hidden="true">+</span>
              <kbd className="px-2 py-1 bg-gray-100 rounded" title="U key">U</kbd>
              <span className="ml-1">to upload</span>
            </div>
          </div>
          <div className="mb-3 flex justify-between items-center">
            <p className="text-xs text-gray-600">Supported formats:</p>
            <a href="#" className="text-xs text-indigo-600 hover:text-indigo-500 underline" onClick={(e) => { e.preventDefault(); alert('Sample files coming soon!'); }}>
              Download sample files
            </a>
          </div>
          <div className="space-y-3">
            <div>
              <p className="text-xs font-semibold text-gray-700">CSV Files:</p>
              {sourceType === 'zerodha' ? (
                <code className="text-xs bg-gray-100 p-2 rounded block overflow-x-auto">
                  Symbol, Quantity Available, Average Price, Previous Closing Price, Unrealized P&L
                </code>
              ) : (
                <div className="space-y-2">
                  <div className="overflow-x-auto">
                    <code className="text-xs bg-gray-100 p-2 rounded block whitespace-nowrap">
                      Stock Name, Average Price, Current Market Price (optional)
                    </code>
                  </div>
                  <p className="text-xs text-gray-500">
                    The parser will auto-detect columns with names like: Stock Name, Symbol, 
                    Average Price, Owned Price, Current Price, Market Price, etc.
                  </p>
                </div>
              )}
            </div>
            
            <div>
              <p className="text-xs font-semibold text-gray-700">Excel Files (.xlsx, .xls):</p>
              <p className="text-xs text-gray-500">
                Excel files with multiple sheets are supported. The parser will automatically detect:
              </p>
              <ul className="text-xs text-gray-500 list-disc list-inside mt-1">
                <li>Stock holdings in sheets with stock-related columns</li>
                <li>Mutual fund holdings in sheets with fund-related columns (NAV, Units, Scheme Name)</li>
                <li>Each sheet will be processed separately</li>
              </ul>
            </div>
          </div>
        </div>
        
        {/* Upload History */}
        <div className="bg-white shadow-sm rounded-lg p-4 sm:p-6 border border-gray-200">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-base sm:text-lg font-medium text-gray-900">Recent Uploads</h2>
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="text-sm text-indigo-600 hover:text-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 rounded px-2 py-1"
              aria-expanded={showHistory}
              aria-controls="upload-history"
            >
              {showHistory ? 'Hide' : 'Show'} History
            </button>
          </div>
          
          {historyLoading ? (
            <div className="flex flex-col items-center justify-center py-8 space-y-2">
              <LoadingSpinner size="md" />
              <p className="text-sm text-gray-500">Loading upload history...</p>
            </div>
          ) : uploadHistory.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-4">No upload history yet</p>
          ) : (
            showHistory && (
              <div className="space-y-2" id="upload-history">
                {uploadHistory.map((history) => (
                  <div key={history.id} className="flex flex-col sm:flex-row sm:justify-between sm:items-center py-2 border-b border-gray-200 last:border-0 gap-2">
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-gray-900 truncate" title={history.file_name}>
                        {history.file_name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {new Date(history.imported_at).toLocaleDateString()} at {new Date(history.imported_at).toLocaleTimeString()}
                      </p>
                    </div>
                    <div className="text-left sm:text-right flex-shrink-0">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        history.import_status === 'success' ? 'bg-green-100 text-green-800' : 
                        history.import_status === 'failed' ? 'bg-red-100 text-red-800' : 
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        <span className="sr-only">Status:</span>
                        {history.import_status}
                      </span>
                      {history.records_imported > 0 && (
                        <p className="text-xs text-gray-500 mt-1">{history.records_imported} records</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )
          )}
        </div>
      </div>
    </Layout>
    </ErrorBoundary>
  );
}