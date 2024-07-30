import React, { useContext, useState, useEffect  } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from './AuthContext';
import logo from './verifai-logo.png';
import './Login.css';

function Login() {
   
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const navigate = useNavigate();
    
    const { user, login } = useAuth();
    

    const handleLogin = async (e) => {
        e.preventDefault();
        await login(username, password, navigate);
    }

    const handleRegister = () => {
        navigate('/registration'); 
    };


    useEffect(() => {
        if (user && user.token && user.token != "" && user.token != undefined) {
            navigate('/main');
        }
    }, [user, navigate]);

    return (
        
        <div className="login-container">
        <img src={logo} alt="Logo" className="login-logo" />
        <div className="login-form">
            <h1>Sign in</h1>
            <form onSubmit={handleLogin}>
                <input type="text" placeholder="Username" onChange={e => setUsername(e.target.value)}/>
                <input type="password" placeholder="Password" onChange={e => setPassword(e.target.value)}/>
                <button class="center-button" onClick={handleLogin}>Login</button>
            </form>
            
        </div>
        <br></br>
        <p>New to VerifAi app? <targe><span onClick={handleRegister} style={{ color: 'blue', cursor: 'pointer' }}>Sign up</span></targe> to get instant access.</p>
    </div>
    
    );
}

export default Login;
