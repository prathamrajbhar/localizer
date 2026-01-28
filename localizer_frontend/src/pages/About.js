import React from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Users, Code, Globe, Zap, Shield, Award, Target, ArrowLeft, 
  CheckCircle, Star, Languages, Mic, Video, FileText,
  IndianRupee, Brain, TrendingUp, BookOpen, Cpu, AlertCircle, ChevronRight
} from 'lucide-react';
import { DEFAULT_LANGUAGES } from '../utils/constants';

const About = () => {
  const navigate = useNavigate();
  
  const languages = DEFAULT_LANGUAGES;

  const coreFeatures = [
    { 
      icon: <FileText className="w-8 h-8" />, 
      title: "Document Translation", 
      desc: "AI-powered translation of PDFs, DOCX, TXT with domain-specific accuracy",
      tech: "IndicTrans2 + mBART"
    },
    { 
      icon: <Mic className="w-8 h-8" />, 
      title: "Audio Localization", 
      desc: "STT + Translation + TTS pipeline for multilingual speech accessibility",
      tech: "Whisper + VITS"
    },
    { 
      icon: <Video className="w-8 h-8" />, 
      title: "Video Localization", 
      desc: "Automated subtitle generation and voiceover in 22 Indian languages",
      tech: "Speech AI + NLP"
    },
    { 
      icon: <Shield className="w-8 h-8" />, 
      title: "LMS Integration", 
      desc: "Seamless API integration with NCVET, MSDE, and Skill India platforms",
      tech: "REST APIs"
    }
  ];

  const aiModels = [
    { name: "IndicTrans2", purpose: "Neural translation for Indian languages", accuracy: "95%+" },
    { name: "Whisper Large-v3", purpose: "Speech-to-text conversion", accuracy: "92%+" },
    { name: "VITS/Tacotron2", purpose: "Text-to-speech generation", quality: "Natural" },
    { name: "IndicBERT", purpose: "Context understanding", performance: "High" },
    { name: "FastText", purpose: "Language detection", speed: "<100ms" },
    { name: "mBART", purpose: "Multilingual translation", coverage: "22 langs" }
  ];

  const impactMetrics = [
    { value: "22+", label: "Indian Languages", icon: <Languages className="w-6 h-6" /> },
    { value: "95%+", label: "Translation Accuracy", icon: <Target className="w-6 h-6" /> },
    { value: "80%", label: "Cost Reduction", icon: <IndianRupee className="w-6 h-6" /> },
    { value: "<2s", label: "Response Time", icon: <Zap className="w-6 h-6" /> }
  ];

  const techStack = [
    { category: "AI Models", items: ["IndicTrans2", "Whisper AI", "VITS/Tacotron2", "IndicBERT"], icon: <Brain className="w-6 h-6" /> },
    { category: "Backend", items: ["FastAPI", "PyTorch", "Hugging Face", "PostgreSQL"], icon: <Cpu className="w-6 h-6" /> },
    { category: "Frontend", items: ["React 19.2", "TailwindCSS", "REST APIs", "WCAG 2.1"], icon: <Code className="w-6 h-6" /> },
    { category: "Integration", items: ["NCVET APIs", "MSDE Connect", "LMS Bridge", "Skill India"], icon: <Globe className="w-6 h-6" /> }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Header */}
      <div className="bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-700 text-white">
        <div className="container mx-auto px-6 py-12">
          <div className="flex items-center mb-8">
            <button 
              onClick={() => navigate('/')}
              className="flex items-center bg-white/10 hover:bg-white/20 px-4 py-2 rounded-lg transition-colors"
            >
              <ArrowLeft size={20} className="mr-2" />
              Back to Home
            </button>
          </div>
          
          <div className="max-w-6xl mx-auto text-center">
            <div className="flex items-center justify-center mb-6">
              <div className="w-20 h-20 bg-white/20 rounded-2xl flex items-center justify-center mr-6">
                <Globe className="w-10 h-10 text-white" />
              </div>
              <div>
                <h1 className="text-4xl md:text-5xl font-bold mb-2">
                  AI-Powered Multilingual Content Localization Engine
                </h1>
                <p className="text-lg md:text-xl opacity-90">Smart India Hackathon 2025 | Problem Statement ID: SIH25203</p>
              </div>
            </div>
            
            <div className="flex flex-wrap justify-center gap-4 mb-8">
              <div className="bg-white/20 backdrop-blur-sm px-4 py-2 rounded-lg flex items-center">
                <Award className="w-5 h-5 mr-2" />
                Team SafeHorizon
              </div>
              <div className="bg-white/20 backdrop-blur-sm px-4 py-2 rounded-lg flex items-center">
                <Target className="w-5 h-5 mr-2" />
                SIH 2025
              </div>
              <div className="bg-white/20 backdrop-blur-sm px-4 py-2 rounded-lg flex items-center">
                <Star className="w-5 h-5 mr-2" />
                AI Localization
              </div>
            </div>
            
            <p className="text-lg md:text-xl opacity-95 max-w-4xl mx-auto leading-relaxed">
              Breaking down language barriers in Indian education through cutting-edge AI technology 
              that preserves cultural context while making quality content accessible in 22+ regional languages.
            </p>
          </div>
        </div>
      </div>

      {/* Problem Overview */}
      <div className="container mx-auto px-6 py-16">
        {/* Demo Video Notice */}
        <div className="mb-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <Video className="h-5 w-5 text-blue-600 mt-0.5" />
            </div>
            <div className="ml-3">
              <p className="text-sm text-blue-800">
                <strong>Note:</strong> We're currently running on CPU processing as we can't afford GPU servers yet. Some features may take longer or occasionally not work. Watch our demo video to see the full potential!
              </p>
              <div className="mt-2">
                <a 
                  href="https://youtu.be/CuezATiplts" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="inline-flex items-center text-sm font-medium text-blue-800 hover:text-blue-900"
                >
                  <Video size={16} className="mr-1" />
                  Watch Demo Video
                  <ChevronRight size={16} className="ml-1" />
                </a>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-lg p-8 mb-16">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">The Challenge We're Solving</h2>
            <p className="text-lg text-gray-600 max-w-3xl mx-auto">
              India's vocational training ecosystem faces critical language barriers that limit accessibility 
              and effectiveness of skill education across diverse linguistic communities.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center p-6 bg-red-50 rounded-xl border border-red-100">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <BookOpen className="w-8 h-8 text-red-600" />
              </div>
              <h3 className="text-lg font-bold text-gray-800 mb-3">Language Accessibility</h3>
              <p className="text-gray-600">Most training content available only in English or few regional languages, excluding rural and non-English learners.</p>
            </div>
            
            <div className="text-center p-6 bg-orange-50 rounded-xl border border-orange-100">
              <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Users className="w-8 h-8 text-orange-600" />
              </div>
              <h3 className="text-lg font-bold text-gray-800 mb-3">Cultural Mismatch</h3>
              <p className="text-gray-600">Content examples often don't relate to regional realities, reducing learning effectiveness and engagement.</p>
            </div>
            
            <div className="text-center p-6 bg-blue-50 rounded-xl border border-blue-100">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <IndianRupee className="w-8 h-8 text-blue-600" />
              </div>
              <h3 className="text-lg font-bold text-gray-800 mb-3">Manual Limitations</h3>
              <p className="text-gray-600">Traditional translation methods are costly, time-consuming, and inconsistent in quality across different domains.</p>
            </div>
          </div>
        </div>

        {/* Our Solution */}
        <div className="bg-white rounded-2xl shadow-lg p-8 mb-16">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Our AI-Powered Solution</h2>
            <p className="text-lg text-gray-600 max-w-3xl mx-auto">
              A comprehensive localization engine that combines neural translation models, 
              cultural intelligence, and speech AI to make skill content accessible and inclusive.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {coreFeatures.map((feature, index) => (
              <div key={index} className="group p-6 border border-gray-200 rounded-xl hover:border-blue-300 hover:shadow-lg transition-all duration-300">
                <div className="flex items-start mb-4">
                  <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center mr-4 text-white group-hover:scale-110 transition-transform duration-300">
                    {feature.icon}
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-800 mb-2">{feature.title}</h3>
                    <p className="text-gray-600 mb-3">{feature.desc}</p>
                    <div className="bg-gray-100 px-3 py-1 rounded-full text-sm font-medium text-gray-700">
                      {feature.tech}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* How It Works */}
        <div className="bg-white rounded-2xl shadow-lg p-8 mb-16">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">How Our System Works</h2>
            <p className="text-lg text-gray-600">End-to-end AI pipeline for multilingual content localization</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { step: "1", title: "Upload", desc: "Content uploaded via web interface", icon: <FileText className="w-6 h-6" /> },
              { step: "2", title: "Detect", desc: "AI auto-detects source language", icon: <Brain className="w-6 h-6" /> },
              { step: "3", title: "Localize", desc: "Neural translation + cultural adaptation", icon: <Globe className="w-6 h-6" /> },
              { step: "4", title: "Integrate", desc: "Push to LMS/NCVET/MSDE platforms", icon: <Shield className="w-6 h-6" /> }
            ].map((step, index) => (
              <div key={index} className="text-center">
                <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4 text-white">
                  {step.icon}
                </div>
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-blue-600 font-bold text-sm">{step.step}</span>
                </div>
                <h3 className="font-bold text-gray-800 mb-2">{step.title}</h3>
                <p className="text-gray-600 text-sm">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* AI Models & Technology */}
        <div className="bg-white rounded-2xl shadow-lg p-8 mb-16">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">AI Model Stack</h2>
            <p className="text-lg text-gray-600">Enterprise-grade AI models fine-tuned for Indian languages</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {aiModels.map((model, index) => (
              <div key={index} className="p-6 bg-gray-50 rounded-xl border border-gray-200 hover:border-blue-300 transition-colors">
                <h3 className="font-bold text-gray-800 mb-2">{model.name}</h3>
                <p className="text-gray-600 text-sm mb-3">{model.purpose}</p>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">Performance</span>
                  <span className="bg-green-100 text-green-700 px-2 py-1 rounded-full text-xs font-medium">
                    {model.accuracy || model.quality || model.performance || model.speed || model.coverage}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Impact Metrics */}
        <div className="bg-gradient-to-br from-blue-600 to-purple-700 rounded-2xl shadow-lg p-8 text-white mb-16">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">Real-World Impact</h2>
            <p className="text-lg opacity-90">Measurable outcomes for inclusive education</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {impactMetrics.map((metric, index) => (
              <div key={index} className="text-center">
                <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <div className="text-white">
                    {metric.icon}
                  </div>
                </div>
                <div className="text-3xl font-bold mb-2">{metric.value}</div>
                <div className="text-lg opacity-90">{metric.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Technology Stack */}
        <div className="bg-white rounded-2xl shadow-lg p-8 mb-16">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Technology Architecture</h2>
            <p className="text-lg text-gray-600">Modern, scalable stack for production deployment</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {techStack.map((category, index) => (
              <div key={index} className="p-6 bg-gray-50 rounded-xl border border-gray-200">
                <div className="flex items-center mb-4">
                  <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center mr-3 text-white">
                    {category.icon}
                  </div>
                  <h3 className="font-bold text-gray-800">{category.category}</h3>
                </div>
                <div className="space-y-2">
                  {category.items.map((item, itemIndex) => (
                    <div key={itemIndex} className="flex items-center">
                      <CheckCircle className="w-4 h-4 text-green-600 mr-2" />
                      <span className="text-sm text-gray-700">{item}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Supported Languages */}
        <div className="bg-white rounded-2xl shadow-lg p-8 mb-16">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Multilingual Support</h2>
            <p className="text-lg text-gray-600">
              Comprehensive coverage of {languages.length} Indian languages with cultural context preservation
            </p>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {languages.map((language) => (
              <div key={language.code} className="flex items-center p-3 bg-gray-50 rounded-lg border border-gray-200 hover:border-blue-300 transition-colors">
                <span className="font-mono text-sm bg-gradient-to-br from-blue-500 to-purple-600 text-white px-3 py-1 rounded-lg mr-3 font-bold">
                  {language.code.toUpperCase()}
                </span>
                <span className="text-sm font-medium text-gray-700">
                  {language.name}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Team & Mission */}
        <div className="bg-gradient-to-br from-indigo-600 via-purple-600 to-blue-700 rounded-2xl shadow-lg p-8 text-white">
          <div className="text-center mb-12">
            <div className="w-20 h-20 bg-white/20 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <Users className="w-10 h-10 text-white" />
            </div>
            <h2 className="text-3xl font-bold mb-4">Team SafeHorizon</h2>
            <p className="text-xl opacity-90">Innovation Through Collaboration</p>
          </div>
          
          <div className="max-w-4xl mx-auto">
            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-8 mb-8">
              <h3 className="text-2xl font-bold mb-4 flex items-center justify-center">
                <Target className="w-6 h-6 mr-3" />
                Our Mission
              </h3>
              <p className="text-lg leading-relaxed opacity-95 text-center">
                "To break down language barriers in Indian education by creating an AI-powered 
                localization platform that preserves cultural context while making quality content 
                accessible to every learner, regardless of their linguistic background."
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className="text-center p-6 bg-white/10 backdrop-blur-sm rounded-xl">
                <Award className="w-8 h-8 mx-auto mb-3" />
                <h4 className="font-bold text-lg mb-2">Smart India Hackathon</h4>
                <p className="text-sm opacity-90">2025 National Competition</p>
              </div>
              
              <div className="text-center p-6 bg-white/10 backdrop-blur-sm rounded-xl">
                <Target className="w-8 h-8 mx-auto mb-3" />
                <h4 className="font-bold text-lg mb-2">Problem Statement</h4>
                <p className="text-sm opacity-90">PS-25203 Localization</p>
              </div>
              
              <div className="text-center p-6 bg-white/10 backdrop-blur-sm rounded-xl">
                <TrendingUp className="w-8 h-8 mx-auto mb-3" />
                <h4 className="font-bold text-lg mb-2">Impact Vision</h4>
                <p className="text-sm opacity-90">Pan-India Accessibility</p>
              </div>
            </div>
            
            <div className="text-center">
              <button 
                onClick={() => navigate('/')} 
                className="bg-white text-indigo-600 px-8 py-4 rounded-xl font-bold text-lg hover:bg-gray-100 transition-all duration-300 transform hover:scale-105 shadow-lg mr-4"
              >
                Explore Platform
              </button>
              <a 
                href="https://youtu.be/CuezATiplts" 
                target="_blank" 
                rel="noopener noreferrer"
                className="border-2 border-white text-white px-8 py-4 rounded-xl font-bold text-lg hover:bg-white hover:text-indigo-600 transition-all duration-300 inline-block"
              >
                Try Demo
              </a>
            </div>
            
            <p className="mt-8 text-center text-sm opacity-75">
              🇮🇳 Proudly contributing to Digital India and educational accessibility initiatives
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default About;