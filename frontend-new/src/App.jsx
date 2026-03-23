import { useState } from 'react'
import './App.css'
import Hero from './components/Hero'
import FileUpload from './components/FileUpload'
import AnalysisCards from './components/AnalysisCards'
import AnalysisResults from './components/AnalysisResults'
import Footer from './components/Footer'
import { uploadFile, analyzeData, applyClean } from './services/api'

function App() {
  const [status, setStatus] = useState('idle') // idle | uploading | analyzing | results | error
  const [errorMsg, setErrorMsg] = useState('')
  const [filename, setFilename] = useState(null)
  const [recommendations, setRecommendations] = useState([])

  const handleFileSelect = async (file) => {
    setStatus('uploading')
    setErrorMsg('')
    try {
      const uploadRes = await uploadFile(file)
      const fname = uploadRes.filename
      setFilename(fname)
      setStatus('analyzing')
      const analyzeRes = await analyzeData(fname)
      setRecommendations(analyzeRes.recommendations || [])
      setStatus('results')
    } catch (e) {
      setErrorMsg(e.message || 'Something went wrong')
      setStatus('error')
    }
  }

  const handleApply = async () => {
    await applyClean(filename, recommendations.map(r => r.type))
  }

  const renderStatus = () => {
    if (status === 'uploading') return <p className="status-msg">⏳ Uploading your file...</p>
    if (status === 'analyzing') return <p className="status-msg">🔍 Analyzing data with AI pipeline...</p>
    if (status === 'error') return <p className="status-msg error">❌ {errorMsg}</p>
    return null
  }

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
        <FileUpload onFileSelect={handleFileSelect} />
        {renderStatus()}
        {status === 'results' && (
          <AnalysisResults
            recommendations={recommendations}
            filename={filename}
            onApply={handleApply}
          />
        )}
        <AnalysisCards />
      </main>

      <Footer />
    </div>
  )
}

export default App
