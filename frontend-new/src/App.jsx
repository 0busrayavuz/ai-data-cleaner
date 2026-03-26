import { useState } from 'react'
import './App.css'
import Hero from './components/Hero'
import FileUpload from './components/FileUpload'
import AnalysisCards from './components/AnalysisCards'
import AnalysisResults from './components/AnalysisResults'
import Footer from './components/Footer'
import { uploadFile, analyzeData, applyClean } from './services/api'
import Chatbot from './components/Chatbot'
import AuthModal from './components/AuthModal'
import UserDashboard from './components/UserDashboard'

function App() {
  const [status, setStatus] = useState('idle') // idle | uploading | analyzing | results | error
  const [errorMsg, setErrorMsg] = useState('')
  const [datasetId, setDatasetId] = useState(null)
  const [recommendations, setRecommendations] = useState([])
  const [isAuthOpen, setIsAuthOpen] = useState(false)
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [currentView, setCurrentView] = useState('home') // home | dashboard

  const handleLogin = (user) => {
    setIsLoggedIn(true)
    setIsAuthOpen(false)
    setCurrentView('dashboard')
  }

  const handleLogout = () => {
    setIsLoggedIn(false)
    setCurrentView('home')
  }

  const handleFileSelect = async (file) => {
    setStatus('uploading')
    setErrorMsg('')
    try {
      const uploadRes = await uploadFile(file)
      const id = uploadRes.dataset_id
      setDatasetId(id)
      setStatus('analyzing')
      const analyzeRes = await analyzeData(id)
      setRecommendations(analyzeRes.recommendations?.recommendations || [])
      setStatus('results')
    } catch (e) {
      setErrorMsg(e.message || 'Something went wrong')
      setStatus('error')
    }
  }

  const handleApply = async (selections) => {
    await applyClean(datasetId, selections)
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
        <div className="nav-links">
          <button 
            className={`nav-btn ${currentView === 'home' ? 'active' : ''}`} 
            onClick={() => setCurrentView('home')}
          >
            Ana Sayfa
          </button>
          
          {isLoggedIn ? (
            <>
              <button 
                className={`nav-btn ${currentView === 'dashboard' ? 'active' : ''}`}
                onClick={() => setCurrentView('dashboard')}
              >
                Panelim
              </button>
              <button className="nav-btn" onClick={handleLogout}>Çıkış Yap</button>
            </>
          ) : (
            <button className="nav-btn" onClick={() => setIsAuthOpen(true)}>Hesabım</button>
          )}
        </div>
      </nav>

      <main className="main-content">
        {currentView === 'home' ? (
          <>
            <Hero />
            <FileUpload onFileSelect={handleFileSelect} />
            {renderStatus()}
            {status === 'results' && (
              <AnalysisResults
                recommendations={recommendations}
                datasetId={datasetId}
                onApply={handleApply}
              />
            )}
            <AnalysisCards />
          </>
        ) : (
          <UserDashboard />
        )}
        <Chatbot />
        <AuthModal isOpen={isAuthOpen} onClose={() => setIsAuthOpen(false)} onLogin={handleLogin} />
      </main>

      <Footer />
    </div>
  )
}

export default App
