import { Route, Routes } from 'react-router-dom'
import Header from './components/Header.jsx'
import Footer from './components/Footer.jsx'
import RegisterModal from './components/RegisterModal.jsx'
import LoginModal from './components/LoginModal.jsx'
import ReceiptModal from './components/ReceiptModal.jsx'
import Home from './pages/Home.jsx'
import Account from './pages/Account.jsx'
import { useApp } from './app-context.jsx'

export default function App() {
  const { modal } = useApp()
  return (
    <>
      <Header />
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/lk" element={<Account />} />
          <Route path="*" element={<Home />} />
        </Routes>
      </main>
      <Footer />
      {modal === 'register' && <RegisterModal />}
      {modal === 'login' && <LoginModal />}
      {modal === 'receipt' && <ReceiptModal />}
    </>
  )
}
