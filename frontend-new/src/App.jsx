import { useState } from 'react'
import './App.css'
import Hero from './components/Hero'
import FileUpload from './components/FileUpload'
import AnalysisCards from './components/AnalysisCards'
import Footer from './components/Footer'

function App() {
  const [selectedFile, setSelectedFile] = useState(null)

  return (
    <div className="app-container container">
      <nav className="navbar">
        <h1 className="glow-text">AI Data Analyst Pro</h1>
        <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          Powered by FastAPI + React
        </span>
      </nav>

      <main className="main-content">
        <Hero />
        <FileUpload onFileSelect={setSelectedFile} />
        <AnalysisCards />
      </main>

      <Footer />
    </div>
  )
}

export default App
