import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import { AppModeProvider } from './contexts/AppModeContext';
import Header from './Header';
import LibraryView from './LibraryView';
import UploadView from './UploadView';
import CategoriesView from './CategoriesView';
import ToolsView from './ToolsView';
import ReadView from './ReadView';
import TestComponent from './TestComponent';
import BackendStatusIndicator from './components/BackendStatusIndicator';
import './App.css';

function App() {
  return (
    <ThemeProvider>
      <AppModeProvider>
        <Router>
          <div className="App">
            <Header />
            <main className="main-content">
              <Routes>
                <Route path="/" element={<LibraryView />} />
                <Route path="/upload" element={<UploadView />} />
                <Route path="/categories" element={<CategoriesView />} />
                <Route path="/tools" element={<ToolsView />} />
                <Route path="/leer/:id" element={<ReadView />} />
                <Route path="/test" element={<TestComponent />} />
              </Routes>
            </main>
            <BackendStatusIndicator />
          </div>
        </Router>
      </AppModeProvider>
    </ThemeProvider>
  );
}

export default App;