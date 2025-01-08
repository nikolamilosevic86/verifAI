import React, { useContext, useState, useEffect  } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from './AuthContext';
import logo from './verifai-logo.png';
import './Login.css';

function Login() {
   
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const navigate = useNavigate();
    
     const { user, login, loginWithAzure, isSSOConfigured } = useAuth();

    const handleAzureLogin = async () => {
        await loginWithAzure(navigate);
    };

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
            <div className='login-subcontainer'>
        <div className='login-text'>
        <img src={logo} alt="Logo" className="login-logo" />
        <div className='login-text-div'><p className='login-verifai'>VerifAI helps you find and summarize information you are looking for with verified references.</p>
        <p className='login-verifai-subtext'>New here? Learn more about VerifAI project at:   <a className='websiteLink' href="https://verifai-project.com/">Verif.ai Project Website</a></p>
        </div>
    
      
        </div>
        <div className='form-section-div'>
      
     
        <div className="login-form">
            <h1>Sign in</h1>
            <form className="formClass" onSubmit={handleLogin}>
                <input className="formInput" type="text" placeholder="Username" onChange={e => setUsername(e.target.value)}/>
                <input className="formInput" type="password" placeholder="Password" onChange={e => setPassword(e.target.value)}/>
                <button class="center-button" onClick={handleLogin}>Log In</button>
            </form>
            {isSSOConfigured && (
                    <button className="center-button azure-button" onClick={handleAzureLogin}>Sign in with Azure AD</button>
                )}
        </div>
        <br></br>
        <p className='message'>New to VerifAi app? <targe><span onClick={handleRegister} style={{ color: '#23a1ee', cursor: 'pointer' }}>Sign up</span></targe> to get instant access.</p>
        </div>
        </div>
    </div>
    
    );
}

export default Login;
