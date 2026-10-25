import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { ClerkProvider } from "@clerk/react"
import { BrowserRouter } from 'react-router-dom'
import './styles/globals.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ClerkProvider 
    publishableKey={import.meta.env.VITE_CLEK_PUBLISHABLE_KEY}>
      <BrowserRouter>
      <App />
      </BrowserRouter>
    </ClerkProvider>
    
  </StrictMode>,
)
