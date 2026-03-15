import React, { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuthStore, API_URL } from '../stores/auth'
import './PersonalityEnrich.css'

interface AIQuestion {
  id: string
  category: string
  question: string
}

interface ManualInput {
  id: string
  content: string
  tags: string[]
  created_at: string
}

interface UploadedFile {
  filename: string
  size: number
  created_at: string
}

interface DistilledData {
  'soul.md': string
  'memories.md': string
  'relationships.md': string
  'secrets.md': string
}

type TabType = 'ai-test' | 'upload' | 'manual' | 'distilled'

const PersonalityEnrich: React.FC = () => {
  const { id: avatarId } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { token } = useAuthStore()
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  // Tab state
  const [activeTab, setActiveTab] = useState<TabType>('ai-test')
  const [avatarName, setAvatarName] = useState('')
  
  // AI Test states
  const [aiQuestions, setAiQuestions] = useState<AIQuestion[]>([])
  const [aiAnswers, setAiAnswers] = useState<Record<string, string>>({})
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [aiLoading, setAiLoading] = useState(false)
  const [batchId, setBatchId] = useState('')
  const [aiHistoryCount, setAiHistoryCount] = useState(0)
  
  // Upload states
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const [uploadLoading, setUploadLoading] = useState(false)
  
  // Manual input states
  const [manualInputs, setManualInputs] = useState<ManualInput[]>([])
  const [manualContent, setManualContent] = useState('')
  const [manualTags, setManualTags] = useState('')
  const [manualLoading, setManualLoading] = useState(false)
  
  // Distilled data
  const [distilledData, setDistilledData] = useState<DistilledData | null>(null)
  const [distillLoading, setDistillLoading] = useState(false)
  
  // Common error
  const [error, setError] = useState('')

  useEffect(() => {
    if (!token) {
      navigate('/login')
      return
    }
    fetchAvatarInfo()
    fetchAiHistoryCount()
    fetchUploadedFiles()
    fetchManualInputs()
    fetchDistilledData()
  }, [avatarId, token, navigate])

  const fetchAvatarInfo = async () => {
    try {
      const response = await fetch(`${API_URL}/avatars/${avatarId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setAvatarName(data.name)
      }
    } catch (error) {
      console.error('Failed to fetch avatar:', error)
    }
  }

  const fetchAiHistoryCount = async () => {
    try {
      const response = await fetch(`${API_URL}/avatars/${avatarId}/ai-answers`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setAiHistoryCount(data.total_questions)
      }
    } catch (error) {
      console.error('Failed to fetch AI history:', error)
    }
  }

  const fetchUploadedFiles = async () => {
    try {
      const response = await fetch(`${API_URL}/avatars/${avatarId}/uploads`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setUploadedFiles(data.files)
      }
    } catch (error) {
      console.error('Failed to fetch uploaded files:', error)
    }
  }

  const fetchManualInputs = async () => {
    try {
      const response = await fetch(`${API_URL}/avatars/${avatarId}/manual-inputs`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setManualInputs(data.inputs)
      }
    } catch (error) {
      console.error('Failed to fetch manual inputs:', error)
    }
  }

  const fetchDistilledData = async () => {
    try {
      const response = await fetch(`${API_URL}/avatars/${avatarId}/distilled`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setDistilledData(data)
      }
    } catch (error) {
      console.error('Failed to fetch distilled data:', error)
    }
  }

  // ========== AI Test Functions ==========
  const generateAIQuestions = async () => {
    setAiLoading(true)
    setError('')
    try {
      const response = await fetch(`${API_URL}/avatars/${avatarId}/ai-questions`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || '生成问题失败')
      }
      const data = await response.json()
      setAiQuestions(data.questions)
      setBatchId(data.batch_id)
      setAiAnswers({})
      setCurrentQuestionIndex(0)
    } catch (error: any) {
      setError(error.message)
    } finally {
      setAiLoading(false)
    }
  }

  const saveAiAnswers = async () => {
    if (!batchId || aiQuestions.length === 0) return
    
    setAiLoading(true)
    setError('')
    try {
      const answers = aiQuestions.map(q => ({
        question_id: q.id,
        question: q.question,
        answer: aiAnswers[q.id] || '',
        category: q.category
      }))
      
      const response = await fetch(`${API_URL}/avatars/${avatarId}/ai-answers/${batchId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(answers)
      })
      
      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || '保存答案失败')
      }
      
      // Reset and refresh
      setAiQuestions([])
      setAiAnswers({})
      setBatchId('')
      setCurrentQuestionIndex(0)
      fetchAiHistoryCount()
      fetchDistilledData()
      alert('答案已保存，AI正在提炼人格数据...')
    } catch (error: any) {
      setError(error.message)
    } finally {
      setAiLoading(false)
    }
  }

  const handleAnswerChange = (questionId: string, value: string) => {
    setAiAnswers(prev => ({ ...prev, [questionId]: value }))
  }

  const currentQuestion = aiQuestions[currentQuestionIndex]
  const aiProgress = aiQuestions.length > 0 ? ((currentQuestionIndex + 1) / aiQuestions.length) * 100 : 0

  // ========== Upload Functions ==========
  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    
    setUploadLoading(true)
    setError('')
    
    const formData = new FormData()
    formData.append('file', file)
    
    try {
      const response = await fetch(`${API_URL}/avatars/${avatarId}/uploads`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      })
      
      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || '上传失败')
      }
      
      fetchUploadedFiles()
      fetchDistilledData()
      alert('文件上传成功，AI正在提炼人格数据...')
    } catch (error: any) {
      setError(error.message)
    } finally {
      setUploadLoading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const deleteFile = async (filename: string) => {
    if (!confirm(`确定要删除文件 "${filename}" 吗？`)) return
    
    try {
      const response = await fetch(`${API_URL}/avatars/${avatarId}/uploads/${filename}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      
      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || '删除失败')
      }
      
      fetchUploadedFiles()
    } catch (error: any) {
      setError(error.message)
    }
  }

  // ========== Manual Input Functions ==========
  const saveManualInput = async () => {
    if (!manualContent.trim()) return
    
    setManualLoading(true)
    setError('')
    
    const tags = manualTags.split(',').map(t => t.trim()).filter(t => t)
    
    try {
      const response = await fetch(`${API_URL}/avatars/${avatarId}/manual-inputs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ content: manualContent, tags })
      })
      
      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || '保存失败')
      }
      
      setManualContent('')
      setManualTags('')
      fetchManualInputs()
      fetchDistilledData()
    } catch (error: any) {
      setError(error.message)
    } finally {
      setManualLoading(false)
    }
  }

  const deleteManualInput = async (inputId: string) => {
    if (!confirm('确定要删除这条记忆吗？')) return
    
    try {
      const response = await fetch(`${API_URL}/avatars/${avatarId}/manual-inputs/${inputId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      
      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || '删除失败')
      }
      
      fetchManualInputs()
    } catch (error: any) {
      setError(error.message)
    }
  }

  // ========== Distill Functions ==========
  const triggerDistill = async () => {
    setDistillLoading(true)
    setError('')
    
    try {
      const response = await fetch(`${API_URL}/avatars/${avatarId}/distill`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ force: true })
      })
      
      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || '提炼失败')
      }
      
      fetchDistilledData()
      alert('人格数据提炼完成！')
    } catch (error: any) {
      setError(error.message)
    } finally {
      setDistillLoading(false)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  return (
    <div className="personality-enrich">
      <div className="container">
        <div className="enrich-header">
          <div>
            <h1>丰富 {avatarName} 的人格</h1>
            <p className="text-muted">通过多种方式让数字分身更接近真实的你</p>
          </div>
          <button 
            className="btn btn-secondary"
            onClick={() => navigate('/dashboard')}
          >
            ← 返回
          </button>
        </div>

        {error && (
          <div className="error-banner">
            <span>❌</span> {error}
            <button onClick={() => setError('')}>×</button>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="tab-nav">
          <button 
            className={`tab-btn ${activeTab === 'ai-test' ? 'active' : ''}`}
            onClick={() => setActiveTab('ai-test')}
          >
            <span className="tab-icon">🧠</span>
            AI人格测试
            {aiHistoryCount > 0 && <span className="badge">{aiHistoryCount}</span>}
          </button>
          <button 
            className={`tab-btn ${activeTab === 'upload' ? 'active' : ''}`}
            onClick={() => setActiveTab('upload')}
          >
            <span className="tab-icon">📁</span>
            上传聊天记录
            {uploadedFiles.length > 0 && <span className="badge">{uploadedFiles.length}</span>}
          </button>
          <button 
            className={`tab-btn ${activeTab === 'manual' ? 'active' : ''}`}
            onClick={() => setActiveTab('manual')}
          >
            <span className="tab-icon">✏️</span>
            手动输入
            {manualInputs.length > 0 && <span className="badge">{manualInputs.length}</span>}
          </button>
          <button 
            className={`tab-btn ${activeTab === 'distilled' ? 'active' : ''}`}
            onClick={() => setActiveTab('distilled')}
          >
            <span className="tab-icon">📊</span>
            人格概览
          </button>
        </div>

        {/* Tab Content */}
        <div className="tab-content">
          {/* AI Test Tab */}
          {activeTab === 'ai-test' && (
            <div className="tab-panel">
              <div className="panel-header">
                <h2>AI人格测试</h2>
                <p>AI会根据已有数据生成个性化问题，回答越多人格越丰富</p>
                {aiHistoryCount > 0 && (
                  <p className="history-info">已累计回答 {aiHistoryCount} 个问题</p>
                )}
              </div>

              {aiQuestions.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-icon">🎯</div>
                  <h3>开始新一轮测试</h3>
                  <p>AI将为你生成10个深度问题，探索你独特的人格特质</p>
                  <button 
                    className="btn btn-primary"
                    onClick={generateAIQuestions}
                    disabled={aiLoading}
                  >
                    {aiLoading ? '生成中...' : '生成新问题'}
                  </button>
                </div>
              ) : (
                <div className="question-card">
                  <div className="progress-bar">
                    <div className="progress-bar-fill" style={{ width: `${aiProgress}%` }}></div>
                  </div>
                  <p className="progress-text">问题 {currentQuestionIndex + 1} / {aiQuestions.length}</p>
                  
                  <div className="question-content">
                    <span className="category-tag">{currentQuestion?.category}</span>
                    <h3>{currentQuestion?.question}</h3>
                    <textarea
                      value={aiAnswers[currentQuestion?.id] || ''}
                      onChange={(e) => handleAnswerChange(currentQuestion?.id, e.target.value)}
                      placeholder="请输入你的回答..."
                      rows={5}
                    />
                  </div>

                  <div className="question-actions">
                    {currentQuestionIndex > 0 && (
                      <button 
                        className="btn btn-secondary"
                        onClick={() => setCurrentQuestionIndex(i => i - 1)}
                      >
                        上一题
                      </button>
                    )}
                    
                    {currentQuestionIndex < aiQuestions.length - 1 ? (
                      <button 
                        className="btn btn-primary"
                        onClick={() => setCurrentQuestionIndex(i => i + 1)}
                        disabled={!aiAnswers[currentQuestion?.id]?.trim()}
                      >
                        下一题
                      </button>
                    ) : (
                      <button 
                        className="btn btn-primary"
                        onClick={saveAiAnswers}
                        disabled={aiLoading || !aiAnswers[currentQuestion?.id]?.trim()}
                      >
                        {aiLoading ? '保存中...' : '完成并保存'}
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Upload Tab */}
          {activeTab === 'upload' && (
            <div className="tab-panel">
              <div className="panel-header">
                <h2>上传聊天记录</h2>
                <p>上传微信、QQ等聊天记录的txt或md文件（最大512KB）</p>
              </div>

              <div className="upload-area">
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileSelect}
                  accept=".txt,.md"
                  style={{ display: 'none' }}
                />
                <div className="upload-box" onClick={() => fileInputRef.current?.click()}>
                  <div className="upload-icon">📤</div>
                  <p>点击或拖拽文件到此处上传</p>
                  <p className="upload-hint">支持 .txt 和 .md 格式，最大 512KB</p>
                </div>
                {uploadLoading && <p className="loading-text">上传中...</p>}
              </div>

              {uploadedFiles.length > 0 && (
                <div className="file-list">
                  <h4>已上传的文件</h4>
                  {uploadedFiles.map(file => (
                    <div key={file.filename} className="file-item">
                      <div className="file-info">
                        <span className="file-icon">📄</span>
                        <div>
                          <p className="file-name">{file.filename}</p>
                          <p className="file-meta">{formatFileSize(file.size)} · {new Date(file.created_at).toLocaleDateString()}</p>
                        </div>
                      </div>
                      <button 
                        className="btn-icon"
                        onClick={() => deleteFile(file.filename)}
                        title="删除"
                      >
                        🗑️
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Manual Input Tab */}
          {activeTab === 'manual' && (
            <div className="tab-panel">
              <div className="panel-header">
                <h2>手动输入记忆</h2>
                <p>直接输入你想让分身记住的事情、故事或感受</p>
              </div>

              <div className="manual-input-form">
                <textarea
                  value={manualContent}
                  onChange={(e) => setManualContent(e.target.value)}
                  placeholder="写下你想记录的事情...&#10;例如：我小时候养过一只叫豆豆的金毛犬，它陪伴了我整个童年..."
                  rows={6}
                />
                <input
                  type="text"
                  value={manualTags}
                  onChange={(e) => setManualTags(e.target.value)}
                  placeholder="标签（用逗号分隔）：童年, 宠物, 回忆"
                />
                <button 
                  className="btn btn-primary"
                  onClick={saveManualInput}
                  disabled={manualLoading || !manualContent.trim()}
                >
                  {manualLoading ? '保存中...' : '添加记忆'}
                </button>
              </div>

              {manualInputs.length > 0 && (
                <div className="memory-list">
                  <h4>已添加的记忆 ({manualInputs.length}条)</h4>
                  {manualInputs.map(input => (
                    <div key={input.id} className="memory-item">
                      <p className="memory-content">{input.content}</p>
                      <div className="memory-meta">
                        <div className="memory-tags">
                          {input.tags.map(tag => (
                            <span key={tag} className="tag">{tag}</span>
                          ))}
                        </div>
                        <button 
                          className="btn-icon"
                          onClick={() => deleteManualInput(input.id)}
                          title="删除"
                        >
                          🗑️
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Distilled Data Tab */}
          {activeTab === 'distilled' && (
            <div className="tab-panel">
              <div className="panel-header">
                <h2>人格概览</h2>
                <p>AI自动提炼的人格核心、记忆、关系和秘密</p>
              </div>

              <div className="distill-actions">
                <button 
                  className="btn btn-primary"
                  onClick={triggerDistill}
                  disabled={distillLoading}
                >
                  {distillLoading ? '提炼中...' : '🔄 重新提炼人格数据'}
                </button>
              </div>

              {distilledData && (
                <div className="distilled-grid">
                  <div className="distilled-card">
                    <h3>🧬 人格核心 (soul.md)</h3>
                    <pre>{distilledData['soul.md'] || '暂无数据'}</pre>
                  </div>
                  <div className="distilled-card">
                    <h3>💭 重要记忆 (memories.md)</h3>
                    <pre>{distilledData['memories.md'] || '暂无数据'}</pre>
                  </div>
                  <div className="distilled-card">
                    <h3>👥 人际关系 (relationships.md)</h3>
                    <pre>{distilledData['relationships.md'] || '暂无数据'}</pre>
                  </div>
                  <div className="distilled-card secret">
                    <h3>🔒 私密信息 (secrets.md)</h3>
                    <pre>{distilledData['secrets.md'] || '暂无数据'}</pre>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default PersonalityEnrich
