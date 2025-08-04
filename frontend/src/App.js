import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Header from './Header';
import LibraryView from './LibraryView';
import UploadView from './UploadView';
import CategoriesView from './CategoriesView';
import ToolsView from './ToolsView';
import ReaderView from './ReaderView';
import ErrorBoundary from './ErrorBoundary';
import ModeNotification from './components/ModeNotification';
import { AppModeProvider } from './contexts/AppModeContext';
import './App.css';

function App() {
  return (
    <ErrorBoundary>
      <AppModeProvider>
        <BrowserRouter>
          <div className="App">
            <Header />
            <main className="App-content">
              <Routes>
                <Route path="/" element={<LibraryView />} />
                <Route path="/upload" element={<UploadView />} />
                <Route path="/etiquetas" element={<CategoriesView />} />
                <Route path="/herramientas" element={<ToolsView />} />
                <Route path="/leer/:bookId" element={<ReaderView />} />
              </Routes>
            </main>
            <ModeNotification />
          </div>
        </BrowserRouter>
      </AppModeProvider>
    </ErrorBoundary>
  );
}

export default App;