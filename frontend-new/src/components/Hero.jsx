import React from 'react';
import { Sparkles, BarChart2, Zap } from 'lucide-react';
import './Hero.css';

const Hero = () => {
  return (
    <section className="hero-section text-center">
      <div className="badge glass-panel">
        <Sparkles size={16} className="text-accent" />
        <span>v2.0 powered by FastAPI</span>
      </div>
      
      <h2 className="hero-title">
        Next-Gen AI <br />
        <span className="glow-text">Data Cleaning & Analysis</span>
      </h2>
      
      <p className="hero-subtitle">
        Upload your dataset and let our advanced AI pipeline handle missing values,
        detect anomalies, and generate intelligent feature engineering pipelines.
      </p>

      <div className="hero-stats glass-panel">
        <div className="stat-item">
          <Zap size={24} className="stat-icon" />
          <div>
            <h4>Lightning Fast</h4>
            <p>Process millions of rows in seconds</p>
          </div>
        </div>
        <div className="stat-divider"></div>
        <div className="stat-item">
          <BarChart2 size={24} className="stat-icon" />
          <div>
            <h4>Smart Analytics</h4>
            <p>Automatic anomaly & pattern detection</p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero;
