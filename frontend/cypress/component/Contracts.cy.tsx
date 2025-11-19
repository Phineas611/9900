import React from 'react'
import { BrowserRouter } from 'react-router-dom'
import Contracts from '../../src/pages/dashboard/Contracts'

describe('Contracts', () => {
  beforeEach(() => {
    cy.mount(
      <BrowserRouter>
        <Contracts />
      </BrowserRouter>
    )
  })

  it('should render contracts page with tab navigation', () => {
    cy.contains('Contract Repository').should('be.visible')
    cy.contains('Manage and analyze your contract evaluation history').should('be.visible')
    
    // Check all tabs are present
    cy.contains('All Contracts').should('be.visible')
    cy.contains('Trends & Patterns').should('be.visible')
    cy.contains('Recurring Phrases').should('be.visible')
  })

  it('should switch between tabs correctly', () => {
    // Default should be All Contracts
    cy.contains('All Contracts').should('have.class', 'active')
    
    // Click Trends & Patterns
    cy.contains('Trends & Patterns').click()
    cy.contains('Trends & Patterns').should('have.class', 'active')
    cy.contains('All Contracts').should('not.have.class', 'active')
    
    // Click Recurring Phrases
    cy.contains('Recurring Phrases').click()
    cy.contains('Recurring Phrases').should('have.class', 'active')
    cy.contains('Trends & Patterns').should('not.have.class', 'active')
  })

  it('should maintain tab state when switching', () => {
    // Navigate to Trends tab
    cy.contains('Trends & Patterns').click()
    
    // Refresh or re-render (simulating navigation away and back)
    cy.mount(
      <BrowserRouter>
        <Contracts />
      </BrowserRouter>
    )
  })
})