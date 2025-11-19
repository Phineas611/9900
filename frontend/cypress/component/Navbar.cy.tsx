import { BrowserRouter } from 'react-router-dom'
import Navbar from '../../src/components/Navbar'

describe('Navbar', () => {
  it('should render login link for unauthenticated users', () => {
    const mockOnLogout = cy.stub().as('onLogout')
    
    cy.mount(
      <BrowserRouter>
        <Navbar isLoggedIn={false} onLogout={mockOnLogout} />
      </BrowserRouter>
    )
    
    cy.contains('LegalContractAnalyzer')
    cy.contains('Login').should('exist')
    cy.contains('Dashboard').should('exist')
    cy.contains('About').should('exist')
  })

  it('should render user menu for authenticated users', () => {
    const mockOnLogout = cy.stub().as('onLogout')
    
    cy.mount(
      <BrowserRouter>
        <Navbar 
          isLoggedIn={true} 
          onLogout={mockOnLogout} 
          userName="John Doe" 
        />
      </BrowserRouter>
    )

    cy.contains('John Doe').should('exist')
    cy.contains('Login').should('not.exist')
  })

  it('should toggle search bar visibility', () => {
    const mockOnLogout = cy.stub().as('onLogout')
    
    cy.mount(
      <BrowserRouter>
        <Navbar isLoggedIn={false} onLogout={mockOnLogout} />
      </BrowserRouter>
    )
    
    // Use more specific selector for search button
    cy.get('.search-btn').first().click()
    cy.get('.search-input').should('be.visible')
    
    // Click again to collapse
    cy.get('.search-btn').first().click()
    cy.get('.search-input').should('not.be.visible')
  })

  it('should call logout callback when logout is clicked', () => {
    const mockOnLogout = cy.stub().as('onLogout')
    
    cy.mount(
      <BrowserRouter>
        <Navbar 
          isLoggedIn={true} 
          onLogout={mockOnLogout} 
          userName="John Doe" 
        />
      </BrowserRouter>
    )

    // Open user dropdown menu - use specific selector
    cy.get('.nav-link.dropdown-toggle').click()
    cy.contains('Logout').click()

    cy.get('@onLogout').should('have.been.calledOnce')
  })

  it('should have working navigation links', () => {
    const mockOnLogout = cy.stub().as('onLogout')
    
    cy.mount(
      <BrowserRouter>
        <Navbar isLoggedIn={false} onLogout={mockOnLogout} />
      </BrowserRouter>
    )

    // Test Dashboard link
    cy.get('a[href="/dashboard_main"]').should('exist')
    
    // Test About link
    cy.get('a[href="/about"]').should('exist')
    
    // Test Login link
    cy.get('a[href="/login"]').should('exist')
  })

  it('should display search functionality correctly', () => {
    const mockOnLogout = cy.stub().as('onLogout')
    
    cy.mount(
      <BrowserRouter>
        <Navbar isLoggedIn={false} onLogout={mockOnLogout} />
      </BrowserRouter>
    )

    // Test mobile search
    cy.get('.search-container').first().within(() => {
      cy.get('.search-btn').click()
      cy.get('.search-input').should('be.visible').type('test search')
      cy.get('.search-input').should('have.value', 'test search')
    })

    // Test desktop search
    cy.get('.d-none.d-lg-block').within(() => {
      cy.get('.search-btn').click()
      cy.get('.search-input').should('be.visible')
    })
  })
})