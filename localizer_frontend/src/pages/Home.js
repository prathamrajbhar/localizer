import React from 'react';
import { Link } from 'react-router-dom';
import { 
  FileText, 
  Volume2, 
  Video, 
  Globe, 
  BookOpen,
  Zap,
  Shield,
  Users,
  Award,
  ChevronRight,
  ArrowRight,
  CheckCircle,
  Star,
  AlertCircle
} from 'lucide-react';

const Home = () => {
  const features = [
    {
      icon: <FileText size={24} />,
      title: "Document Translation",
      description: "Translate PDFs, Word docs, and text files with 99% accuracy",
      link: "/document"
    },
    {
      icon: <Volume2 size={24} />,
      title: "Audio Localization",
      description: "Convert speech to multiple languages with natural voice",
      link: "/audio"
    },
    {
      icon: <Video size={24} />,
      title: "Video Localization",
      description: "Generate subtitles and professional dubbing",
      link: "/video"
    },
    {
      icon: <Globe size={24} />,
      title: "Platform Integration",
      description: "Seamless LMS, NCVET, and MSDE connectivity",
      link: "/integration"
    }
  ];

  const stats = [
    { number: "22+", label: "Languages Supported", description: "Including all major Indian languages" },
    { number: "99.2%", label: "Translation Accuracy", description: "Industry-leading precision" },
    { number: "< 5s", label: "Processing Time", description: "Lightning-fast results" },
    { number: "3", label: "Content Types", description: "Text, Audio, and Video" }
  ];

  const benefits = [
    {
      icon: <Zap style={{color: '#FF9933'}} size={24} />,
      title: "Lightning Fast",
      description: "Process content in seconds, not hours"
    },
    {
      icon: <Shield style={{color: '#138808'}} size={24} />,
      title: "Enterprise Security",
      description: "Bank-grade encryption and data protection"
    },
    {
      icon: <CheckCircle style={{color: '#000080'}} size={24} />,
      title: "Guaranteed Quality",
      description: "AI-verified translations with human-level accuracy"
    },
    {
      icon: <Star style={{color: '#FF9933'}} size={24} />,
      title: "24/7 Support",
      description: "Round-the-clock technical assistance"
    }
  ];

  const integrations = [
    {
      name: "Learning Management Systems",
      logo: <BookOpen style={{color: '#000080'}} size={32} />,
      description: "Seamless integration with popular LMS platforms"
    },
    {
      name: "NCVET Platform",
      logo: <Award style={{color: '#138808'}} size={32} />,
      description: "Direct connectivity to National Council for Vocational Education"
    },
    {
      name: "MSDE Systems",
      logo: <Users style={{color: '#FF9933'}} size={32} />,
      description: "Ministry of Skill Development and Entrepreneurship alignment"
    }
  ];

  return (
    <div className="min-h-screen" style={{backgroundColor: '#fff7ed'}}>
      {/* Hero Section */}
      <div className="bg-white py-16 border-b-4" style={{borderColor: '#FF9933'}}>
        <div className="container">
          <div className="text-center">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium mb-8" 
                 style={{backgroundColor: '#fff7ed', border: '2px solid #FF9933', color: '#000080'}}>
              <Award size={16} className="text-orange-500" />
              <span className="font-bold">Smart India Hackathon 2025</span>
            </div>
            
            {/* Main Heading */}
            <h1 className="text-4xl md:text-6xl font-bold mb-6 max-w-4xl mx-auto" style={{color: '#000080'}}>
              AI-Powered Multilingual
              <span className="block mt-2" style={{color: '#FF9933'}}>
                Content Localization Engine
              </span>
            </h1>
            
            {/* Subtitle */}
            <p className="text-xl max-w-3xl mx-auto mb-8" style={{color: '#4b5563'}}>
              Transform educational content across 22+ languages with AI. 
              Translate documents, localize audio, generate video subtitles, and integrate 
              with LMS, NCVET, and MSDE platforms.
            </p>
            
            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12">
              <Link to="/document" className="btn-primary inline-flex items-center gap-2">
                <FileText size={20} />
                Start Translating
                <ArrowRight size={20} />
              </Link>
              
              <a 
                href="https://youtu.be/CuezATiplts" 
                target="_blank" 
                rel="noopener noreferrer"
                className="btn-secondary inline-flex items-center gap-2"
              >
                <Video size={20} />
                View Demo
                <ChevronRight size={20} />
              </a>
            </div>

            {/* Demo Video Notice */}
            <div className="max-w-2xl mx-auto mb-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <Video className="h-5 w-5 text-blue-600 mt-0.5" />
                </div>
                <div className="ml-3">
                  <p className="text-sm text-blue-800">
                    <strong>Note:</strong> We're currently running on CPU processing as we can't afford GPU servers yet. Some features may take longer or occasionally not work. Watch our demo video to see the full potential!
                  </p>
                  <div className="mt-3">
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

            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 max-w-4xl mx-auto">
              {stats.map((stat, index) => (
                <div key={index} className="text-center p-4 rounded-lg" 
                     style={{backgroundColor: '#fff7ed', border: '1px solid #FFB366'}}>
                  <div className="text-3xl font-bold mb-2" style={{color: '#FF9933'}}>{stat.number}</div>
                  <div className="font-semibold mb-1" style={{color: '#000080'}}>{stat.label}</div>
                  <div className="text-sm" style={{color: '#4b5563'}}>{stat.description}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="py-16 bg-white">
        <div className="container">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold mb-4" style={{color: '#000080'}}>Complete Localization Solution</h2>
            <p className="text-lg max-w-3xl mx-auto" style={{color: '#4b5563'}}>
              Everything you need to make your content accessible across languages and platforms
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <Link
                key={index}
                to={feature.link}
                className="card text-center hover:shadow-xl transition-all duration-300 hover:scale-105"
                style={{borderColor: '#FFB366', backgroundColor: '#fff'}}
              >
                <div className="w-16 h-16 rounded-lg flex items-center justify-center mx-auto mb-4" 
                     style={{backgroundColor: '#fff7ed', color: '#FF9933'}}>
                  {feature.icon}
                </div>
                <h3 className="text-lg font-bold mb-2" style={{color: '#000080'}}>
                  {feature.title}
                </h3>
                <p className="mb-4" style={{color: '#4b5563'}}>
                  {feature.description}
                </p>
                <div className="inline-flex items-center font-medium text-sm" style={{color: '#FF9933'}}>
                  <span>Try Now</span>
                  <ChevronRight size={16} className="ml-1" />
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* Benefits Section */}
      <div className="py-16" style={{backgroundColor: '#fff7ed'}}>
        <div className="container">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold mb-4" style={{color: '#000080'}}>Why Choose Our Platform</h2>
            <p className="text-lg max-w-3xl mx-auto" style={{color: '#4b5563'}}>
              Built with cutting-edge AI technology and designed for enterprise-level performance
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {benefits.map((benefit, index) => (
              <div key={index} className="card text-center" style={{borderColor: '#FFB366', backgroundColor: '#fff'}}>
                <div className="w-12 h-12 flex items-center justify-center mx-auto mb-4 rounded-lg" 
                     style={{backgroundColor: '#fff7ed'}}>
                  {benefit.icon}
                </div>
                <h3 className="font-bold mb-2" style={{color: '#000080'}}>{benefit.title}</h3>
                <p className="text-sm" style={{color: '#4b5563'}}>{benefit.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Integration Section */}
      <div className="py-16 bg-white">
        <div className="container">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold mb-4" style={{color: '#000080'}}>Platform Integration</h2>
            <p className="text-lg max-w-3xl mx-auto" style={{color: '#4b5563'}}>
              Connect seamlessly with India's leading educational and skill development platforms
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {integrations.map((integration, index) => (
              <div key={index} className="card text-center hover:shadow-lg transition-shadow" 
                   style={{borderColor: '#FFB366', backgroundColor: '#fff'}}>
                <div className="w-16 h-16 rounded-lg flex items-center justify-center mx-auto mb-4" 
                     style={{backgroundColor: '#fff7ed'}}>
                  {integration.logo}
                </div>
                <h3 className="text-lg font-bold mb-2" style={{color: '#000080'}}>{integration.name}</h3>
                <p style={{color: '#4b5563'}}>{integration.description}</p>
              </div>
            ))}
          </div>

          <div className="text-center mt-8">
            <Link to="/integration" className="btn-primary inline-flex items-center gap-2">
              <FileText size={20} />
              View API Documentation
            </Link>
          </div>
        </div>
      </div>

      {/* Final CTA Section */}
      <div className="py-16 text-white" style={{backgroundColor: '#FF9933'}}>
        <div className="container">
          <div className="text-center">
            <h2 className="text-3xl md:text-4xl font-bold mb-4 text-white">Ready to Transform Your Content?</h2>
            <p className="text-lg mb-8" style={{color: '#fff7ed'}}>
              Join thousands of educators and organizations already using our AI localization platform
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Link 
                to="/document" 
                className="bg-white hover:bg-gray-100 px-6 py-3 rounded-lg font-semibold transition-colors inline-flex items-center gap-2"
                style={{color: '#000080'}}
              >
                <FileText size={20} />
                Get Started Free
                <ArrowRight size={20} />
              </Link>
              
              <Link 
                to="/about" 
                className="border-2 border-white text-white hover:bg-white px-6 py-3 rounded-lg font-semibold transition-colors inline-flex items-center gap-2"
                style={{'--hover-color': '#000080'}}
                onMouseEnter={(e) => e.target.style.color = '#000080'}
                onMouseLeave={(e) => e.target.style.color = 'white'}
              >
                <BookOpen size={20} />
                Learn More
                <ChevronRight size={20} />
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Footer Credit */}
      <div className="py-12 text-white" style={{backgroundColor: '#000080'}}>
        <div className="container">
          <div className="text-center">
            <div className="flex items-center justify-center gap-3 mb-4">
              <Award style={{color: '#FF9933'}} size={28} />
              <h3 className="text-2xl font-bold text-white">Team SafeHorizon</h3>
            </div>
            <p className="text-lg mb-2" style={{color: '#FFB366'}}>Smart India Hackathon 2025</p>
            <p className="text-sm" style={{color: '#fff7ed'}}>
              Problem Statement ID: 25203 • AI-Powered Multilingual Content Localization Engine
            </p>
            <div className="mt-4 flex justify-center gap-1">
              <div className="w-6 h-4" style={{backgroundColor: '#FF9933'}}></div>
              <div className="w-6 h-4 bg-white"></div>
              <div className="w-6 h-4" style={{backgroundColor: '#138808'}}></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;
