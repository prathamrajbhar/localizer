import './App.css';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useEffect } from 'react';
import Layout from './components/Layout';
function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/document" element={<DocumentTranslation />} />
          <Route path="/audio" element={<AudioLocalization />} />
          <Route path="/video" element={<VideoLocalization />} />
          <Route path="/integration" element={<Integration />} />
          <Route path="/about" element={<About />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
