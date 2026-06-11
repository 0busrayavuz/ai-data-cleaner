import { useState, useEffect } from 'react'
import {
  Database,
  FileSearch,
  GitCompareArrows,
  Home,
  LayoutDashboard,
  LogIn,
  LogOut,
  WandSparkles,
} from 'lucide-react'
import './App.css'
import Hero from './components/Hero'
import FileUpload from './components/FileUpload'
import AnalysisCards from './components/AnalysisCards'
import AnalysisResults from './components/AnalysisResults'
import HowItWorks from './components/HowItWorks'
import Footer from './components/Footer'
import {
  uploadFile,
  analyzeData,
  applyClean,
  fetchMe,
  getStoredToken,
  clearAuthToken,
  fetchProjects,
  createProject,
  fetchTemplates,
  getDatasetStatus,
} from './services/api'
import Chatbot from './components/Chatbot'
import AuthModal from './components/AuthModal'
import UserDashboard from './components/UserDashboard'
import DatasetWorkspace from './components/DatasetWorkspace'

function App() {
  const [status, setStatus] = useState('idle')
  const [errorMsg, setErrorMsg] = useState('')
  const [datasetId, setDatasetId] = useState(null)
  const [originalFilename, setOriginalFilename] = useState('')
  const [recommendations, setRecommendations] = useState([])
  const [isAuthOpen, setIsAuthOpen] = useState(false)
  const [isLoggedIn, setIsLoggedIn] = useState(() => !!getStoredToken())
  const [userEmail, setUserEmail] = useState('')
  const [currentView, setCurrentView] = useState('home')
  const [projects, setProjects] = useState([])
  const [selectedProjectId, setSelectedProjectId] = useState(null)
  const [templates, setTemplates] = useState([])

  const loadProjects = () => {
    fetchProjects()
      .then((r) => setProjects(r.projects || []))
      .catch(() => setProjects([]))
  }

  const loadTemplates = () => {
    fetchTemplates()
      .then((r) => setTemplates(r.templates || []))
      .catch(() => setTemplates([]))
  }

  useEffect(() => {
    if (!getStoredToken()) return
    let cancelled = false
    fetchMe()
      .then((me) => {
        if (cancelled) return
        setIsLoggedIn(true)
        setUserEmail(me.email || '')
      })
      .catch(() => {
        if (cancelled) return
        clearAuthToken()
        setIsLoggedIn(false)
        setUserEmail('')
      })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (!isLoggedIn) return
    loadProjects()
    loadTemplates()
  }, [isLoggedIn])

  const handleLogin = (user) => {
    setIsLoggedIn(true)
    setUserEmail(user?.email || '')
    setIsAuthOpen(false)
    setCurrentView('dashboard')
    loadProjects()
    loadTemplates()
  }

  const handleLogout = () => {
    clearAuthToken()
    setIsLoggedIn(false)
    setUserEmail('')
    setCurrentView('home')
  }

  const openDatasetWorkspace = (id, view = 'profile') => {
    setDatasetId(Number(id))
    setCurrentView(view)
  }

  const handleFileSelect = async (file) => {
    if (!getStoredToken()) {
      setIsAuthOpen(true)
      setErrorMsg('Dosya yüklemek için giriş yapın.')
      setStatus('error')
      return
    }
    setStatus('uploading')
    setErrorMsg('')
    try {
      const uploadRes = await uploadFile(file, selectedProjectId)
      const id = uploadRes.dataset_id
      setDatasetId(id)
      setOriginalFilename(uploadRes.original_filename || file.name)
      setStatus('analyzing')
      let analyzeRes = await analyzeData(id)
      if (analyzeRes.status === 'analyzing') {
        const POLL_TIMEOUT_MS = 120_000; // 2 minutes
        await new Promise((resolve, reject) => {
          const deadline = Date.now() + POLL_TIMEOUT_MS;
          const interval = setInterval(async () => {
            if (Date.now() > deadline) {
              clearInterval(interval);
              reject(new Error('Analiz zaman aşımına uğradı. Lütfen sayfayı yenileyerek tekrar deneyin.'));
              return;
            }
            try {
              const statusRes = await getDatasetStatus(id)
              if (statusRes.status === 'ready') {
                clearInterval(interval)
                resolve()
              } else if (statusRes.status === 'error') {
                clearInterval(interval)
                reject(new Error('Dosya analizi sırasında hata oluştu.'))
              }
            } catch (err) {
              clearInterval(interval)
              reject(err)
            }
          }, 1500)
        })
        analyzeRes = await analyzeData(id)
      }
      setRecommendations(analyzeRes.recommendations?.recommendations || [])
      setStatus('results')
    } catch (e) {
      setErrorMsg(e.message || 'Something went wrong')
      setStatus('error')
    }
  }

  const handleApply = async (selections) => {
    return await applyClean(datasetId, selections)
  }

  const handleCreateProject = async (name) => {
    const p = await createProject(name)
    await loadProjects()
    setSelectedProjectId(p.id)
  }

  const renderStatus = () => {
    if (status === 'uploading') {
      return (
        <div className="status-msg">
          <span className="status-spinner" aria-hidden />
          <div>
            <strong>Dosya güvenli alana yükleniyor</strong>
            <span>Dosya yapısı ve biçimi kontrol ediliyor.</span>
          </div>
        </div>
      )
    }
    if (status === 'analyzing') {
      return (
        <div className="status-msg">
          <span className="status-spinner" aria-hidden />
          <div>
            <strong>Kalite analizi devam ediyor</strong>
            <span>Eksik değer, aykırı gözlem ve format sorunları taranıyor.</span>
          </div>
        </div>
      )
    }
    if (status === 'error') {
      return (
        <div className="status-msg error">
          <span className="status-error-mark" aria-hidden>!</span>
          <div>
            <strong>İşlem tamamlanamadı</strong>
            <span>{errorMsg}</span>
          </div>
        </div>
      )
    }
    return null
  }

  return (
    <div className="app-shell">
      <header className="navbar-shell">
        <nav className="container navbar-inner" aria-label="Ana menü">
          <button
            type="button"
            className="navbar-brand"
            onClick={() => setCurrentView('home')}
            aria-label="VeriTemiz AI ana sayfa"
          >
            <span className="brand-mark" aria-hidden>
              <Database size={21} strokeWidth={2.2} />
            </span>
            <div className="navbar-title-wrap">
              <h1 className="navbar-title">VeriTemiz <span>AI</span></h1>
              <p className="navbar-tagline">Veri kalite çalışma alanı</p>
            </div>
          </button>
          <div className="nav-links">
            <button
              type="button"
              className={`nav-btn ${currentView === 'home' ? 'active' : ''}`}
              onClick={() => setCurrentView('home')}
            >
              <Home size={16} aria-hidden />
              Ana Sayfa
            </button>

            {isLoggedIn ? (
              <>
                <button
                  type="button"
                  className={`nav-btn ${currentView === 'dashboard' ? 'active' : ''}`}
                  onClick={() => setCurrentView('dashboard')}
                >
                  <LayoutDashboard size={16} aria-hidden />
                  Panelim
                </button>
                <button
                  type="button"
                  className={`nav-btn ${currentView === 'profile' ? 'active' : ''}`}
                  onClick={() => setCurrentView('profile')}
                >
                  <FileSearch size={16} aria-hidden />
                  Profil
                </button>
                <button
                  type="button"
                  className={`nav-btn ${currentView === 'studio' ? 'active' : ''}`}
                  onClick={() => setCurrentView('studio')}
                >
                  <WandSparkles size={16} aria-hidden />
                  Stüdyo
                </button>
                <button
                  type="button"
                  className={`nav-btn ${currentView === 'comparison' ? 'active' : ''}`}
                  onClick={() => setCurrentView('comparison')}
                >
                  <GitCompareArrows size={16} aria-hidden />
                  Karşılaştır
                </button>
                <button type="button" className="nav-btn nav-btn-quiet" onClick={handleLogout}>
                  <LogOut size={16} aria-hidden />
                  Çıkış
                </button>
              </>
            ) : (
              <button type="button" className="nav-btn nav-btn-cta" onClick={() => setIsAuthOpen(true)}>
                <LogIn size={16} aria-hidden />
                Giriş Yap
              </button>
            )}
          </div>
        </nav>
      </header>

      <main className="main-content container">
        {currentView === 'home' && (
          <>
            <Hero
              isLoggedIn={isLoggedIn}
              onStart={() => {
                if (!isLoggedIn) {
                  setIsAuthOpen(true)
                  return
                }
                document.getElementById('upload-workspace')?.scrollIntoView({ behavior: 'smooth' })
              }}
              onOpenDashboard={() => setCurrentView('dashboard')}
            />
            <HowItWorks />
            <FileUpload
              onFileSelect={handleFileSelect}
              canUpload={isLoggedIn}
              projects={projects}
              selectedProjectId={selectedProjectId}
              onProjectChange={setSelectedProjectId}
              onCreateProject={handleCreateProject}
              onNeedAuth={() => {
                setIsAuthOpen(true)
                setErrorMsg('Dosya yüklemek için önce giriş yapın.')
                setStatus('error')
              }}
            />
            {renderStatus()}
            {status === 'results' && (
              <AnalysisResults
                key={datasetId}
                recommendations={recommendations}
                datasetId={datasetId}
                originalFilename={originalFilename}
                onApply={handleApply}
                templates={templates}
                onTemplatesChanged={loadTemplates}
              />
            )}
            <AnalysisCards />
          </>
        )}
        {currentView === 'dashboard' && (
          <UserDashboard
            userEmail={userEmail}
            onNewAnalysis={() => setCurrentView('home')}
            onOpenDataset={(id) => openDatasetWorkspace(id, 'profile')}
          />
        )}
        {['profile', 'studio', 'comparison'].includes(currentView) && (
          <DatasetWorkspace
            view={currentView}
            selectedDatasetId={datasetId}
            onDatasetChange={setDatasetId}
            onNavigate={setCurrentView}
            templates={templates}
            onTemplatesChanged={loadTemplates}
          />
        )}
        <Chatbot onNeedAuth={() => setIsAuthOpen(true)} isLoggedIn={isLoggedIn} />
        <AuthModal
          isOpen={isAuthOpen}
          onClose={() => setIsAuthOpen(false)}
          onLogin={handleLogin}
        />
      </main>

      <Footer />
    </div>
  )
}

export default App
