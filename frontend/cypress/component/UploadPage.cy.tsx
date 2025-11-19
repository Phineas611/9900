import { BrowserRouter } from 'react-router-dom'
import UploadPage from '../../src/pages/Dashboard/UploadPage'

describe('UploadPage', () => {
  beforeEach(() => {
    cy.mount(
      <BrowserRouter>
        <UploadPage />
      </BrowserRouter>
    )
  })

  it('should render upload page with all elements', () => {
    cy.contains('Upload Contract')
    cy.contains('Drag and drop your files here')
    cy.contains('Browse Files').should('exist')
  })

  it('should select files via drag and drop', () => {
    const fileName = 'test-contract.pdf'
    
    cy.get('.drop-zone').selectFile({
      contents: Cypress.Buffer.from('fake pdf content'),
      fileName: fileName,
      mimeType: 'application/pdf',
    }, { action: 'drag-drop' })

    cy.contains(fileName).should('be.visible')
  })
})