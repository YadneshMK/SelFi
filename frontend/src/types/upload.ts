export interface UploadHistoryItem {
  id: number;
  file_name: string;
  file_type: string;
  import_status: 'success' | 'failed' | 'processing';
  imported_at: string;
  records_imported: number;
  platform_account_id: number;
}

export interface UploadWarning {
  type: 'duplicate' | 'missing_fields' | 'validation' | string;
  symbol?: string;
  row_number?: number;
  missing_fields?: string[];
  message: string;
  old_quantity?: number;
  new_quantity?: number;
  old_avg_price?: number;
  new_avg_price?: number;
}

export interface UploadResponse {
  message: string;
  imported_count: number;
  prices_updated?: number;
  warnings?: UploadWarning[];
  has_duplicates?: boolean;
  duplicate_holdings?: UploadWarning[];
  sheet_summaries?: {
    sheet: string;
    imported: number;
    updated: number;
  }[];
}