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

//function MainScreenWrapper(props) {
//  const { sessionId } = useParams();
//  return <MainScreen {...props} sessionId={sessionId} />;
//}

export const BACKEND = "http://127.0.0.1:5001/"//"https://api.verifai-project.com/";

function App() {


  return (
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
  );
}

export default App;

