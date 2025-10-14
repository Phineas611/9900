import { useState, useRef, useEffect } from 'react';

interface NavbarProps {
  isLoggedIn: boolean;
  onLogout: () => void;
  userName?: string;
}

const Navbar = ({ isLoggedIn, onLogout, userName }: NavbarProps) => {
  const [isSearchActive, setIsSearchActive] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [searchValue, setSearchValue] = useState('');
  const searchContainerMobileRef = useRef<HTMLDivElement>(null);
  const searchContainerDesktopRef = useRef<HTMLDivElement>(null);
  const searchInputMobileRef = useRef<HTMLInputElement>(null);
  const searchInputDesktopRef = useRef<HTMLInputElement>(null);
  const userMenuRef = useRef<HTMLLIElement>(null);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchValue(e.target.value);
  };

  // Handle search bar expand/collapse
  const toggleSearch = () => {
    setIsSearchActive(!isSearchActive);
    if (!isSearchActive) {
      setTimeout(() => {
        if (window.innerWidth < 992) {
          searchInputMobileRef.current?.focus();
        } else {
          searchInputDesktopRef.current?.focus();
        }
      }, 400);
    } else {
      if (searchValue && searchValue.length > 0) {
        handleSearch(searchValue);
      }
    }
  };

  // Handle search
  const handleSearch = (keyword: string) => {
    console.log('Searching for:', keyword);
    // Replace with actual search logic
  };

  // Handle keyboard events
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      if (searchValue && searchValue.length > 0) {
        handleSearch(searchValue);
      }
      setSearchValue('');
      setIsSearchActive(false);
    } else if (e.key === 'Escape') {
      setIsSearchActive(false);
    }
  };

  const handleInputClick = (e: React.MouseEvent) => {
    e.stopPropagation();
  };

  // Click outside to close search bar and user menu
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;

      const isOutsideMobile = searchContainerMobileRef.current &&
        !searchContainerMobileRef.current.contains(target);

      const isOutsideDesktop = searchContainerDesktopRef.current &&
        !searchContainerDesktopRef.current.contains(target);

      if (isOutsideMobile && isOutsideDesktop && isSearchActive) {
        setIsSearchActive(false);
      }

      // Close user menu
      if (userMenuRef.current &&
        !userMenuRef.current.contains(target) &&
        isUserMenuOpen) {
        setIsUserMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isSearchActive, isUserMenuOpen]);

  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-dark">
      <div className="container-fluid">
        {/* Brand and mobile search */}
        <div className="d-flex align-items-center">
          <a className="navbar-brand" href="/dashboard" style={{ fontSize: '1.5rem', paddingRight: '30px' }}>
            <span style={{ color: '#0c0', fontSize: '1.5rem' }}>L</span>egal
            <span style={{ color: '#0c0', fontSize: '1.5rem' }}>C</span>ontract
            <span style={{ color: '#0c0', fontSize: '1.5rem' }}>A</span>nalyzer
          </a>
        </div>

        {/* Mobile search bar - positioned next to logo */}
        <div className="d-lg-none ms-3">
          <div
            ref={searchContainerMobileRef}
            className={`search-container ${isSearchActive ? 'active' : ''}`}
            style={{ marginLeft: '1rem' }}
          >
            <input
              ref={searchInputMobileRef}
              type="text"
              className="search-input"
              placeholder="Search..."
              value={searchValue}
              onChange={handleSearchChange}
              onKeyDown={handleKeyPress}
              onClick={handleInputClick}
            />
            <button className="search-btn" onClick={toggleSearch}>
              <i className="fas fa-search"></i>
            </button>
          </div>
        </div>

        {/* Toggle button */}
        <button
          className="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#navbarNav"
          aria-controls="navbarNav"
          aria-expanded="false"
          aria-label="Toggle navigation"
        >
          <span className="navbar-toggler-icon"></span>
        </button>

        {/* Collapsible content */}
        <div className="collapse navbar-collapse" id="navbarNav">
          {/* Navigation links - left aligned on mobile */}
          <ul className="navbar-nav me-auto text-lg-start">
            <li className="nav-item">
              <a className="nav-link" href="/dashboard_main">Dashboard</a>
            </li>
            <li className="nav-item">
              <a className="nav-link" href="/about">About</a>
            </li>
          </ul>

          {/* Right side items */}
          <ul className="navbar-nav" style={{ margin: 0 }}>
            {/* Desktop search bar */}
            <li className="nav-item d-none d-lg-block" style={{ marginLeft: '2rem', paddingRight: '0px' }}>
              <div
                ref={searchContainerDesktopRef}
                className={`search-container ${isSearchActive ? 'active' : ''}`}
              >
                <input
                  ref={searchInputDesktopRef}
                  type="text"
                  className="search-input"
                  placeholder="Search..."
                  value={searchValue}
                  onChange={handleSearchChange}
                  onKeyDown={handleKeyPress}
                  onClick={handleInputClick}
                />
                <button className="search-btn" onClick={toggleSearch}>
                  <i className="fas fa-search"></i>
                </button>
              </div>
            </li>

            {/* User menu */}
            {!isLoggedIn ? (
              <li className="nav-item">
                <a className="nav-link" href="/login">Login</a>
              </li>
            ) : (
              <li
                ref={userMenuRef}
                className="nav-item dropdown"
              >
                <a
                  className="nav-link dropdown-toggle d-flex align-items-center"
                  href="#"
                  role="button"
                  onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                  aria-expanded={isUserMenuOpen}
                >
                  <i className="fas fa-user-circle me-2" style={{ fontSize: '1.2rem' }}></i>
                  <span>{userName || 'User'}</span>
                </a>
                <ul className={`dropdown-menu dropdown-menu-end ${isUserMenuOpen ? 'show' : ''}`}>
                  <li><a className="dropdown-item" href="/profile">Profile</a></li>
                  <li><a className="dropdown-item" href="/settings">Settings</a></li>
                  <li><hr className="dropdown-divider" /></li>
                  <li>
                    <a className="dropdown-item" href="#" onClick={onLogout}>
                      Logout
                    </a>
                  </li>
                </ul>
              </li>
            )}
          </ul>
        </div>
      </div>

      <style>{`
        .dl, ol, ul {
          margin-top: 0;
        }

        .navbar-nav .nav-item {
          padding: 0.5rem 1rem;
        }
        
        /* Mobile menu text alignment */
        @media (max-width: 991.98px) {
          .navbar-nav.me-auto {
            text-align: left !important;
            width: 100%;
          }
          .navbar-nav.me-auto .nav-item {
            text-align: left;
          }
        }
        
        /* Search Styles */
        .search-container {
          position: relative;
          height: 40px;
          display: flex;
          align-items: center;
          color: #000;
        }

        .search-btn {
          position: absolute;
          right: 0;
          color: #000;
          background: transparent;
          border: none;
          width: 40px;
          height: 40px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.3s ease;
          z-index: 3;
        }

        .search-btn i {
          color: #fff;
          font-size: 14px;
          transition: transform 0.3s ease;
        }

        .search-container.active .search-btn i {
          color: #333;
        }

        .search-input {
          position: absolute;
          right: 0;
          height: 40px;
          border: 1px solid #ccc;
          background: #fff;
          padding: 0 45px 0 20px;
          font-size: 16px;
          outline: none;
          transition: all 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
          width: 40px;
          opacity: 0;
          pointer-events: none;
          border-radius: 25px;
          z-index: 2;
        }

        .search-container.active .search-input {
          width: 300px;
          opacity: 1;
          pointer-events: auto;
        }

        .search-input:focus {
          border-color: #0c0;
        }

        /* Mobile search adjustments */
        @media (max-width: 991.98px) {
          .search-container.active .search-input {
            width: 200px;
          }
        }

        /* User dropdown styles */
        .dropdown-toggle::after {
          margin-left: 0.5em;
        }

        .nav-link.dropdown-toggle {
          color: rgba(255, 255, 255, 0.75) !important;
        }

        .nav-link.dropdown-toggle:hover {
          color: rgba(255, 255, 255, 0.9) !important;
        }

        /* Fix dropdown menu positioning */
        .navbar-nav .dropdown-menu {
          position: absolute;
          right: 0;
          left: auto;
          z-index: 1111;
        }
        
        .dropdown-menu {
          max-width: 200px;
          min-width: 150px;
        }
        
        .dropdown-item {
          width: auto;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        @media (max-width: 992px) {
          .navbar-nav .dropdown-menu {
            position: absolute;
            left: 0;
          }
          .dropdown-menu {
            max-width: 100%;
            min-width: 80%;
          }
        }
      `}</style>
    </nav>
  );
}

export default Navbar;