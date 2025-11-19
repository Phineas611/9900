import React from 'react'
import { BrowserRouter } from 'react-router-dom'
import DashboardMain from '../../src/pages/dashboard/DashboardMain'

describe('DashboardMain', () => {
  beforeEach(() => {
    // Mock successful API responses
    cy.intercept('GET', '**/analytics/kpi', {
      statusCode: 200,
      body: {
        total_contracts: 150,
        growth_percentage: 12,
        total_sentences: 450,
        certificates_change_pct: 8,
        avg_explanation_clarity: 0.85,
        score_change: 0.05,
        avg_analysis_time_sec: 180,
        time_change_pct: -15
      }
    }).as('getStats')

    cy.intercept('GET', '**/uploads/recent*', {
      statusCode: 200,
      body: [
        {
          contract_id: '1',
          file_name: 'contract1.pdf',
          file_type: 'PDF',
          uploaded_at: '2024-01-15',
          status: 'completed',
          total_sentences: 25
        }
      ]
    }).as('getUploads')

    cy.intercept('GET', '**/activity/recent*', {
      statusCode: 200,
      body: [
        {
          id: '1',
          event_type: 'Analysis Complete',
          title: 'Contract processed',
          message: 'contract1.pdf analysis completed',
          created_at: '2024-01-15T10:30:00Z'
        }
      ]
    }).as('getActivities')

    cy.mount(
      <BrowserRouter>
        <DashboardMain />
      </BrowserRouter>
    )
  })

  it('should render dashboard with main sections', () => {
    cy.contains('Dashboard').should('be.visible')
    cy.contains('Overview of your contract analysis activity and insights').should('be.visible')
    
    // Check main sections exist
    cy.contains('Recent Uploads').should('be.visible')
    cy.contains('Quick Start').should('be.visible')
    cy.contains('Recent Activity').should('be.visible')
  })

  it('should display statistics cards with data', () => {
    cy.wait('@getStats')
    
    cy.contains('Analyzed Contracts').should('be.visible')
    cy.contains('150').should('be.visible') // total_contracts
    cy.contains('Ambiguous Sentences').should('be.visible')
    cy.contains('450').should('be.visible') // total_sentences
    cy.contains('Clarity Score').should('be.visible')
    cy.contains('0.85/1').should('be.visible') // avg_explanation_clarity
  })

  it('should navigate to upload page when upload button is clicked', () => {
    cy.contains('Upload New Contract').click()
    cy.url().should('include', '/upload')
  })

  it('should navigate to sentence analysis when view button is clicked', () => {
    cy.wait('@getUploads')
    
    cy.get('.action-btn-dashboard-main').first().click() // First action button (eye icon)
    cy.url().should('include', '/sentence_analysis')
  })
})