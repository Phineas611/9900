import React from 'react'
import { BrowserRouter } from 'react-router-dom'
import Reports from '../../src/pages/dashboard/Reports'

describe('Reports', () => {
  beforeEach(() => {
    // Mock reports data
    cy.intercept('GET', '**/reports/data', {
      statusCode: 200,
      body: {
        stats: {
          totalContracts: 150,
          ambiguousSentences: 450,
          ambiguityRate: 15.5,
          avgQualityScore: 0.85
        },
        qualityMetrics: [
          { month: 'Jan', clarity: 8.2, completeness: 7.8, accuracy: 8.5, consistency: 8.0 }
        ],
        ambiguityTrends: [
          { month: 'Jan', ambiguityRate: 16.2, targetRate: 15.0 }
        ],
        contractAnalysis: [
          { name: 'Contract A', totalSentences: 100, ambiguousSentences: 18, percentage: 18.0 }
        ]
      }
    }).as('getReportsData')

    cy.mount(
      <BrowserRouter>
        <Reports />
      </BrowserRouter>
    )
  })

  it('should render reports page with charts', () => {
    cy.contains('Reports & Analytics').should('be.visible')
    cy.contains('Visualize contract analysis trends and export detailed reports').should('be.visible')
    
    cy.contains('Export Report').should('be.visible')
  })

  it('should load and display report data', () => {
    cy.wait('@getReportsData')
    
    cy.contains('150').should('be.visible') // totalContracts
    cy.contains('450').should('be.visible') // ambiguousSentences
    cy.contains('15.5%').should('be.visible') // ambiguityRate
  })

  it('should open export modal when export button is clicked', () => {
    cy.contains('Export Report').click()
    cy.contains('Export Analysis Report').should('be.visible')
    cy.contains('Configure your report export settings').should('be.visible')
  })

  it('should close export modal when cancel is clicked', () => {
    cy.contains('Export Report').click()
    cy.contains('Cancel').click()
    cy.contains('Export Analysis Report').should('not.exist')
  })

  it('should display charts when data is loaded', () => {
    cy.wait('@getReportsData')
    
    cy.contains('Model Explanation Quality').should('be.visible')
    cy.contains('Ambiguity Rate Trend').should('be.visible')
    cy.contains('Per-Contract Analysis').should('be.visible')
  })
})