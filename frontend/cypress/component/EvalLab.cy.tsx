import React from 'react'
import { BrowserRouter } from 'react-router-dom'
import EvalLab from '../../src/pages/dashboard/EvalLab'

describe('EvalLab', () => {
  beforeEach(() => {
    // Mock configuration
    cy.intercept('GET', '**/config', {
      statusCode: 200,
      body: {
        judges: [
          { id: 'judge-mini-a', label: 'judge-a-llama-3.1-8b-instant' },
          { id: 'judge-mini-b', label: 'judge-b-prometheus-7b-v2.0' }
        ],
        default_rubrics: ['grammar', 'clarity']
      }
    }).as('getConfig')

    cy.mount(
      <BrowserRouter>
        <EvalLab />
      </BrowserRouter>
    )
  })

  it('should render evaluation lab interface', () => {
    cy.contains('Evaluation Lab').should('be.visible')
    cy.contains('Configuration').should('be.visible')
    cy.contains('Upload & Run').should('be.visible')
    cy.contains('Status & Summary').should('be.visible')
    cy.contains('Records & Export').should('be.visible')
  })

  it('should load configuration on mount', () => {
    cy.wait('@getConfig')
    
    cy.contains('judge-a-llama-3.1-8b-instant').should('be.visible')
    cy.contains('judge-b-prometheus-7b-v2.0').should('be.visible')
  })

  it('should allow judge selection', () => {
    cy.wait('@getConfig')
    
    // All judges should be selected by default
    cy.get('input[type="checkbox"]').should('be.checked')
    
    // Unselect one judge
    cy.get('input[type="checkbox"]').first().uncheck()
    cy.get('input[type="checkbox"]').first().should('not.be.checked')
  })
})