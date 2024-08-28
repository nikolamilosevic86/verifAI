import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import logo from './verifai-logo.png';
import './Login.css';
import {BACKEND} from './App.js'

function Registration() {
    const [name, setName] = useState('');
    const [surname, setSurname] = useState('');
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const navigate = useNavigate();

    
    const navigateLogin = () => {
        navigate('/login'); 
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
                navigate('/login');
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
        <img src={logo} alt="Logo" className="login-logo" />
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
        <p>Already have an account? Log in <targe><span onClick={navigateLogin} style={{ color: '#23a1ee', cursor: 'pointer' }}>here</span></targe>.</p>
       
    </div>
    
    );
}

export default Registration;
