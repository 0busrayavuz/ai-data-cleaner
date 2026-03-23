import { useState } from 'react'
import './App.css'

function App() {
  return (
    <div className="app-container container">
      <nav className="navbar">
        <h1 className="glow-text">AI Data Analyst Pro</h1>
        <button className="btn-primary" style={{ padding: '8px 16px', fontSize: '0.9rem' }}>
          Connect
        </button>
      </nav>
      
      <main className="main-content">
        <div className="glass-panel" style={{ padding: '40px', textAlign: 'center' }}>
          <h2 style={{ fontSize: '2.5rem', marginBottom: '16px' }}>
            Next-Gen AI Data Cleaning & Analysis
          </h2>
          <p style={{ color: 'var(--text-secondary)', maxWidth: '600px', margin: '0 auto 30px' }}>
            Drag and drop your dataset to automatically handle missing values,
            detect anomalies, and generate intelligent feature engineering pipelines.
          </p>
          <button className="btn-primary">
            Get Started
          </button>
        </div>
      </main>
    </div>
  )
}

export default App
