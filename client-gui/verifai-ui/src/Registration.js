import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import logo from './verifai-logo.png';
import './Login.css';
import {BACKEND} from './App.js'

function getRedirectionPath() {
  
    const query = window.location.search;
    const params = new URLSearchParams(query);
    const redirectionPath = params.get('redirection')
  
    if(redirectionPath)
      return '/' + redirectionPath;
    else
      return '/login';
   
       
  }

function Registration() {
    const [name, setName] = useState('');
    const [surname, setSurname] = useState('');
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const navigate = useNavigate();

    
    const navigateLogin = () => {
        const redirectionPath = getRedirectionPath();
        navigate('/login?redirection=' + redirectionPath); 
    };

    const handleLogin = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch(BACKEND + 'registration', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name, surname, username, email, password })
            });
            if (response.ok) {
                alert('Registration completed successfully!');

                const redirectionPath = getRedirectionPath();
                navigate('/login?redirection=' + redirectionPath);
            } else if (response.status === 400) {
                alert('Username already registered');
            }
        } catch (error) {
            console.error('Login error:', error);
            alert('Login failed due to an unexpected error');
        }
    };


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
        <div class="special-h2">
            <h1>Registration</h1>
        </div>
        
        <form className="formClass" onSubmit={handleLogin}>
            <input className="formInput" type="text" placeholder="Name" onChange={e => setName(e.target.value)}/>
            <input className="formInput" type="text" placeholder="Surname" onChange={e => setSurname(e.target.value)}/>
            <input className="formInput" type="text" placeholder="E-mail" onChange={e => setEmail(e.target.value)}/>
            <input className="formInput" type="text" placeholder="Username" onChange={e => setUsername(e.target.value)}/>
            <input className="formInput" type="password" placeholder="Password" onChange={e => setPassword(e.target.value)}/>
            <button class="center-button" onClick={handleLogin}>Submit</button>
        </form>
        </div>
        <br></br>
        <p className='message'>Already have an account? Log in <targe><span onClick={navigateLogin} style={{ color: '#23a1ee', cursor: 'pointer' }}>here</span></targe>.</p>
        </div>
        </div>
    </div>
    
    );
}

export default Registration;
