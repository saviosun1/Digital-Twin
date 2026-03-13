import React from 'react'
import { Link } from 'react-router-dom'
import './Home.css'

const Home: React.FC = () => {
  return (
    <div className="home">
      {/* Hero Section */}
      <section className="hero">
        <div className="container">
          <h1 className="hero-title">
            创建你的<span className="highlight">数字分身</span>
          </h1>
          <p className="hero-subtitle">
            记录你的故事、性格与记忆，让爱与智慧跨越时空延续
          </p>
          <div className="hero-actions">
            <Link to="/register" className="btn btn-primary btn-large">
              开始创建
            </Link>
            <Link to="/login" className="btn btn-secondary btn-large">
              已有账号
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features">
        <div className="container">
          <h2 className="section-title">核心功能</h2>
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">📝</div>
              <h3>性格画像</h3>
              <p>通过科学问卷和开放式问题，构建完整的性格模型</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">💬</div>
              <h3>智能对话</h3>
              <p>分身能够以你的语气和风格与他人自然交流</p>
            </div>
            <div className="feature-icon">⏰</div>
              <h3>定时消息</h3>
              <p>预设重要时刻的祝福与提醒，跨越时间的关怀</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🔒</div>
              <h3>安全私密</h3>
              <p>端到端加密，你完全掌控谁能访问你的分身</p>
            </div>
          </div>
        </div>
      </section>

      {/* Use Cases Section */}
      <section className="use-cases">
        <div className="container">
          <h2 className="section-title">使用场景</h2>
          <div className="use-cases-list">
            <div className="use-case">
              <h4>💝 爱的延续</h4>
              <p>为家人留下数字陪伴，让思念有处安放</p>
            </div>
            <div className="use-case">
              <h4>📚 智慧传承</h4>
              <p>记录人生经验，为后代提供指引</p>
            </div>
            <div className="use-case">
              <h4>🔐 重要信息</h4>
              <p>在需要时向指定人传递关键信息</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}

export default Home
