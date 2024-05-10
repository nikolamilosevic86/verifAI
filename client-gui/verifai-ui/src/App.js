import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import MainScreen from './MainScreen';
import Login from './Login';
import Registration from './Registration'
import { AuthProvider } from './AuthContext'; // Import the AuthProvider

function App() {


  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/main" element={<MainScreen />} />
          <Route path="/login" element={<Login />} />
          <Route path="/registration" element={<Registration />} />
          <Route path="/" element={<Login />} />
        </Routes>
      </Router>
    </
    AuthProvider>
  );
}

export default App;
