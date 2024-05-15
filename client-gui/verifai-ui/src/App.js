import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import MainScreen from './MainScreen';
import Login from './Login';
import Registration from './Registration';
import SessionView from './SessionView';
import { AuthProvider } from './AuthContext';
import { DataProvider } from './DataContext'; // Import the DataProvider


function App() {
  return (
    <AuthProvider>
      <DataProvider>
        <Router>
          <Routes>
            <Route path="/main" element={<MainScreen />} />
            <Route path="/login" element={<Login />} />
            <Route path="/registration" element={<Registration />} />
            <Route path="/" element={<Login />} />
            <Route path="/get_session/:sessionId" element={<SessionView />} />
          </Routes>
        </Router>
      </DataProvider>
    </AuthProvider>
  );
}

export default App;

