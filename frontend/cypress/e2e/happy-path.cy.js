describe('LegalContractAnalyzer Happy Path - Complete User Journey', () => {
  const testUser = { email: 'test@test.com', name: 'ttt', password: '123456' };
  
  const ensureLoggedIn = (user) => {
    cy.visit('http://localhost:5173')

    // Check if you have logged in
    cy.get('body').then(($body) => {
      if ($body.text().includes(user.email)) {
        cy.log(`User ${user.email} is already logged in`)
        return
      }

      // No login, try logging in
      cy.contains('Login').click()
      cy.get('input[name="email"]').type(user.email)
      cy.get('input[name="password"]').type(user.password)
      cy.wait(1000)
      cy.contains('input', 'Login').click()

      // If login fails, register
      cy.wait(3000)
      cy.url().then((url) => {
        if (url.includes('/login')) {
          cy.log(`Login failed for ${user.email}, trying to register...`)
          cy.contains("Register").click()
          cy.get('input[name="email"]').type(user.email)
          cy.get('input[name="name"]').type(user.name)
          cy.get('input[name="password"]').type(user.password)
          cy.get('input[name="confirmPassword"]').type(user.password)
          cy.contains('input', 'Register').click()
          cy.wait(3000)
          cy.contains("Go to Login").click()
          cy.get('input[name="email"]').type(user.email)
          cy.get('input[name="password"]').type(user.password)
          cy.wait(1000)
          cy.contains('input', 'Login').click()
        }
      })

      // Confirm successful login
      cy.url({ timeout: 10000 }).should('include', '/dashboard_main')
      cy.contains(user.name, { timeout: 10000 }).should('be.visible')
    })
  }

  beforeEach(() => { cy.visit('http://localhost:5173') })

  it('completes the full happy path journey', () => {
    // 1. Ensure the login status of the landlord user
    ensureLoggedIn(testUser)

    // 2. Enter Dashboard Main
    cy.wait(1000)
    cy.contains('.menu-label', 'Dashboard').click()

    // 3. Enter the upload contract page
    cy.wait(2000)
    cy.contains('.upload-btn', 'Upload New Contract').click()

    // 4. Upload contract documents
    cy.get('body').then(($body) => {
      cy.wait(2000)
      if ($body.find('.upload-container').length > 0) {
        cy.get('.drop-zone').selectFile('cypress/fixtures/test.pdf', {
          action: 'drag-drop'
        });
        cy.wait(2000)
        cy.contains('Upload 1 File').click()
        cy.wait(3000)
        cy.contains('Successfully uploaded').should('be.visible')
        cy.contains('Go to Dashboard').click()
      }
    })

    // 4. Download the contract file and upload the Prompt Lab page for analysis
    cy.intercept('GET', '**/download/**').as('downloadFile');
    cy.wait(3000)
    cy.get('button[title="Download report"]').first().click();
    cy.wait('@downloadFile').then((interception) => {
      const downloadedFile = interception.response.body;

      cy.wait(3000)
      cy.get('button[title="Go Prompt Lab"]').first().click();
      cy.get('.file-input').selectFile({
        contents: Cypress.Buffer.from(downloadedFile),
        fileName: 'downloaded-contract.pdf',
        mimeType: 'application/pdf'
      }, { force: true });

      cy.wait(2000)
      cy.contains('Process File').click()
    });

    // 5. Waiting for the completion of contract analysis
    cy.get('.download-btn', { timeout: 80000 })

    // 6. Return to Dashboard Main again
    cy.wait(3000)
    cy.contains('.menu-label', 'Dashboard').click()

    // 7. Enter the page for viewing contract sentence analysis
    cy.wait(3000)
    cy.get('button[title="View analysis"]').first().click();

    // 8. View sentence analysis in detail
    cy.wait(3000)
    cy.get('button[title="View Details"]').first().click();

    // 9. Log out and return to the login page
    cy.wait(6000)
    cy.contains(testUser.name).click()
    cy.contains('Logout').click()
  })
})