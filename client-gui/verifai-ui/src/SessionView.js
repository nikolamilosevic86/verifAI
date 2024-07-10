import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import MainScreen from './MainScreen';
import { BACKEND } from './App';

function MainScreenWrapper(props) {
    const { sessionId } = useParams();
    const [sessionData, setSessionData] = useState(null);

    useEffect(() => {
        async function fetchSessionData() {
            try {
                
                const response = await fetch(`${BACKEND}get_session/${sessionId}`);
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                const data = await response.json();
                setSessionData(data['state']);
            } catch (error) {
                console.error('Failed to fetch session data:', error);
            }
        }

        if (sessionId) {
            fetchSessionData();
        }
    }, [sessionId]);

  
    if (!sessionData) {
        return <div>Loading...</div>;
    }

   
    return <MainScreen {...props} sessionData={sessionData} />;
}

export default MainScreenWrapper;
