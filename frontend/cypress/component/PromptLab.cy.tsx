import React from 'react'
import { BrowserRouter } from 'react-router-dom'
import PromptLab from '../../src/pages/dashboard/PromptLab'

describe('PromptLab', () => {
  beforeEach(() => {
    // Mock API responses
    cy.intercept('GET', '**/models', {
      statusCode: 200,
      body: {
        current: { id: 'modelA', hf_name: 'model-a' },
        available: [
          { id: 'modelA', name: 'Model A' },
          { id: 'modelB', name: 'Model B' }
        ]
      }
    }).as('getModels')

    cy.intercept('GET', '**/prompts', {
      statusCode: 200,
      body: {
        prompts: ['amb-basic', 'amb-advanced', 'custom-prompt']
      }
    }).as('getPrompts')

    cy.mount(
      <BrowserRouter>
        <PromptLab />
      </BrowserRouter>
    )
  })

  it('should render prompt lab interface', () => {
    cy.contains('Prompt Lab').should('be.visible')
    cy.contains('Test and evaluate different prompts for contract analysis').should('be.visible')
    
    // Check all sections are present
    cy.contains('Models & Prompts').should('be.visible')
    cy.contains('Single Sentence Analysis').should('be.visible')
    cy.contains('Batch Analysis').should('be.visible')
    cy.contains('File Upload Analysis').should('be.visible')
  })

  it('should load models and prompts on mount', () => {
    cy.wait('@getModels')
    cy.wait('@getPrompts')

    cy.get('.config-select').first().should('contain', 'Model A')
    cy.get('.config-select').eq(1).should('contain', 'amb-basic')
  })

  it('should handle file drag and drop', () => {
    const testFile = new File(['test content'], 'test.csv', { type: 'text/csv' })
    
    cy.get('.file-drop-zone').selectFile({
      contents: testFile,
      fileName: 'test.csv'
    }, { action: 'drag-drop' })

    cy.contains('test.csv').should('be.visible')
  })
})