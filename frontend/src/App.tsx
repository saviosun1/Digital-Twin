import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import AvatarCreate from './pages/AvatarCreate'
import Questionnaire from './pages/Questionnaire'
import Chat from './pages/Chat'
import Scheduler from './pages/Scheduler'
import './App.css'

function App() {
  return (
    <div className="app">
      <Routes>
        <Route path="/" element={<Layout><Home /></Layout>} />
        <Route path="/login" element={<Layout><Login /></Layout>} />
        <Route path="/register" element={<Layout><Register /></Layout>} />
        <Route path="/dashboard" element={<Layout><Dashboard /></Layout>} />
        <Route path="/avatar/create" element={<Layout><AvatarCreate /></Layout>} />
        <Route path="/avatar/:id/questionnaire" element={<Layout><Questionnaire /></Layout>} />
        <Route path="/chat/:avatarId" element={<Layout><Chat /></Layout>} />
        <Route path="/scheduler/:avatarId" element={<Layout><Scheduler /></Layout>} />
      </Routes>
    </div>
  )
}

export default App
