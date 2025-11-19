import React from 'react'
import { BrowserRouter } from 'react-router-dom'
import SentenceAnalysis from '../../src/pages/dashboard/SentenceAnalysis'

describe('SentenceAnalysis', () => {
  const mockContractId = '123'

  beforeEach(() => {
    // Set up search params mock
    cy.stub(URLSearchParams.prototype, 'get')
      .withArgs('id')
      .returns(mockContractId)

    // Mock the import API call
    cy.intercept('POST', `**/contracts/${mockContractId}/sentences/import`, {
      statusCode: 200,
      body: {
        contract_id: 1,
        job_id: 'job-123',
        imported_count: 10,
        csv_path: '/path/to/csv'
      }
    }).as('importSentences')

    // Mock the extract API call
    cy.intercept('GET', '**/extract/job-123', {
      statusCode: 200,
      body: {
        sentences: [
          {
            docId: 'doc-1',
            docName: 'Contract A',
            page: 1,
            sentenceId: 'sent-1',
            text: 'This is an ambiguous sentence that needs review.',
            label: 'AMBIGUOUS',
            score: 0.76,
            rationale: 'The language is vague and could be interpreted multiple ways.'
          },
          {
            docId: 'doc-1',
            docName: 'Contract A',
            page: 2,
            sentenceId: 'sent-2',
            text: 'This is a clear and unambiguous statement.',
            label: 'UNAMBIGUOUS',
            score: 0.92,
            rationale: 'The meaning is specific and clear.'
          }
        ]
      }
    }).as('getSentences')

    cy.mount(
      <BrowserRouter>
        <SentenceAnalysis />
      </BrowserRouter>
    )
  })

  it('should render sentence analysis page', () => {
    cy.contains('Sentence Analysis').should('be.visible')
    cy.contains('Review ambiguous sentences and their explanations').should('be.visible')
  })

  it('should load and display sentences after API calls', () => {
    // Wait for both API calls to complete
    cy.wait('@importSentences').then((interception) => {
      expect(interception.response?.statusCode).to.equal(200)
    })

    cy.wait('@getSentences').then((interception) => {
      expect(interception.response?.statusCode).to.equal(200)
    })

    // Verify sentences are displayed
    cy.contains('This is an ambiguous sentence that needs review.').should('be.visible')
    cy.contains('This is a clear and unambiguous statement.').should('be.visible')
    cy.contains('AMBIGUOUS').should('be.visible')
    cy.contains('UNAMBIGUOUS').should('be.visible')
  })

  it('should show loading state initially', () => {
    cy.contains('Loading sentence analysis...').should('be.visible')
    
    // Wait for data to load and loading to disappear
    cy.wait('@importSentences')
    cy.wait('@getSentences')
    cy.contains('Loading sentence analysis...').should('not.exist')
  })

  it('should expand and collapse sentence details when eye button is clicked', () => {
    // Wait for data to load
    cy.wait('@importSentences')
    cy.wait('@getSentences')

    // Click first eye button to expand details
    cy.get('.eye-btn').first().click()
    
    // Should show detailed information
    cy.contains('Original Sentence').should('be.visible')
    cy.contains('Explanation').should('be.visible')
    cy.contains('Classification Details').should('be.visible')
    
    // Verify the content
    cy.contains('This is an ambiguous sentence that needs review.').should('be.visible')
    cy.contains('The language is vague and could be interpreted multiple ways.').should('be.visible')
    
    // Click again to collapse
    cy.get('.eye-btn').first().click()
    cy.contains('Original Sentence').should('not.exist')
  })

  it('should filter sentences by type', () => {
    cy.wait('@importSentences')
    cy.wait('@getSentences')

    // Filter to show only ambiguous sentences
    cy.get('.filter-select').select('ambiguous')
    
    // Should only show ambiguous sentences
    cy.contains('AMBIGUOUS').should('be.visible')
    cy.contains('UNAMBIGUOUS').should('not.exist')
  })

  it('should display statistics cards', () => {
    cy.wait('@importSentences')
    cy.wait('@getSentences')

    // Check that stats are displayed
    cy.contains('Total Sentences').should('be.visible')
    cy.contains('Ambiguous').should('be.visible')
    cy.contains('Unambiguous').should('be.visible')
    
    // Should show correct counts (2 total, 1 ambiguous, 1 unambiguous)
    cy.contains('2').should('be.visible') // Total sentences
  })

  it('should handle pagination when many sentences exist', () => {
    // Mock more sentences to test pagination
    cy.intercept('GET', '**/extract/job-123', {
      statusCode: 200,
      body: {
        sentences: Array.from({ length: 15 }, (_, i) => ({
          docId: 'doc-1',
          docName: `Contract ${i + 1}`,
          page: i + 1,
          sentenceId: `sent-${i + 1}`,
          text: `Sentence number ${i + 1}`,
          label: i % 2 === 0 ? 'AMBIGUOUS' : 'UNAMBIGUOUS',
          score: i % 2 === 0 ? 0.7 : 0.9,
          rationale: `Rationale for sentence ${i + 1}`
        }))
      }
    }).as('getManySentences')

    // Remount to trigger the new mock
    cy.mount(
      <BrowserRouter>
        <SentenceAnalysis />
      </BrowserRouter>
    )

    cy.wait('@importSentences')
    cy.wait('@getManySentences')

    // Should show pagination controls
    cy.contains('Previous').should('be.visible')
    cy.contains('Next').should('be.visible')
    
    // Should be able to navigate to next page
    cy.contains('Next').click()
    cy.contains('Page 2').should('be.visible')
  })

  it('should export CSV when export button is clicked', () => {
    cy.wait('@importSentences')
    cy.wait('@getSentences')

    // Stub the window.URL.createObjectURL and revokeObjectURL
    cy.window().then((win) => {
      cy.stub(win.URL, 'createObjectURL').returns('blob:fake-url')
      cy.stub(win.URL, 'revokeObjectURL')
    })

    // Click export button
    cy.contains('Export CSV').click()
    
    // Should create a download (we can't actually download in tests, but we can verify the function is called)
    cy.window().its('URL.createObjectURL').should('have.been.called')
  })

  it('should display error state when API fails', () => {
    // Mock API failure
    cy.intercept('POST', `**/contracts/${mockContractId}/sentences/import`, {
      statusCode: 500,
      body: { error: 'Internal server error' }
    }).as('importError')

    cy.mount(
      <BrowserRouter>
        <SentenceAnalysis />
      </BrowserRouter>
    )

    cy.wait('@importError')
    cy.contains('Error Loading Sentence Analysis').should('be.visible')
    cy.contains('Failed to import sentences').should('be.visible')
    cy.contains('Retry').should('be.visible')
  })

  it('should retry loading when retry button is clicked', () => {
    // Mock initial failure then success
    let callCount = 0
    cy.intercept('POST', `**/contracts/${mockContractId}/sentences/import`, (req) => {
      callCount++
      if (callCount === 1) {
        req.reply({ statusCode: 500, body: { error: 'First attempt failed' } })
      } else {
        req.reply({
          statusCode: 200,
          body: {
            contract_id: 1,
            job_id: 'job-123',
            imported_count: 10,
            csv_path: '/path/to/csv'
          }
        })
      }
    }).as('importRetry')

    cy.intercept('GET', '**/extract/job-123', {
      statusCode: 200,
      body: { sentences: [] }
    }).as('getEmptySentences')

    cy.mount(
      <BrowserRouter>
        <SentenceAnalysis />
      </BrowserRouter>
    )

    cy.wait('@importRetry')
    cy.contains('Retry').click()
    cy.wait('@importRetry')
    cy.wait('@getEmptySentences')
    
    // Should load successfully on retry
    cy.contains('Error Loading Sentence Analysis').should('not.exist')
  })
})