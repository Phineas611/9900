import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './LoginPage.css';

interface LoginPageProps {
  onLogin: (email: string, token: string) => void;
}

// Login component page
const LoginPage = ({ onLogin }: LoginPageProps) => {

  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [msg, setMsg] = useState('');
  
  // Verify the correctness of the email address
  const validateEmail = (email: string) => {
    const emailRegex = /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i;
    return emailRegex.test(email);
  };

  // Login to submit business
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setMsg('Please wait while logging in...');

    if (!validateEmail(email)) {
      setMsg('Email verification failed!');
      return;
    }

    if (password === '') {
      setMsg('No password entered!');
      return;
    }

    // test
    onLogin(email, '111');
    navigate('/dashboard');
    return;

    fetch(`/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    })
      .then(response => {
        if (!response.ok) {
          return response.json();
        }
        return response.json();
      })
      .then(data => {
        if (!data.error) {
          // After successful login, the callback is written to localStorage and enters the dashboard page
          onLogin(email, data.token);
          navigate('/dashboard');
        } else {
          setMsg(data.error);
        }
      })
      .catch(error => {
        console.error('Error:', error);
      });
  };

  return (
    <div className="login">
      <h1>Legal Contract Analyzer - Login</h1>
      <div className="links">
        <a href="#">Login</a>
        <a href="/register">Register</a>
      </div>
      <form onSubmit={handleSubmit}>
        <div className="form-row">
          <label htmlFor="email">
            <i className="fas fa-user"></i>
          </label>
          <input 
            type="text" 
            name="email" 
            placeholder="Email" 
            id="email" 
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div className="form-row">
          <label htmlFor="password">
            <i className="fas fa-lock"></i>
          </label>
          <input 
            type="password" 
            name="password" 
            placeholder="Password" 
            id="password" 
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <div className="msg" style={{color: '#c33'}}>{msg}</div>
        <input type="submit" value="Login" />
      </form>
    </div>
  );
};

export default LoginPage;