import { BrowserRouter } from 'react-router-dom'
import LoginPage from '../../src/pages/LoginPage'

describe('LoginPage', () => {
  beforeEach(() => {
    cy.mount(
      <BrowserRouter>
        <LoginPage onLogin={cy.stub().as('onLogin')} />
      </BrowserRouter>
    )
  })

  it('should render login form with all required elements', () => {
    cy.contains('Legal Contract Analyzer - Login')
    cy.get('input[name="email"]').should('exist')
    cy.get('input[name="password"]').should('exist')
    cy.get('input[type="submit"]').should('exist')
    cy.contains('Register').should('have.attr', 'href', '/register')
  })

  it('should display error message for invalid email format', () => {
    cy.get('input[name="email"]').type('invalid-email')
    cy.get('input[type="submit"]').click()
    cy.contains('Email verification failed!').should('be.visible')
  })

  it('should display error message when password is empty', () => {
    cy.get('input[name="email"]').type('test@example.com')
    cy.get('input[type="submit"]').click()
    cy.contains('No password entered!').should('be.visible')
  })

  it('should successfully submit form with valid credentials', () => {
    const mockOnLogin = cy.stub().as('onLogin')
    
    // Re-mount with the stub
    cy.mount(
      <BrowserRouter>
        <LoginPage onLogin={mockOnLogin} />
      </BrowserRouter>
    )

    cy.intercept('POST', '**/auth/login', {
      statusCode: 200,
      body: { token: 'fake-token', name: 'Test User' }
    }).as('loginRequest')

    cy.get('input[name="email"]').type('test@example.com')
    cy.get('input[name="password"]').type('password123')
    cy.get('input[type="submit"]').click()

    cy.wait('@loginRequest')
    cy.get('@onLogin').should('have.been.calledWith', 'test@example.com', 'fake-token', 'Test User')
  })

  it('should display server error message on login failure', () => {
    cy.intercept('POST', '**/auth/login', {
      statusCode: 401,
      body: { detail: 'Invalid credentials' }
    }).as('loginRequest')

    cy.get('input[name="email"]').type('test@example.com')
    cy.get('input[name="password"]').type('wrongpassword')
    cy.get('input[type="submit"]').click()

    cy.wait('@loginRequest')
    cy.contains('Invalid credentials').should('be.visible')
  })
})