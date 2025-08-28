import React, { useState, useCallback, useEffect } from 'react';
import { HashRouter, Routes, Route } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import AdminPanel from './components/AdminPanel';
import { ReportDetailView } from './components/ReportDetailView';
import Header from './components/Header';
import { Chatbot } from './components/Chatbot';
import { PartNumber, QAReport } from './types';
import { supabaseService } from './services/supabaseService';
import { parseExcelFile } from './services/parserService';
import { AuthProvider, useAuth } from './context/AuthContext';
import LoginForm from './components/LoginForm';
import ProtectedRoute from './components/ProtectedRoute';

// Main app content that requires authentication
const AppContent: React.FC = () => {
  const [allParts, setAllParts] = useState<PartNumber[]>([]);
  const [reports, setReports] = useState<QAReport[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const { user, isLoading: authLoading } = useAuth();

  useEffect(() => {
    const loadData = async () => {
      try {
        const { parts, reports } = await supabaseService.fetchAllData();
        setAllParts(parts);
        setReports(reports);
      } catch (error) {
        console.error("Failed to fetch initial data", error);
      } finally {
        setIsLoading(false);
      }
    };

    if (user) {
      loadData();

      // WebSocket for backend notifications - only connect when user is authenticated
      const ws = new WebSocket('ws://localhost:8000/ws');
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'analyzed') {
          // Re-fetch data and update state instead of reloading the page
          loadData();
        }
      };
      
      return () => ws.close();
    }
  }, [user]);

  const handleFileUpload = useCallback(async (file: File) => {
    setIsUploading(true);
    setUploadError(null);
    try {
      const parsedData = await parseExcelFile(file);
      const { report: savedReport, parts: savedParts } = await supabaseService.addReport(parsedData.report, parsedData.parts);
      
      setAllParts(prevParts => [...prevParts, ...savedParts]);
      setReports(prevReports => [...prevReports, savedReport]);
    } catch (err) {
      console.error("Error processing file:", err);
      const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred.';
      setUploadError(errorMessage);
    } finally {
      setIsUploading(false);
    }
  }, []);

  const handlePartCorrected = useCallback(async (partId: string) => {
    try {
      const updatedPart = await supabaseService.updatePartStatus(partId, 'corrected');
      if (updatedPart) {
        setAllParts(prevParts => prevParts.map(part => part.id === partId ? updatedPart : part));
      } else {
        throw new Error(`Failed to update part ${partId} in the backend.`);
      }
    } catch (error) {
        console.error(error);
        throw error;
    }
  }, []);

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!user) {
    return <LoginForm />;
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-lg text-slate-600 animate-pulse">Loading QA Data...</p>
        </div>
      </div>
    );
  }

  return (
    <HashRouter>
      <div className="min-h-screen bg-slate-50 font-sans text-slate-800">
        <Header />
        <main className="max-w-7xl mx-auto p-4 sm:p-6 lg:p-8">
          <Routes>
            <Route 
              path="/admin" 
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <AdminPanel reports={reports} allParts={allParts} />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/admin/:reportId" 
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <ReportDetailView reports={reports} parts={allParts} />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/" 
              element={
                <ProtectedRoute allowedRoles={['employee', 'admin']}>
                  <Dashboard 
                    parts={allParts} 
                    reports={reports}
                    onFileUpload={handleFileUpload} 
                    onPartCorrected={handlePartCorrected} 
                    isUploading={isUploading}
                    uploadError={uploadError}
                  />
                </ProtectedRoute>
              } 
            />
          </Routes>
        </main>
        <Chatbot partsData={allParts} reportsData={reports} />
      </div>
    </HashRouter>
  );
};

// Main App component with AuthProvider
const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

export default App;