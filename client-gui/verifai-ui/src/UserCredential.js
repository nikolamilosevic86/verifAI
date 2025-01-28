import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from './AuthContext';
import logo from './verifai-logo.png';
import logout_img from './new_logout.svg';
import './Login.css'; // Assuming you have similar styles for consistency

function UserCredential() {
    const [oldPassword, setOldPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const navigate = useNavigate();
    const { user, logout } = useAuth();
    const backend = process.env.REACT_APP_BACKEND;

    const handleChangePassword = async (e) => {
        e.preventDefault();
        if (!user) {
            alert('Login before');
            return;
        }
        try {
            const response = await fetch(backend + 'change_password', {
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

   /* if (!user) {
        return (
            <div className="login-container">
                <h1>Login before</h1>
            </div>
        );
    }*/

        if (!user) {
             
            const handleLogin = () => {                     
              navigate("/login/?redirection=user_credential");              

            }

            return (
                <div className='App'>
                    <div className='login-message'>
                        <img src={logo} alt="Logo" className="login-logo" />
                        <div className='websiteLinkDiv'>  <a className='websiteLink' href="https://verifai-project.com/">Verif.ai Project Website</a>
                        </div>
                        <div class='message-container'>
                            <h1>Please log in to access this page.</h1>
                            <button onClick={handleLogin}>Log in</button>
                        </div>
                    </div>
                </div>
            );
        } 
        

    return (
        <div>
        <div className='MenuButtons'>
        <button  className='UserButton' onClick={handleMain}><div><p className='username'>HOME</p></div></button>
           
      <div className='MenuButtonSection'>  <button title="Log out" className='LogoutButton' onClick={handleLogout}> <div className="button-content">
            <img className="Logout-logo" src={logout_img}  />
           
        </div></button></div>
          

    </div>
        <div className="login-container">
            <div className="credentials-subcontainer">
            <div className='login-text'>
            <img src={logo} alt="Logo" className="cred-logo" />
            <div className='websiteLinkDivCredentials'>  <a className='websiteLinkCred' href="https://verifai-project.com/">Verif.ai Project Website</a>
            </div>
            </div>

            <div className='form-section-div'>
            <div className="login-form">
                <h1>Change Password</h1>
                <form className="formClass" onSubmit={handleChangePassword}>
                    <input className="formInput" type="password" placeholder="Old Password" onChange={e => setOldPassword(e.target.value)} />
                    <input className="formInput" type="password" placeholder="New Password" onChange={e => setNewPassword(e.target.value)} />
                    <button className="center-button" onClick={handleChangePassword}>Change Password</button>
                </form>
            
            </div>
            </div>
            </div>
        </div>
        </div>
    );
}

export default UserCredential;
