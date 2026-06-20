import { useState, useEffect } from 'react'
import {
  Home,
  LayoutDashboard,
  LogIn,
  UserRound,
  WandSparkles,
} from 'lucide-react'
import './App.css'
import Hero from './components/Hero'
import FileUpload from './components/FileUpload'
import AnalysisCards from './components/AnalysisCards'
import AnalysisResults from './components/AnalysisResults'
import HowItWorks from './components/HowItWorks'
import FAQ from './components/FAQ'
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
import AccountSettings from './components/AccountSettings'

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
  const [progress, setProgress] = useState(0)

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
    setCurrentView('panel')
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
    setStatus(null)
  }

  const scrollToUpload = () => {
    setCurrentView('home')
    setStatus(null)
    setTimeout(() => {
      const el = document.getElementById('upload-workspace')
      if (el) {
        const yOffset = -80; // Account for the sticky header height
        const y = el.getBoundingClientRect().top + window.scrollY + yOffset;
        window.scrollTo({ top: y, behavior: 'smooth' });
      }
    }, 50)
  }

  const goToHome = () => {
    setCurrentView('home');
    setStatus(null);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

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
      setErrorMsg(e.message || 'Bir şeyler ters gitti.')
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

  useEffect(() => {
    let interval
    if (status === 'uploading' || status === 'analyzing') {
      setProgress(0)
      interval = setInterval(() => {
        setProgress((p) => {
          // Asimptotik olarak %95'e yaklaş
          const remaining = 95 - p
          const step = Math.max(0.5, remaining * 0.08)
          return Math.min(95, p + step)
        })
      }, 400)
    } else if (status === 'results') {
      setProgress(100)
    } else {
      setProgress(0)
    }
    return () => clearInterval(interval)
  }, [status])

  const renderStatus = () => {
    if (status === 'uploading' || status === 'analyzing') {
      const isUploading = status === 'uploading'
      return (
        <div className="status-msg loading-with-progress">
          <div className="status-header">
            <span className="status-spinner" aria-hidden />
            <div className="status-text">
              <strong>{isUploading ? 'Dosya güvenli alana yükleniyor' : 'Kalite analizi devam ediyor'}</strong>
              <span>{isUploading ? 'Dosya yapısı ve biçimi kontrol ediliyor.' : 'Eksik değer, aykırı gözlem ve format sorunları taranıyor.'}</span>
            </div>
            <div className="status-percent">{Math.round(progress)}%</div>
          </div>
          <div className="status-progress-track">
            <div className="status-progress-fill" style={{ width: `${progress}%` }} />
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
            onClick={goToHome}
            aria-label="PrepWise ana sayfa"
          >
            <img src="/logo.png" alt="PrepWise" className="navbar-logo-img" />
          </button>
          <div className="nav-links">
            <button
              type="button"
              className={`nav-btn ${currentView === 'home' ? 'active' : ''}`}
              onClick={goToHome}
            >
              <Home size={16} aria-hidden />
              Ana sayfa
            </button>

            {isLoggedIn ? (
              <>
                <button
                  type="button"
                  className={`nav-btn ${currentView === 'panel' ? 'active' : ''}`}
                  onClick={() => setCurrentView('panel')}
                >
                  <LayoutDashboard size={16} aria-hidden />
                  Panel
                </button>
                <button
                  type="button"
                  className={`nav-btn ${
                    ['profile', 'studio', 'comparison'].includes(currentView) ? 'active' : ''
                  }`}
                  onClick={() => setCurrentView('profile')}
                >
                  <WandSparkles size={16} aria-hidden />
                  Stüdyo
                </button>
                <button
                  type="button"
                  className={`nav-btn nav-btn-account ${currentView === 'account' ? 'active' : ''}`}
                  onClick={() => setCurrentView('account')}
                >
                  <UserRound size={16} aria-hidden />
                  Hesabım
                </button>
              </>
            ) : (
              <button type="button" className="nav-btn nav-btn-cta" onClick={() => setIsAuthOpen(true)}>
                <LogIn size={16} aria-hidden />
                Giriş yap
              </button>
            )}
          </div>
        </nav>
      </header>

      {currentView === 'home' && (
        <div className="hero-marquee-container" aria-hidden="true">
          <div className="hero-marquee">
            <span>PrepWise Veri Ön İşleme</span>
            <span className="marquee-dot">•</span>
            <span>PrepWise Veri Ön İşleme</span>
            <span className="marquee-dot">•</span>
            <span>PrepWise Veri Ön İşleme</span>
            <span className="marquee-dot">•</span>
            <span>PrepWise Veri Ön İşleme</span>
            <span className="marquee-dot">•</span>
            <span>PrepWise Veri Ön İşleme</span>
            <span className="marquee-dot">•</span>
            <span>PrepWise Veri Ön İşleme</span>
            <span className="marquee-dot">•</span>
          </div>
          <div className="hero-marquee" aria-hidden="true">
            <span>PrepWise Veri Ön İşleme</span>
            <span className="marquee-dot">•</span>
            <span>PrepWise Veri Ön İşleme</span>
            <span className="marquee-dot">•</span>
            <span>PrepWise Veri Ön İşleme</span>
            <span className="marquee-dot">•</span>
            <span>PrepWise Veri Ön İşleme</span>
            <span className="marquee-dot">•</span>
            <span>PrepWise Veri Ön İşleme</span>
            <span className="marquee-dot">•</span>
            <span>PrepWise Veri Ön İşleme</span>
            <span className="marquee-dot">•</span>
          </div>
        </div>
      )}

      <main className={`main-content container ${currentView === 'home' ? 'home-view' : ''}`}>
        {currentView === 'home' && (
          <>
            <Hero
              isLoggedIn={isLoggedIn}
              onStart={() => {
                if (!isLoggedIn) {
                  setIsAuthOpen(true)
                  return
                }
                scrollToUpload()
              }}
              onOpenPanel={() => setCurrentView('panel')}
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
            <FAQ />
          </>
        )}
        {currentView === 'panel' && (
          <UserDashboard
            userEmail={userEmail}
            onNewAnalysis={scrollToUpload}
            onOpenDataset={(id) => openDatasetWorkspace(id, 'profile')}
            onProjectsChanged={loadProjects}
          />
        )}
        {currentView === 'account' && (
          <AccountSettings
            userEmail={userEmail}
            onOpenPanel={() => setCurrentView('panel')}
            onLogout={handleLogout}
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
