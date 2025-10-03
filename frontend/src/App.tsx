import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from'react-router-dom';
import Navbar from './components/Navbar';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import AboutPage from './pages/AboutPage';
import DashboardPage from './pages/DashboardPage';
import './App.css'

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(localStorage.getItem('isLoggedIn') === 'true');

  const handleLogin = (email: string, token: string) => {
    setIsLoggedIn(true);
    localStorage.setItem('isLoggedIn', 'true');
    localStorage.setItem('email', JSON.stringify(email));
    localStorage.setItem('token', token);
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    localStorage.removeItem('isLoggedIn');
    localStorage.removeItem('email');
    localStorage.removeItem('token');
  };

  return (
    <Router>
      <Routes>
        <Route path="/login" element={<LoginPage onLogin={handleLogin}/>}/>
        <Route path="/register" element={<RegisterPage />}/>
        <Route
          path="/about"
          element={isLoggedIn ? (<div><Navbar isLoggedIn={isLoggedIn} onLogout={handleLogout}/><AboutPage /></div>) : <Navigate to="/login" />}
        />
        <Route
          path="/"
          element={isLoggedIn ? (<div><Navbar isLoggedIn={isLoggedIn} onLogout={handleLogout}/><DashboardPage /></div>) : <Navigate to="/login" />}
        />
        <Route
          /*path="/dashboard"*/
          path="/*"
          element={isLoggedIn ? (<div><Navbar isLoggedIn={isLoggedIn} onLogout={handleLogout}/><DashboardPage /></div>) : <Navigate to="/login" />}
        />
      </Routes>
    </Router>
  )
}

export default App
