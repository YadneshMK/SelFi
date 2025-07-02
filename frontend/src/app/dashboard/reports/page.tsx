'use client';

import { useState } from 'react';
import Layout from '@/components/Layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { DatePickerWithRange } from '@/components/ui/date-range-picker';
import { Download, FileText, TrendingUp, TrendingDown, DollarSign, PieChart, Loader2, HelpCircle } from 'lucide-react';
import { DateRange } from 'react-day-picker';
import { addDays, format, isAfter, isBefore, differenceInDays, startOfDay } from 'date-fns';
import api from '@/lib/api';
import { useRouter } from 'next/navigation';

interface Report {
  id: string;
  title: string;
  description: string;
  icon: any;
}

interface RecentReport {
  id: number;
  type: string;
  title: string;
  dateRange: DateRange;
  generatedAt: Date;
  status: 'completed' | 'failed';
}

export default function ReportsPage() {
  const [dateRange, setDateRange] = useState<DateRange | undefined>({
    from: addDays(new Date(), -30),
    to: new Date(),
  });
  const [reportType, setReportType] = useState('portfolio-summary');
  const [reportFormat, setReportFormat] = useState('pdf');
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recentReports, setRecentReports] = useState<any[]>([]);
  const router = useRouter();

  const reports: Report[] = [
    {
      id: 'portfolio-summary',
      title: 'Portfolio Summary',
      description: 'Overview of your entire portfolio performance',
      icon: PieChart,
    },
    {
      id: 'gains-losses',
      title: 'Gains & Losses',
      description: 'Detailed report of realized and unrealized gains',
      icon: TrendingUp,
    },
    {
      id: 'tax-report',
      title: 'Tax Report',
      description: 'Capital gains report for tax filing (requires full year)',
      icon: FileText,
    },
    {
      id: 'transaction-history',
      title: 'Transaction History',
      description: 'Complete history of all transactions',
      icon: DollarSign,
    },
  ];

  // Date range presets
  const datePresets = [
    { label: 'Last 7 days', days: 7 },
    { label: 'Last 30 days', days: 30 },
    { label: 'Last 90 days', days: 90 },
    { label: 'Year to date', days: -1 }, // Special case
    { label: 'Last year', days: 365 },
  ];

  const applyDatePreset = (preset: { label: string; days: number }) => {
    const to = new Date();
    let from: Date;
    
    if (preset.days === -1) { // Year to date
      from = new Date(to.getFullYear(), 0, 1);
    } else {
      from = addDays(to, -preset.days);
    }
    
    setDateRange({ from, to });
    setError(null);
  };

  const validateDateRange = (): boolean => {
    if (!dateRange?.from || !dateRange?.to) {
      setError('Please select both start and end dates');
      return false;
    }

    const today = startOfDay(new Date());
    const from = startOfDay(dateRange.from);
    const to = startOfDay(dateRange.to);

    // Check if dates are in the future
    if (isAfter(from, today) || isAfter(to, today)) {
      setError('Report dates cannot be in the future');
      return false;
    }

    // Check if from date is after to date
    if (isAfter(from, to)) {
      setError('Start date must be before end date');
      return false;
    }

    // Check maximum date range (1 year)
    const daysDiff = differenceInDays(to, from);
    if (daysDiff > 365) {
      setError('Date range cannot exceed 1 year');
      return false;
    }

    // Specific validations for report types
    if (reportType === 'tax-report' && daysDiff < 365) {
      setError('Tax reports require a full financial year (365 days)');
      return false;
    }

    return true;
  };

  const handleGenerateReport = async () => {
    setError(null);
    
    if (!validateDateRange()) {
      return;
    }

    setIsGenerating(true);

    try {
      // Generate report
      const response = await api.post('/reports/generate', {
        report_type: reportType,
        start_date: format(dateRange.from, 'yyyy-MM-dd'),
        end_date: format(dateRange.to, 'yyyy-MM-dd'),
        format: reportFormat
      });

      // Download the report
      const mimeType = reportFormat === 'pdf' ? 'application/pdf' : 'text/csv';
      const blob = new Blob([response.data], { type: mimeType });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${reportType}_${format(new Date(), 'yyyy-MM-dd')}.${reportFormat}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      // Add to recent reports
      const newReport = {
        id: Date.now(),
        type: reportType,
        title: reports.find(r => r.id === reportType)?.title || 'Report',
        dateRange: { from: dateRange.from, to: dateRange.to },
        generatedAt: new Date(),
        status: 'completed'
      };
      setRecentReports(prev => [newReport, ...prev].slice(0, 5));
      
    } catch (error: any) {
      console.error('Report generation failed:', error);
      setError(error.response?.data?.detail || 'Failed to generate report. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
          <p className="text-gray-600 mt-1">
            Generate and download comprehensive reports for your investment portfolio
          </p>
        </div>

      {/* Main Report Generation Card */}
      <Card className="border-0 shadow-sm">
        <CardContent className="p-6 space-y-6 relative">
          {/* Loading State */}
          {isGenerating && (
            <div className="absolute inset-0 bg-white/90 backdrop-blur-sm flex items-center justify-center z-10 rounded-lg">
              <div className="text-center">
                <Loader2 className="h-8 w-8 animate-spin mx-auto mb-3 text-indigo-600" />
                <p className="text-base font-medium text-gray-900">Generating your report...</p>
                <p className="text-sm text-gray-500 mt-1">Please wait while we prepare your {reports.find(r => r.id === reportType)?.title}</p>
              </div>
            </div>
          )}
          {/* Step 1: Select Report Type */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">1. Choose Report Type</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {reports.map((report) => {
                const Icon = report.icon;
                return (
                  <div
                    key={report.id}
                    onClick={() => setReportType(report.id)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        setReportType(report.id);
                      }
                    }}
                    tabIndex={0}
                    role="radio"
                    aria-checked={reportType === report.id}
                    className={`relative flex p-4 border rounded-lg cursor-pointer transition-all hover:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 ${
                      reportType === report.id 
                        ? 'border-indigo-500 bg-indigo-50' 
                        : 'border-gray-200 bg-white'
                    }`}
                  >
                    <div className="flex items-start w-full">
                      <Icon className={`h-5 w-5 flex-shrink-0 mr-3 mt-0.5 ${
                        reportType === report.id ? 'text-indigo-600' : 'text-gray-400'
                      }`} />
                      <div className="flex-1">
                        <p className={`font-medium ${
                          reportType === report.id ? 'text-indigo-900' : 'text-gray-900'
                        }`}>
                          {report.title}
                        </p>
                        <p className="text-sm text-gray-600 mt-0.5">{report.description}</p>
                      </div>
                      {reportType === report.id && (
                        <div className="h-2 w-2 bg-indigo-600 rounded-full ml-3 mt-2" />
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
          {/* Step 2: Configure Options */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">2. Configure Options</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Date Range */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Date Range
                </label>
                <DatePickerWithRange 
                  id="date-range"
                  date={dateRange} 
                  setDate={(newDate) => {
                    setDateRange(newDate);
                    setError(null);
                  }}
                />
                {/* Quick Select Buttons */}
                <div className="mt-3">
                  <p className="text-xs text-gray-500 mb-2">Quick select:</p>
                  <div className="flex flex-wrap gap-2">
                    {datePresets.map((preset) => (
                      <button
                        key={preset.label}
                        onClick={() => applyDatePreset(preset)}
                        className="text-sm px-3 py-1 border border-gray-200 rounded-md bg-white hover:bg-gray-50 hover:border-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-1 transition-colors"
                        type="button"
                      >
                        {preset.label}
                      </button>
                    ))}
                  </div>
                  {dateRange?.from && dateRange?.to && (
                    <p className="text-sm text-gray-600 mt-2">
                      Selected: {differenceInDays(dateRange.to, dateRange.from) + 1} days
                    </p>
                  )}
                </div>
              </div>

              {/* Format Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Export Format
                </label>
                <div className="space-y-2">
                  <div
                    onClick={() => setReportFormat('pdf')}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        setReportFormat('pdf');
                      }
                    }}
                    tabIndex={0}
                    role="radio"
                    aria-checked={reportFormat === 'pdf'}
                    className={`relative flex p-3 border rounded-lg cursor-pointer transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 ${
                      reportFormat === 'pdf' 
                        ? 'border-indigo-500 bg-indigo-50' 
                        : 'border-gray-200 bg-white hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-start w-full">
                      <FileText className={`h-5 w-5 flex-shrink-0 mr-3 mt-0.5 ${
                        reportFormat === 'pdf' ? 'text-indigo-600' : 'text-gray-400'
                      }`} />
                      <div className="flex-1">
                        <p className="font-medium text-gray-900">PDF Document</p>
                        <p className="text-sm text-gray-500">Best for printing and sharing</p>
                      </div>
                      {reportFormat === 'pdf' && (
                        <div className="h-2 w-2 bg-indigo-600 rounded-full ml-3 mt-1.5" />
                      )}
                    </div>
                  </div>
                  <div
                    onClick={() => setReportFormat('csv')}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        setReportFormat('csv');
                      }
                    }}
                    tabIndex={0}
                    role="radio"
                    aria-checked={reportFormat === 'csv'}
                    className={`relative flex p-3 border rounded-lg cursor-pointer transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 ${
                      reportFormat === 'csv' 
                        ? 'border-indigo-500 bg-indigo-50' 
                        : 'border-gray-200 bg-white hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-start w-full">
                      <FileText className={`h-5 w-5 flex-shrink-0 mr-3 mt-0.5 ${
                        reportFormat === 'csv' ? 'text-indigo-600' : 'text-gray-400'
                      }`} />
                      <div className="flex-1">
                        <p className="font-medium text-gray-900">CSV Spreadsheet</p>
                        <p className="text-sm text-gray-500">Best for data analysis in Excel</p>
                      </div>
                      {reportFormat === 'csv' && (
                        <div className="h-2 w-2 bg-indigo-600 rounded-full ml-3 mt-1.5" />
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Error Alert */}
          {error && (
            <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-md">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3 flex-1">
                  <p className="text-sm text-red-700">{error}</p>
                </div>
                <button
                  onClick={() => setError(null)}
                  className="ml-3 text-red-400 hover:text-red-500"
                >
                  <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
            </div>
          )}

          {/* Generate Button */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-t pt-6">
            <div>
              <p className="text-sm text-gray-600">
                Your report will be downloaded automatically when ready
              </p>
            </div>
            <Button 
              onClick={handleGenerateReport} 
              className="px-6 w-full sm:w-auto"
              disabled={isGenerating || !dateRange?.from || !dateRange?.to}
            >
              {isGenerating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Generating Report...
                </>
              ) : (
                <>
                  <Download className="mr-2 h-4 w-4" />
                  Generate Report
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Recent Reports */}
      <Card className="border-0 shadow-sm">
        <CardContent className="p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Recent Reports</h2>
          {recentReports.length === 0 ? (
            <div className="text-center py-12">
              <div className="mx-auto w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                <FileText className="h-8 w-8 text-gray-400" aria-hidden="true" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No reports yet</h3>
              <p className="text-gray-500 max-w-sm mx-auto mb-6">
                Generate comprehensive reports for your portfolio by selecting a report type and date range above.
              </p>
              <div className="flex justify-center">
                <Button
                  variant="outline"
                  onClick={() => document.getElementById('report-type')?.focus()}
                >
                  Create Your First Report
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-2">
              {recentReports.map((report) => (
                <div
                  key={report.id}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-start space-x-3">
                    <div className={`p-2 rounded-lg flex-shrink-0 ${
                      report.status === 'completed' ? 'bg-green-100' : 'bg-red-100'
                    }`}>
                      <FileText className={`h-5 w-5 ${
                        report.status === 'completed' ? 'text-green-600' : 'text-red-600'
                      }`} />
                    </div>
                    <div>
                      <p className="font-medium text-sm">{report.title}</p>
                      <p className="text-xs text-gray-500">
                        {format(report.dateRange.from!, 'MMM d')} - {format(report.dateRange.to!, 'MMM d, yyyy')}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-500">
                      {format(report.generatedAt, 'MMM d, h:mm a')}
                    </p>
                    <p className={`text-xs font-medium ${
                      report.status === 'completed' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {report.status === 'completed' ? 'Completed' : 'Failed'}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}