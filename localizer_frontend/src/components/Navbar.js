import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Home, 
  FileText, 
  Mic, 
  Video, 
  Building2, 
  Info, 
  Menu, 
  X,
  Globe,
  Zap,
  ChevronRight
} from 'lucide-react';

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();

  const navigation = [
    { name: 'Home', href: '/', icon: Home },
    { name: 'Document Translation', href: '/document', icon: FileText },
    { name: 'Audio Localization', href: '/audio', icon: Mic },
    { name: 'Video Localization', href: '/video', icon: Video },
    { name: 'Integration', href: '/integration', icon: Building2 },
    { name: 'About', href: '/about', icon: Info },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="bg-white shadow-lg sticky top-0 z-50" style={{borderBottom: '3px solid #FF9933'}}>
      <div className="container">
        <div className="flex justify-between items-center h-16">
          {/* Enhanced Logo */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-3 group">
              <div className="relative">
                <div className="w-10 h-10 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform duration-300" 
                     style={{backgroundColor: '#FF9933'}}>
                  <Globe className="w-6 h-6 text-white" />
                </div>
                <div className="absolute -top-1 -right-1 w-3 h-3 rounded-full animate-pulse" 
                     style={{backgroundColor: '#138808'}}></div>
              </div>
              <div className="hidden sm:block">
                <div className="flex flex-col">
                  <span className="text-xl font-bold group-hover:scale-105 transition-transform" style={{color: '#000080'}}>
                    SafeHorizon
                  </span>
                  <span className="text-xs font-medium -mt-0.5" style={{color: '#FF9933'}}>
                    AI Localization Engine
                  </span>
                </div>
              </div>
            </Link>
          </div>

          {/* Professional Desktop Navigation */}
          <div className="hidden lg:block">
            <div className="flex items-center space-x-2">
              {navigation.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.href);
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`group relative px-4 py-2.5 rounded-xl text-sm font-semibold transition-all duration-300 flex items-center space-x-2 ${
                      active
                        ? 'text-white shadow-lg'
                        : 'hover:shadow-md'
                    }`}
                    style={active ? 
                      {backgroundColor: '#FF9933'} : 
                      {color: '#000080'}}
                    onMouseEnter={(e) => {
                      if (!active) {
                        e.target.style.backgroundColor = '#fff7ed';
                        e.target.style.color = '#FF9933';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!active) {
                        e.target.style.backgroundColor = 'transparent';
                        e.target.style.color = '#000080';
                      }
                    }}
                  >
                    <Icon className={`w-4 h-4 ${active ? 'text-white' : 'group-hover:scale-110 transition-transform duration-300'}`} />
                    <span>{item.name}</span>
                    {active && (
                      <Zap className="w-3 h-3 text-white/80" />
                    )}
                    
                    {/* Active indicator */}
                    {active && (
                      <div className="absolute -bottom-2 left-1/2 transform -translate-x-1/2 w-1 h-1 bg-white rounded-full"></div>
                    )}
                  </Link>
                );
              })}
            </div>
          </div>

          {/* Mobile/Tablet Navigation Toggle */}
          <div className="lg:hidden">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="p-2.5 rounded-xl text-gray-600 hover:text-blue-600 hover:bg-blue-50 transition-all duration-300 hover:scale-110"
            >
              {isOpen ? (
                <X className="h-6 w-6" />
              ) : (
                <Menu className="h-6 w-6" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Enhanced Mobile/Tablet Navigation */}
      {isOpen && (
        <div className="lg:hidden">
          <div className="px-6 py-4 space-y-2 bg-white/95 backdrop-blur-md border-t border-gray-200/50 shadow-lg">
            <div className="mb-4 pb-4 border-b border-gray-200">
              <h3 className="text-sm font-bold text-gray-900 mb-1">Navigation Menu</h3>
              <p className="text-xs text-gray-500">AI-Powered Localization Platform</p>
            </div>
            
            {navigation.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.href);
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`group flex items-center justify-between px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-300 ${
                    active
                      ? 'bg-blue-gradient text-white shadow-lg'
                      : 'text-gray-700 hover:text-blue-600 hover:bg-blue-50/80 active:scale-95'
                  }`}
                  onClick={() => setIsOpen(false)}
                >
                  <div className="flex items-center space-x-3">
                    <div className={`p-2 rounded-lg ${
                      active 
                        ? 'bg-white/20' 
                        : 'bg-gray-100 group-hover:bg-blue-100'
                    }`}>
                      <Icon className={`w-4 h-4 ${
                        active 
                          ? 'text-white' 
                          : 'text-gray-600 group-hover:text-blue-600'
                      }`} />
                    </div>
                    <span>{item.name}</span>
                  </div>
                  
                  <ChevronRight className={`w-4 h-4 ${
                    active 
                      ? 'text-white/80' 
                      : 'text-gray-400 group-hover:text-blue-600'
                  } transition-transform duration-300 group-hover:translate-x-1`} />
                </Link>
              );
            })}
            
            {/* Mobile Footer */}
            <div className="mt-6 pt-4 border-t border-gray-200">
              <div className="text-center">
                <p className="text-xs text-gray-500 mb-2">Smart India Hackathon 2025</p>
                <div className="flex items-center justify-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-xs font-medium text-gray-600">System Online</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;



