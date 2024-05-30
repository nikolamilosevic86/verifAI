import React, { createContext, useContext, useState, useEffect } from 'react';


const AuthContext = createContext(null) ?? {};

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    

    const syncTokenFromSessionStorage = () => {
      const token = sessionStorage.getItem("token");
      const username = sessionStorage.getItem("username");
      if (token && token != "" && token != undefined) setUser({token: token, username: username});
    }

    useEffect(() => {
      syncTokenFromSessionStorage();
    }, []);

    const login = async (username, password, navigate) => {
    try {
        const response = await fetch('http://18.198.26.251:5001/login/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        if (response.ok) {
            const data = await response.json(); 
            sessionStorage.setItem("token",data.token);
            sessionStorage.setItem("username",username);
            setUser({ token: data.token, username: username}); 
            navigate('/main');
        } else if (response.status === 401) {
            alert('Invalid username or password');
        }
    } catch (error) {
        console.error('Login error:', error);
        alert('Login failed due to an unexpected error');
    }
};
  

  const logout = async () => {
      sessionStorage.removeItem("token");
      sessionStorage.removeItem("username");
      setUser({token:null});
};

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export { AuthContext };