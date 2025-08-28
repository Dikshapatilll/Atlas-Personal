export enum PartNumberCategory {
  MISSING_EXTENSION = 'Missing Extension',
  SURFACE_BODY = 'Surface Body',
  INVALID_LENGTH = 'Non-10-Digit',
  NON_ENGLISH_CHARS = 'Incorrect Naming',
}

export interface PartNumber {
  id: string; 
  value: string;
  category: PartNumberCategory;
  reportId: string;
  dateAdded: string;
  status: 'open' | 'corrected';
  dateCorrected?: string;
}

export interface QAReport {
  id: string;
  fileName: string;
  uploadDate: string;
  totalPartsAnalyzed: number;
  sheetStats: {
    sheetName: string;
    totalRows: number;
    issueRows: number;
  }[];
}

export interface ChartData {
  name: PartNumberCategory | string;
  count: number;
}

export interface ChatMessage {
  sender: 'user' | 'bot';
  text: string;
}

// NEW: Authentication types
export interface User {
  id: string;
  email: string;
  name: string;
  role: 'employee' | 'admin';
}

export type UserRole = 'employee' | 'admin';