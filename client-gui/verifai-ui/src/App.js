import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useParams } from 'react-router-dom';
import MainScreen from './MainScreen';
import Login from './Login';
import Registration from './Registration';
//import SessionView from './SessionView';
import MainScreenWrapper from './SessionView';
import { AuthProvider } from './AuthContext';
import { DataProvider } from './DataContext'; // Import the DataProvider
import UserCredential from './UserCredential';
import { MsalProvider } from "@azure/msal-react";
import { PublicClientApplication } from "@azure/msal-browser";
import { msalConfig, isSSOConfigured } from './msalConfig';

//function MainScreenWrapper(props) {
//  const { sessionId } = useParams();
//  return <MainScreen {...props} sessionId={sessionId} />;
//}
const msalInstance = isSSOConfigured ? new PublicClientApplication(msalConfig) : null;
export const BACKEND = process.env.REACT_APP_BACKEND;

function App() {


  return (
   isSSOConfigured ? (
   <MsalProvider instance={msalInstance}>
        <AuthProvider>
          <DataProvider>
            <Router>
            <Routes>
                 <Route path="/main" element={<MainScreen />} />
            <Route path="/login" element={<Login />} />
            <Route path="/registration" element={<Registration />} />
            <Route path="/user_credential" element={<UserCredential />} />
            <Route path="/" element={<Login />} />
            <Route path="/get_session/:sessionId" element={<MainScreenWrapper />} />
            </Routes>
            </Router>
          </DataProvider>
        </AuthProvider>
      </MsalProvider>
    ) : (
    <AuthProvider>
      <DataProvider>
        <Router>
          <Routes>
            <Route path="/main" element={<MainScreen />} />
            <Route path="/login" element={<Login />} />
            <Route path="/registration" element={<Registration />} />
            <Route path="/user_credential" element={<UserCredential />} />
            <Route path="/" element={<Login />} />
            <Route path="/get_session/:sessionId" element={<MainScreenWrapper />} />
          </Routes>
        </Router>
      </DataProvider>
    </AuthProvider>
  )
  );
}

export default App;

