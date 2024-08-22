import React, { createContext, useContext, useState, useEffect } from 'react';
import { BACKEND } from './App.js';
const AuthContext = createContext(null) ?? {};

function getRedirectionPath() {
  
  const query = window.location.search;
  const params = new URLSearchParams(query);
  const redirectionPath = params.get('redirection')

  if(redirectionPath)
    return '/' + redirectionPath;
  else
    return '/main';
 
     
}

export const useAuth = () => useContext(AuthContext);
export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    

    const syncTokenFromLocalStorage = () => {
      const token = localStorage.getItem("token");
      const username = localStorage.getItem("username");
      
      if (token && token != "" && token != undefined) setUser({token: token, username: username});
    }

    useEffect(() => {
      syncTokenFromLocalStorage();
    }, []);

   

    const login = async (username, password, navigate) => {
    try {
        const response = await fetch(BACKEND + 'login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
                
            },
            body: JSON.stringify({ username: username, password: password })
        });

     

        if (response.ok) {
            const data = await response.json(); 
            localStorage.setItem("token",data.token);
            localStorage.setItem("username",username);
            setUser({ token: data.token, username: username}); 
            const redirectionPath = getRedirectionPath();
            navigate(redirectionPath);
            
        } else if (response.status === 401) {
            alert('Invalid username or password');
        }
    } catch (error) {
        console.error('Login error:', error);
        alert('Login failed due to an unexpected error');
    }
};
  

  const logout = async () => {
      localStorage.removeItem("token");
      localStorage.removeItem("username");
      setUser({token:null});
};

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export { AuthContext };