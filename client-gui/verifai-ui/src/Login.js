import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from './AuthContext';
import logo from './verifai-logo.png';
import './Login.css';

function Login() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const navigate = useNavigate();
    const { login } = useAuth();
    const handleLogin = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch('http://3.74.47.54:5001/login/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });
            if (response.ok) {
                const newUser = await response.json(); // Assume the response includes user data
                login(newUser);
                navigate('/main');
            } else if (response.status === 401) {
                alert('Invalid username or password');
            }
        } catch (error) {
            console.error('Login error:', error);
            alert('Login failed due to an unexpected error');
        }
    };

    const handleRegister = () => {
        navigate('/registration'); // Adjust the path according to your route settings
    };

    return (
        
        <div className="login-container">
        <img src={logo} alt="Logo" className="login-logo" />
        <div className="login-form">
            <h1>Sign in</h1>
            <input type="text" placeholder="Username" onChange={e => setUsername(e.target.value)}/>
            <input type="password" placeholder="Password" onChange={e => setPassword(e.target.value)}/>
            <button onClick={handleLogin}>Login</button>
        </div>
        <br></br>
        <p>New to VerifAi <targe><span onClick={handleRegister} style={{ color: 'blue', cursor: 'pointer' }}>join now</span></targe></p>
    </div>
    
    );
}

export default Login;
