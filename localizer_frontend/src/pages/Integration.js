import React, { useState, useEffect } from 'react';
import { ArrowLeft, Play, Copy, CheckCircle, AlertCircle, Loader, Terminal, Code, Video, ChevronRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { apiService } from '../utils/apiService';

const Integration = () => {
  const [results, setResults] = useState({});
  const [isExecuting, setIsExecuting] = useState({});
  const [error, setError] = useState('');
  const [curlCommands, setCurlCommands] = useState({});
  const [copiedStates, setCopiedStates] = useState({});

  // Initialize CURL commands based on API documentation
  useEffect(() => {
    const defaultCurls = {
      health: `curl -X GET "http://localhost:8000/"`,
      languages: `curl -X GET "http://localhost:8000/supported-languages"`,
      upload: `curl -X POST "http://localhost:8000/content/upload" \\
  -F "file=@demo_book_english.pdf" \\
  -F "domain=general" \\
  -F "source_language=en"`,
      translate: `curl -X POST "http://localhost:8000/translate" \\
  -H "Content-Type: application/json" \\
  -d '{
    "text": "Welcome to our vocational training program",
    "source_language": "en",
    "target_languages": ["hi", "bn"],
    "domain": "education",
    "apply_localization": true
  }'`,
      integration_upload: `curl -X POST "http://localhost:8000/integration/upload" \\
  -F "file=@demo_book_hindi.pdf" \\
  -F "target_languages=hi,bn,ta" \\
  -F "content_type=document" \\
  -F "domain=general" \\
  -F "partner_id=NCVET_123" \\
  -F "priority=normal"`,
      integration_status: `curl -X GET "http://localhost:8000/integration/results/integration_12345"`,
      integration_download: `curl -X GET "http://localhost:8000/integration/download/integration_12345_hi.txt?partner_id=NCVET_123" \\
  --output translated_content.txt`
    };
    setCurlCommands(defaultCurls);
  }, []);

  // API endpoints for Integration Testing
  const apiEndpoints = [
    {
      id: 'health',
      name: 'Health Check',
      method: 'GET',
      endpoint: 'http://localhost:8000/',
      description: 'Check service health and system status',
      icon: <CheckCircle size={20} className="text-green-600" />
    },
    {
      id: 'languages',
      name: 'Supported Languages',
      method: 'GET',
      endpoint: 'http://localhost:8000/supported-languages',
      description: 'Get list of 22 Indian languages supported',
      icon: <Code size={20} className="text-blue-600" />
    },
    {
      id: 'upload',
      name: 'Upload File',
      method: 'POST',
      endpoint: 'http://localhost:8000/content/upload',
      description: 'Upload document with automatic text extraction',
      icon: <Terminal size={20} className="text-purple-600" />
    },
    {
      id: 'translate',
      name: 'Translate Content',
      method: 'POST',
      endpoint: 'http://localhost:8000/translate',
      description: 'Translate text to multiple Indian languages',
      icon: <Copy size={20} className="text-orange-600" />
    },
    {
      id: 'integration_upload',
      name: 'Integration Upload',
      method: 'POST',
      endpoint: 'http://localhost:8000/integration/upload',
      description: 'Upload to NCVET/MSDE/LMS platforms',
      icon: <Play size={20} className="text-indigo-600" />
    },
    {
      id: 'integration_status',
      name: 'Check Status',
      method: 'GET',
      endpoint: 'http://localhost:8000/integration/results/{job_id}',
      description: 'Get integration job status and results',
      icon: <Loader size={20} className="text-teal-600" />
    },
    {
      id: 'integration_download',
      name: 'Download Result',
      method: 'GET',
      endpoint: 'http://localhost:8000/integration/download/{job_id}/{language}/{filename}',
      description: 'Download processed files from integration',
      icon: <ArrowLeft size={20} className="text-red-600" />
    }
  ];

  // Update CURL command
  const updateCurlCommand = (endpointId, newCurl) => {
    setCurlCommands(prev => ({
      ...prev,
      [endpointId]: newCurl
    }));
  };

  // Execute custom CURL command
  const executeCurl = async (endpoint) => {
    setIsExecuting(prev => ({ ...prev, [endpoint.id]: true }));
    setError('');
    
    try {
      const curlCommand = curlCommands[endpoint.id];
      console.log(`🚀 Executing custom CURL: ${curlCommand}`);
      
      // Parse CURL command to extract URL and method
      const urlMatch = curlCommand.match(/curl\s+-X\s+(\w+)\s+"([^"]+)"/);
      if (!urlMatch) {
        throw new Error('Invalid CURL command format');
      }
      
      const method = urlMatch[1].toLowerCase();
      const url = urlMatch[2];
      
      // Extract headers and data from CURL command
      const headers = {};
      const headerMatches = curlCommand.matchAll(/-H\s+"([^"]+)"/g);
      for (const match of headerMatches) {
        const [key, value] = match[1].split(': ');
        headers[key] = value;
      }
      
      // Extract JSON data
      let data = null;
      const dataMatch = curlCommand.match(/-d\s+'([^']+)'/);
      if (dataMatch) {
        try {
          data = JSON.parse(dataMatch[1]);
        } catch (e) {
          data = dataMatch[1];
        }
      }
      
      // Extract form data
      const formData = new FormData();
      const formMatches = curlCommand.matchAll(/-F\s+"([^"]+)"/g);
      for (const match of formMatches) {
        const [key, value] = match[1].split('=');
        if (value.startsWith('@')) {
          // Handle file uploads - create a sample file
          const filename = value.substring(1);
          const sampleText = "Sample file content for testing";
          const blob = new Blob([sampleText], { type: 'text/plain' });
          const file = new File([blob], filename, { type: 'text/plain' });
          formData.append(key, file);
        } else {
          formData.append(key, value);
        }
      }
      
      // Make the request using axios directly
      let result;
      const config = { headers };
      
      // Import axios for direct API calls
      const axios = (await import('axios')).default;
      
      if (formData.entries().next().done === false) {
        // Has form data
        result = await axios[method](url, formData, config);
      } else if (data) {
        // Has JSON data
        result = await axios[method](url, data, config);
      } else {
        // Simple request
        result = await axios[method](url, config);
      }
      
      setResults(prev => ({
        ...prev,
        [endpoint.id]: {
          success: true,
          data: result.data || result,
          timestamp: new Date().toLocaleTimeString()
        }
      }));
      
      console.log(`✅ ${endpoint.name} completed:`, result);
    } catch (error) {
      console.error(`❌ ${endpoint.name} failed:`, error);
      setResults(prev => ({
        ...prev,
        [endpoint.id]: {
          success: false,
          error: error.response?.data?.message || error.message || 'Request failed',
          timestamp: new Date().toLocaleTimeString()
        }
      }));
    } finally {
      setIsExecuting(prev => ({ ...prev, [endpoint.id]: false }));
    }
  };

  // Copy CURL to clipboard
  const copyCurl = async (curlCommand, endpointId) => {
    try {
      await navigator.clipboard.writeText(curlCommand);
      setCopiedStates(prev => ({ ...prev, [endpointId]: true }));
      setTimeout(() => {
        setCopiedStates(prev => ({ ...prev, [endpointId]: false }));
      }, 2000);
    } catch (err) {
      console.error('❌ Failed to copy CURL:', err);
    }
  };

  return (
    <div className="min-h-screen" style={{backgroundColor: '#fff7ed'}}>
      {/* Header */}
      <div className="bg-white shadow-sm" style={{borderBottom: '3px solid #004aad'}}>
        <div className="container py-8">
          <div className="flex items-center justify-between mb-6">
            <Link to="/" className="btn-secondary inline-flex items-center gap-2 hover:bg-gray-100 transition-colors">
              <ArrowLeft size={20} />
              Back to Home
            </Link>
            <div className="px-4 py-2 rounded-xl flex items-center gap-2 bg-blue-50 border-2 border-blue-200">
              <Terminal size={18} className="text-blue-600" />
              <span className="text-blue-800 font-semibold">Live API Testing</span>
            </div>
          </div>
          
          <div className="text-center max-w-5xl mx-auto">
            <h1 className="text-5xl font-bold mb-4" style={{color: '#004aad'}}>
              API Integration
            </h1>
            <p className="text-xl mb-6 text-gray-600 leading-relaxed">
              Test and explore AI-Powered Multilingual Content Localization APIs with interactive CURL commands.
              Upload, translate, and integrate with NCVET, MSDE platforms.
            </p>
            <div className="flex flex-wrap justify-center gap-4 text-sm">
              <div className="px-4 py-2 bg-green-100 text-green-800 rounded-full font-medium">
                ✓ 22 Indian Languages
              </div>
              <div className="px-4 py-2 bg-blue-100 text-blue-800 rounded-full font-medium">
                ✓ Real-time Translation
              </div>
              <div className="px-4 py-2 bg-purple-100 text-purple-800 rounded-full font-medium">
                ✓ Platform Integration
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container py-8">
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

        {/* Error Display */}
        {error && (
          <div className="mb-8 p-6 bg-red-50 border border-red-200 rounded-xl">
            <div className="flex items-center">
              <AlertCircle className="h-6 w-6 text-red-500 mr-3" />
              <span className="text-red-700 font-medium">{error}</span>
            </div>
        </div>
        )}

        {/* API Endpoints */}
        <div className="grid gap-6">
          {apiEndpoints.map((endpoint) => (
            <div key={endpoint.id} className="bg-white rounded-2xl shadow-lg border border-gray-100 hover:shadow-xl transition-all duration-300">
              {/* API Header */}
              <div className="p-6 border-b border-gray-100">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-4 mb-3">
                      {endpoint.icon}
                      <div className="flex items-center gap-3">
                        <span className={`px-3 py-1 rounded-full text-xs font-bold text-white ${
                          endpoint.method === 'GET' ? 'bg-green-500' : 'bg-blue-500'
                        }`}>
                          {endpoint.method}
                        </span>
                        <h3 className="text-xl font-bold text-gray-900">
                          {endpoint.name}
                        </h3>
                      </div>
                    </div>
                    <p className="text-sm font-mono text-blue-600 bg-blue-50 p-2 rounded-lg mb-2">
                      {endpoint.endpoint}
                    </p>
                    <p className="text-gray-600">
                      {endpoint.description}
                    </p>
                  </div>
                  <div className="flex gap-2 ml-4">
                    <button
                      onClick={() => copyCurl(curlCommands[endpoint.id] || '', endpoint.id)}
                      className={`p-3 rounded-xl transition-all duration-200 ${
                        copiedStates[endpoint.id] 
                          ? 'bg-green-100 text-green-600' 
                          : 'bg-gray-100 hover:bg-gray-200 text-gray-600'
                      }`}
                      title={copiedStates[endpoint.id] ? 'Copied!' : 'Copy CURL'}
                    >
                      {copiedStates[endpoint.id] ? (
                        <CheckCircle size={18} />
                      ) : (
                        <Copy size={18} />
                      )}
                    </button>
                    <button
                      onClick={() => executeCurl(endpoint)}
                      disabled={isExecuting[endpoint.id] || !curlCommands[endpoint.id]}
                      className="btn-primary flex items-center gap-2 px-4 py-3 disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105 transition-transform"
                    >
                      {isExecuting[endpoint.id] ? (
                        <>
                          <Loader size={18} className="animate-spin" />
                          Running...
                        </>
                      ) : (
                        <>
                          <Play size={18} />
                          Execute
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>

              {/* Editable CURL Command */}
              <div className="p-6 pt-0">
                <div className="mb-4">
                  <label className="flex items-center gap-2 text-sm font-semibold mb-3 text-gray-700">
                    <Terminal size={16} />
                    CURL Command
                  </label>
                  <div className="relative">
                    <textarea
                      value={curlCommands[endpoint.id] || ''}
                      onChange={(e) => updateCurlCommand(endpoint.id, e.target.value)}
                      className="w-full p-4 bg-gray-900 text-green-400 text-sm font-mono rounded-xl border-2 border-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                      rows={8}
                      placeholder="Enter your CURL command here..."
                    />
                    <div className="absolute top-2 right-2 text-xs text-gray-500 bg-gray-800 px-2 py-1 rounded">
                      BASH
                    </div>
                  </div>
                </div>

                {/* Results */}
                {results[endpoint.id] && (
                  <div className="mt-6">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Terminal size={16} className="text-gray-600" />
                        <span className="font-semibold text-gray-700">
                          Response
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${
                          results[endpoint.id].success ? 'bg-green-500' : 'bg-red-500'
                        }`}></div>
                        <span className="text-xs text-gray-500">
                          {results[endpoint.id].timestamp}
                        </span>
                      </div>
                    </div>
                    <div className={`p-4 rounded-xl border-2 ${
                      results[endpoint.id].success 
                        ? 'bg-green-50 border-green-200' 
                        : 'bg-red-50 border-red-200'
                    }`}>
                      {results[endpoint.id].success ? (
                        <div>
                          <div className="flex items-center gap-2 mb-2">
                            <CheckCircle size={16} className="text-green-600" />
                            <span className="text-green-800 font-medium text-sm">Success</span>
                          </div>
                          <pre className="text-sm overflow-x-auto text-green-900 bg-white p-3 rounded-lg border">
                            {JSON.stringify(results[endpoint.id].data, null, 2)}
                          </pre>
                        </div>
                      ) : (
                        <div>
                          <div className="flex items-center gap-2 mb-2">
                            <AlertCircle size={16} className="text-red-600" />
                            <span className="text-red-800 font-medium text-sm">Error</span>
                          </div>
                          <div className="text-red-700 text-sm bg-white p-3 rounded-lg border">
                            {results[endpoint.id].error}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Integration;
