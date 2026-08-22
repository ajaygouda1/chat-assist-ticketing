import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'
import { AuthProvider } from './context/AuthContext'
import ReactErrorBoundary from './components/ReactErrorBoundary'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ReactErrorBoundary>
      <AuthProvider>
        <App />
      </AuthProvider>
    </ReactErrorBoundary>
  </React.StrictMode>,
)


