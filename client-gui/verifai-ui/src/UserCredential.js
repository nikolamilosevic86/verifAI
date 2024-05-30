import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from './AuthContext';
import logo from './verifai-logo.png';
import './Login.css'; // Assuming you have similar styles for consistency

function UserCredential() {
    const [oldPassword, setOldPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const navigate = useNavigate();
    const { user, logout } = useAuth();

    const handleChangePassword = async (e) => {
        e.preventDefault();
        if (!user) {
            alert('Login before');
            return;
        }
        try {
            const response = await fetch('http://18.198.26.251:5001/change_password', {
                method: 'POST',
                headers: {
                    'Authorization': "Bearer " + user.token, 
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username: user.username, oldPassword:oldPassword, newPassword: newPassword })
            });
            if (response.ok) {
                alert('Password changed successfully');
                logout();
                navigate('/login');
            } else if (response.status === 401) {
                alert('Invalid old password');
            }
        } catch (error) {
            console.error('Change password error:', error);
            alert('Change password failed due to an unexpected error');
        }
    };

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const handleMain = () => {
        navigate('/main');
    };

    if (!user) {
        return (
            <div className="login-container">
                <h1>Login before</h1>
            </div>
        );
    }

    return (
        <div className="login-container">
            <img src={logo} alt="Logo" className="login-logo" />
            <div className="login-form">
                <h1>Change Password</h1>
                <form onSubmit={handleChangePassword}>
                    <input type="password" placeholder="Old Password" onChange={e => setOldPassword(e.target.value)} />
                    <input type="password" placeholder="New Password" onChange={e => setNewPassword(e.target.value)} />
                    <button className="center-button" onClick={handleChangePassword}>Change Password</button>
                </form>
                <button className="LogoutButton" onClick={handleLogout}>Logout</button>
                <button className='UserButton' onClick={handleMain}>Main</button>
            </div>
        </div>
    );
}

export default UserCredential;
