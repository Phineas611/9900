interface NavbarProps {
  isLoggedIn: boolean;
  onLogout: () => void;
}

const Navbar = ({ isLoggedIn, onLogout }: NavbarProps) => {
  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-dark">
      <div className="container">
        <a className="navbar-brand" href="/dashboard" style={{ fontSize: '2rem', paddingRight: '30px' }}>
          <span style={{ color: '#0c0', fontSize: '2rem' }}>L</span>egal<span style={{ color: '#0c0', fontSize: '2rem' }}>C</span>ontract<span style={{ color: '#0c0', fontSize: '2rem' }}>A</span>nalyzer
        </a>
        <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav"
          aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
          <span className="navbar-toggler-icon"></span>
        </button>
        <div className="collapse navbar-collapse" id="navbarNav">
          <ul className="navbar-nav">
            <li className="nav-item">
              <a className="nav-link" href="/dashboard_main">Dashboard</a>
            </li>

            <li className="nav-item">
              <a className="nav-link" href="/about">About</a>
            </li>

            {!isLoggedIn && (
              <li className="nav-item">
                <a className="nav-link" href="/login">Login</a>
              </li>
            )}
            {isLoggedIn && (
              <li className="nav-item">
                <a className="nav-link" href="#" onClick={onLogout}>Logout</a>
              </li>
            )}
          </ul>
        </div>
      </div>
      <style>{`
          .navbar-nav .nav-item {
          padding: 0.5rem 1rem;
        `}</style>
    </nav>
  );
}

export default Navbar;  