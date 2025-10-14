import { useState} from 'react';
import { useNavigate } from 'react-router-dom';
import './RegisterPage.css';

// Register component page
const RegisterPage = () => {

  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [name, setName] = useState('');
  const [msg, setMsg] = useState('');

  // Verify the correctness of the email address
  const validateEmail = (email: string) => {
    const emailRegex = /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i;
    return emailRegex.test(email);
  };

  // Register to submit business
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setMsg('Registering account, please wait...');

    if (!validateEmail(email)) {
      setMsg('Email verification failed!');
      return;
    }

    if (password === '') {
      setMsg('No password entered!');
      return;
    }

    if (confirmPassword === '') {
      setMsg('No confirm password entered!');
      return;
    }

    if (password !== confirmPassword) {
      setMsg('The two entered passwords are inconsistent!');
      return;
    }

    if (name.length < 1) {
      setMsg('No name entered!');
      return;
    }

    fetch(`/api/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password, name }),
    })
      .then(response => {
        if (!response.ok) {
          return response.json();
        }
        return response.json();
      })
      .then(data => {
        if (!data.error) {
          if (window.confirm("Successfully registered")) {
            // Callback redirects to login page
            navigate('/login');
          }
        } else {
          setMsg(data.error);
        }
      })
      .catch(error => {
        console.error('Error:', error);
      });
  };

  return (
    <>
      <div className="register">
        <h1>Legal Contract Analyzer - Register</h1>
        <div className="links">
          <a href="/login">Login</a>
          <a href="#">Register</a>
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
          <div className="form-row">
            <label htmlFor="confirmPassword">
              <i className="fas fa-lock"></i>
            </label>
            <input
              type="password"
              name="confirmPassword"
              placeholder="Confirm password"
              id="confirmPassword"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
            />
          </div>
          <div className="form-row">
            <label htmlFor="name">
              <i className="fas fa-user"></i>
            </label>
            <input
              type="text"
              name="name"
              placeholder="Name"
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div className="msg" style={{ color: '#c33' }}>{msg}</div>
          <input type="submit" value="Register" />
        </form>

      </div>
    </>
  );
};

export default RegisterPage;