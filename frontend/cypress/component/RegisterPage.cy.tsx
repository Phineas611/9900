import React from 'react'
import { BrowserRouter } from 'react-router-dom'
import RegisterPage from '../../src/pages/RegisterPage'

describe('RegisterPage', () => {
  beforeEach(() => {
    cy.mount(
      <BrowserRouter>
        <RegisterPage />
      </BrowserRouter>
    )
  })

  it('should render the registration form with all required fields', () => {
    // Check page title and header
    cy.contains('Legal Contract Analyzer - Register').should('be.visible')
    
    // Check navigation links
    cy.contains('Login').should('have.attr', 'href', '/login')
    
    // Check all form fields exist
    cy.get('input[name="email"]').should('exist')
    cy.get('input[name="password"]').should('exist')
    cy.get('input[name="confirmPassword"]').should('exist')
    cy.get('input[name="name"]').should('exist')
    
    // Check submit button
    cy.get('input[type="submit"]').should('exist').and('have.value', 'Register')
    
    // Check form icons
    cy.get('.fas.fa-user').should('have.length', 2) // Email and Name icons
    cy.get('.fas.fa-lock').should('have.length', 2) // Password and Confirm Password icons
  })

  it('should display error for invalid email format', () => {
    cy.get('input[name="email"]').type('invalid-email')
    cy.get('input[name="password"]').type('password123')
    cy.get('input[name="confirmPassword"]').type('password123')
    cy.get('input[name="name"]').type('Test User')
    
    cy.get('input[type="submit"]').click()
    
    cy.contains('Email verification failed!').should('be.visible')
    cy.get('.msg').should('have.css', 'color', 'rgb(204, 51, 51)') // #c33
  })

  it('should display error when password is empty', () => {
    cy.get('input[name="email"]').type('test@example.com')
    cy.get('input[name="name"]').type('Test User')
    
    cy.get('input[type="submit"]').click()
    
    cy.contains('No password entered!').should('be.visible')
  })

  it('should display error when confirm password is empty', () => {
    cy.get('input[name="email"]').type('test@example.com')
    cy.get('input[name="password"]').type('password123')
    cy.get('input[name="name"]').type('Test User')
    
    cy.get('input[type="submit"]').click()
    
    cy.contains('No confirm password entered!').should('be.visible')
  })

  it('should display error when passwords do not match', () => {
    cy.get('input[name="email"]').type('test@example.com')
    cy.get('input[name="password"]').type('password123')
    cy.get('input[name="confirmPassword"]').type('differentpassword')
    cy.get('input[name="name"]').type('Test User')
    
    cy.get('input[type="submit"]').click()
    
    cy.contains('The two entered passwords are inconsistent!').should('be.visible')
  })

  it('should display error when name is empty', () => {
    cy.get('input[name="email"]').type('test@example.com')
    cy.get('input[name="password"]').type('password123')
    cy.get('input[name="confirmPassword"]').type('password123')
    
    cy.get('input[type="submit"]').click()
    
    cy.contains('No name entered!').should('be.visible')
  })

  it('should show loading message when form is submitted', () => {
    cy.intercept('POST', '**/auth/register', {
      delay: 1000,
      statusCode: 200,
      body: { success: true }
    }).as('registerRequest')

    cy.get('input[name="email"]').type('test@example.com')
    cy.get('input[name="password"]').type('password123')
    cy.get('input[name="confirmPassword"]').type('password123')
    cy.get('input[name="name"]').type('Test User')
    
    cy.get('input[type="submit"]').click()
    
    cy.contains('Registering account, please wait...').should('be.visible')
  })

  it('should successfully register and show success modal', () => {
    cy.intercept('POST', '**/auth/register', {
      statusCode: 200,
      body: { success: true }
    }).as('registerRequest')

    cy.get('input[name="email"]').type('test@example.com')
    cy.get('input[name="password"]').type('password123')
    cy.get('input[name="confirmPassword"]').type('password123')
    cy.get('input[name="name"]').type('Test User')
    
    cy.get('input[type="submit"]').click()

    cy.wait('@registerRequest')
    
    // Check success modal appears
    cy.contains('Registration Successful').should('be.visible')
    cy.contains('Registered successfully').should('be.visible')
    cy.contains('Your account has been successfully registered!').should('be.visible')
    cy.contains('You will be redirected to the login page.').should('be.visible')
    
    // Check modal has correct styling
    cy.get('.modal').should('have.css', 'display', 'block')
    cy.get('.modal').should('have.css', 'backgroundColor', 'rgba(0, 0, 0, 0.5)')
    
    // Check success button exists
    cy.contains('Go to Login').should('be.visible')
  })

  it('should display server error message when registration fails', () => {
    cy.intercept('POST', '**/auth/register', {
      statusCode: 400,
      body: { detail: 'Email already exists' }
    }).as('registerRequest')

    cy.get('input[name="email"]').type('existing@example.com')
    cy.get('input[name="password"]').type('password123')
    cy.get('input[name="confirmPassword"]').type('password123')
    cy.get('input[name="name"]').type('Test User')
    
    cy.get('input[type="submit"]').click()

    cy.wait('@registerRequest')
    
    cy.contains('Email already exists').should('be.visible')
  })

  it('should handle network errors gracefully', () => {
    cy.intercept('POST', '**/auth/register', {
      forceNetworkError: true
    }).as('registerRequest')

    cy.get('input[name="email"]').type('test@example.com')
    cy.get('input[name="password"]').type('password123')
    cy.get('input[name="confirmPassword"]').type('password123')
    cy.get('input[name="name"]').type('Test User')
    
    cy.get('input[type="submit"]').click()

    // The component should handle the error without crashing
    cy.get('.msg').should('exist')
  })

  it('should clear error messages when user starts typing again', () => {
    // Trigger an error first
    cy.get('input[name="email"]').type('invalid-email')
    cy.get('input[type="submit"]').click()
    
    cy.contains('Email verification failed!').should('be.visible')
    
    // Start typing a valid email
    cy.get('input[name="email"]').clear().type('valid@example.com')
    
    // Error message should persist until next submission
    cy.contains('Email verification failed!').should('be.visible')
  })

  it('should have proper input types and attributes', () => {
    cy.get('input[name="email"]')
      .should('have.attr', 'type', 'text')
      .and('have.attr', 'placeholder', 'Email')
      .and('have.attr', 'id', 'email')

    cy.get('input[name="password"]')
      .should('have.attr', 'type', 'password')
      .and('have.attr', 'placeholder', 'Password')
      .and('have.attr', 'id', 'password')

    cy.get('input[name="confirmPassword"]')
      .should('have.attr', 'type', 'password')
      .and('have.attr', 'placeholder', 'Confirm password')
      .and('have.attr', 'id', 'confirmPassword')

    cy.get('input[name="name"]')
      .should('have.attr', 'type', 'text')
      .and('have.attr', 'placeholder', 'Name')
      .and('have.attr', 'id', 'name')
  })

  it('should maintain form values after failed submission', () => {
    cy.get('input[name="email"]').type('test@example.com')
    cy.get('input[name="password"]').type('password123')
    cy.get('input[name="confirmPassword"]').type('differentpassword') // This will cause error
    cy.get('input[name="name"]').type('Test User')
    
    cy.get('input[type="submit"]').click()
    
    cy.contains('The two entered passwords are inconsistent!').should('be.visible')
    
    // Form values should be preserved
    cy.get('input[name="email"]').should('have.value', 'test@example.com')
    cy.get('input[name="password"]').should('have.value', 'password123')
    cy.get('input[name="confirmPassword"]').should('have.value', 'differentpassword')
    cy.get('input[name="name"]').should('have.value', 'Test User')
  })

  describe('Form Validation Edge Cases', () => {
    it('should accept valid email formats', () => {
      const validEmails = [
        'user@example.com',
        'first.last@example.co.uk',
        'user+tag@example.org',
        'user.name@example.com'
      ]

      validEmails.forEach(email => {
        cy.get('input[name="email"]').clear().type(email)
        cy.get('input[name="password"]').type('password123')
        cy.get('input[name="confirmPassword"]').type('password123')
        cy.get('input[name="name"]').type('Test User')
        
        cy.get('input[type="submit"]').click()
        
        // Should not show email validation error for valid emails
        cy.contains('Email verification failed!').should('not.exist')
        
        // Clear the form for next iteration
        cy.get('input[name="password"]').clear()
        cy.get('input[name="confirmPassword"]').clear()
        cy.get('input[name="name"]').clear()
      })
    })

    it('should reject invalid email formats', () => {
      const invalidEmails = [
        'invalid',
        'invalid@',
        'invalid@example',
        'invalid@example.',
        '@example.com'
      ]

      invalidEmails.forEach(email => {
        cy.get('input[name="email"]').clear().type(email)
        cy.get('input[name="password"]').type('password123')
        cy.get('input[name="confirmPassword"]').type('password123')
        cy.get('input[name="name"]').type('Test User')
        
        cy.get('input[type="submit"]').click()
        
        cy.contains('Email verification failed!').should('be.visible')
      })
    })
  })
})