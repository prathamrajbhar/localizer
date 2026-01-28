import React, { useState } from 'react';
import { Building2, Upload, Download, CheckCircle, Terminal, Database, AlertCircle, Loader, ArrowLeft, Globe, Zap, Link as LinkIcon, Code, Settings, Play, Copy, RefreshCw, FileText, Mic, Video } from 'lucide-react';
import { Link } from 'react-router-dom';
import { apiService } from '../utils/apiService';

const Integration = () => {
  const [file, setFile] = useState(null);
  const [platform, setPlatform] = useState('NCVET');
  const [targetLang, setTargetLang] = useState('hi');
  const [uploadResult, setUploadResult] = useState(null);
  const [statusResult, setStatusResult] = useState(null);
  const [downloadResult, setDownloadResult] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isCheckingStatus, setIsCheckingStatus] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [error, setError] = useState('');


  // Handle file upload for integration
  const handleFileUpload = (e) => {
    const uploadedFile = e.target.files[0];
    if (uploadedFile) {
      setFile(uploadedFile);
      setError('');
    }
  };

  // Real API upload to integration endpoint
  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }
    
    setIsUploading(true);
    setError('');
    setUploadResult(null);

    try {
      const response = await apiService.integrationUpload(
        file,
        [targetLang],
        'document',
        'general',
        `${platform.toLowerCase()}_partner_123`,
        'normal'
      );
      
      setUploadResult(response);
    } catch (err) {
      setError('Upload failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsUploading(false);
    }
  };

  // Check integration status
  const handleCheckStatus = async () => {
    if (!uploadResult?.job_id) {
      setError('No job ID available. Please upload a file first.');
      return;
    }

    setIsCheckingStatus(true);
    setError('');

    try {
      const response = await apiService.getIntegrationResults(uploadResult.job_id);
      setStatusResult(response);
    } catch (err) {
      setError('Status check failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsCheckingStatus(false);
    }
  };

  // Download integration results
  const handleDownload = async () => {
    if (!uploadResult?.job_id) {
      setError('No job ID available for download');
      return;
    }

    setIsDownloading(true);
    setError('');

    try {
      const downloadFilename = `${uploadResult.job_id}_${targetLang}.txt`;
      
      const response = await apiService.downloadIntegrationOutput(uploadResult.job_id, targetLang, downloadFilename);
      
      // Create and download the file
      const url = window.URL.createObjectURL(response);
      const link = document.createElement('a');
      link.href = url;
      link.download = downloadFilename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      setDownloadResult({
        job_id: uploadResult.job_id,
        status: 'Downloaded',
        download_url: downloadFilename,
        completion_time: new Date().toISOString()
      });
    } catch (err) {
      setError('Download failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsDownloading(false);
    }
  };

  // Generate CURL command
  const generateCurlCommand = (action) => {
    const baseUrl = process.env.REACT_APP_API_URL || 'https://api.safehorizon.com';
    
    switch (action) {
      case 'upload':
        return `curl -X POST ${baseUrl}/integration/upload \\
  -F "file=@document.pdf" \\
  -F "target_language=hi" \\
  -F "partner=NCVET"`;
      
      case 'status':
        return `curl -X GET ${baseUrl}/integration/status \\
  -H "Content-Type: application/json"`;
      
      case 'download':
        return `curl -X GET "${baseUrl}/integration/download/NCVET_1234/hi/document.pdf" \\
  -H "Accept: application/octet-stream" \\
  --output document.pdf`;
      
      default:
        return '';
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Professional Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="container py-8">
          <div className="flex items-center justify-between mb-6">
            <button className="btn-secondary flex items-center">
              <ArrowLeft size={20} className="mr-2" />
              Back to Dashboard
            </button>
          </div>
          
          <div className="max-w-4xl">
            <div className="flex items-start">
              <div className="icon-container-lg bg-orange-gradient mr-6">
                <Building2 size={32} className="text-white" />
              </div>
              
              <div>
                <h1 className="text-4xl font-bold mb-4 text-gray-900">
                  Enterprise Platform Integration
                </h1>
                <p className="text-lg text-gray-600 max-w-3xl mb-6">
                  Seamlessly integrate with LMS, NCVET, and MSDE platforms for automated 
                  multilingual content delivery across enterprise education systems.
                </p>
                
                <div className="flex flex-wrap items-center gap-4">
                  <div className="badge-enterprise">
                    <Terminal size={16} className="mr-2" />
                    REST API Integration
                  </div>
                  <div className="badge-enterprise">
                    <Globe size={16} className="mr-2" />
                    22+ Languages Supported
                  </div>
                  <div className="badge-enterprise">
                    <Zap size={16} className="mr-2" />
                    Real-time Processing
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container py-12">

        {/* Error Display */}
        {error && (
          <div className="mb-8 p-6 bg-red-50 border border-red-200 rounded-xl">
            <div className="flex items-center">
              <AlertCircle className="h-6 w-6 text-red-500 mr-3" />
              <span className="text-red-700 font-medium">{error}</span>
            </div>
          </div>
        )}

        {/* Platform Configuration & File Upload */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
          <div className="card">
            <h2 className="text-2xl font-bold mb-8 flex items-center text-gray-900">
              <Settings className="mr-3 text-orange-600" size={28} />
              Platform Configuration
            </h2>

            {/* Platform Selection */}
            <div className="">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Building2 className="w-4 h-4 inline mr-2" />
                Target Platform
              </label>
              <select
                value={platform}
                onChange={(e) => setPlatform(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {SUPPORTED_PLATFORMS.map(platform => (
                  <option key={platform.id} value={platform.id.toUpperCase()}>
                    {platform.name} - {platform.description}
                  </option>
                ))}
              </select>
            </div>

            {/* Language Selection */}
            <div className="">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Globe className="w-4 h-4 inline mr-2" />
                Target Language
              </label>
              <select
                value={targetLang}
                onChange={(e) => setTargetLang(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="hi">Hindi (hi)</option>
                <option value="bn">Bengali (bn)</option>
                <option value="ta">Tamil (ta)</option>
                <option value="te">Telugu (te)</option>
                <option value="gu">Gujarati (gu)</option>
              </select>
            </div>

            {/* File Upload */}
            <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-orange-500 hover:bg-orange-50/30 transition-all duration-300 group">
              <input
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={handleFileUpload}
                className="hidden"
                id="integration-upload"
              />
              <label
                htmlFor="integration-upload"
                className="cursor-pointer flex flex-col items-center"
              >
                <div className="w-16 h-16 bg-orange-100 rounded-2xl flex items-center justify-center mb-4 group-hover:bg-orange-200 transition-colors">
                  <Database className="w-8 h-8 text-orange-600" />
                </div>
                <p className="text-lg font-semibold text-gray-700 mb-2">
                  Upload Integration Content
                </p>
                <p className=" text-gray-500 mb-4">
                  Select files for platform integration
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-gray-400">
                  <p>• PDF Documents</p>
                  <p>• Word Files (.docx)</p>
                  <p>• Text Files (.txt)</p>
                  <p>• Enterprise Ready</p>
                </div>
              </label>
            </div>

            {file && (
              <div className="mt-8 p-6 bg-orange-50 rounded-xl border border-orange-200">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center mb-2">
                      <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
                      <p className="font-semibold text-gray-800">{file.name}</p>
                    </div>
                    <p className="text-sm text-gray-500 mb-3">
                      <span className="font-medium">Ready for:</span> {platform} Platform Integration
                    </p>
                    
                    <div className="flex items-center p-3 bg-green-100 border border-green-300 rounded-lg">
                      <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
                      <span className="text-sm font-medium text-green-700">
                        File validated for platform upload
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* API Integration Demo */}
          <div className="card">
            <h2 className="text-2xl font-bold mb-8 flex items-center text-gray-900">
              <Code className="mr-3 text-orange-600" size={28} />
              Live API Integration
            </h2>

            <div className="space-y-6">
              {/* Upload Section */}
              <div className="p-6 border border-gray-200 rounded-xl bg-gray-50">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-bold text-gray-800 flex items-center">
                    <span className="w-8 h-8 bg-orange-600 text-white rounded-lg flex items-center justify-center text-sm font-bold mr-3">1</span>
                    Upload to Platform
                  </h3>
                  <div className="badge-success">POST</div>
                </div>
                
                <div className="bg-gray-900 text-green-400 p-4 rounded-lg text-sm font-mono mb-4 overflow-x-auto">
                  <div className="text-gray-400 mb-2"># Upload content to platform</div>
                  {generateCurlCommand('upload')}
                </div>
                
                <button
                  onClick={handleUpload}
                  disabled={!file || isUploading}
                  className="btn-primary w-full"
                >
                  {isUploading ? (
                    <>
                      <Loader className="w-5 h-5 animate-spin mr-2" />
                      Uploading to {platform}...
                    </>
                  ) : (
                    <>
                      <Upload className="w-5 h-5 mr-2" />
                      Execute Upload API
                    </>
                  )}
                </button>
              </div>

              {/* Status Section */}
              <div className="p-6 border border-gray-200 rounded-xl bg-gray-50">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-bold text-gray-800 flex items-center">
                    <span className="w-8 h-8 bg-blue-600 text-white rounded-lg flex items-center justify-center text-sm font-bold mr-3">2</span>
                    Monitor Processing Status
                  </h3>
                  <div className="badge-info">GET</div>
                </div>
                
                <div className="bg-gray-900 text-green-400 p-4 rounded-lg text-sm font-mono mb-4 overflow-x-auto">
                  <div className="text-gray-400 mb-2"># Check processing status</div>
                  {generateCurlCommand('status')}
                </div>
                
                <button
                  onClick={handleCheckStatus}
                  disabled={isCheckingStatus || !uploadResult}
                  className="btn-secondary w-full"
                >
                  {isCheckingStatus ? (
                    <>
                      <Loader className="w-5 h-5 animate-spin mr-2" />
                      Checking Status...
                    </>
                  ) : (
                    <>
                      <Terminal className="w-5 h-5 mr-2" />
                      Check Status API
                    </>
                  )}
                </button>
              </div>

              {/* Download Section */}
              <div className="p-6 border border-gray-200 rounded-xl bg-gray-50">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-bold text-gray-800 flex items-center">
                    <span className="w-8 h-8 bg-green-600 text-white rounded-lg flex items-center justify-center text-sm font-bold mr-3">3</span>
                    Download Localized Content
                  </h3>
                  <div className="badge-success">GET</div>
                </div>
                
                <div className="bg-gray-900 text-green-400 p-4 rounded-lg text-sm font-mono mb-4 overflow-x-auto">
                  <div className="text-gray-400 mb-2"># Download processed files</div>
                  {generateCurlCommand('download')}
                </div>
                
                <button
                  onClick={handleDownload}
                  disabled={isDownloading || !uploadResult}
                  className="btn-primary w-full"
                >
                  {isDownloading ? (
                    <>
                      <Loader className="w-5 h-5 animate-spin mr-2" />
                      Downloading...
                    </>
                  ) : (
                    <>
                      <Download className="w-5 h-5 mr-2" />
                      Download Result API
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* API Response Display */}
        {(uploadResult || statusResult || downloadResult) && (
          <div className="mb-12">
            <h2 className="text-2xl font-bold mb-8 text-gray-900 flex items-center">
              <Terminal className="mr-3 text-blue-600" size={28} />
              Live API Responses
            </h2>
            
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Upload Response */}
              {uploadResult && (
                <div className="card">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-lg font-bold text-gray-800">
                      Upload Response
                    </h3>
                    <div className="badge-success">200 OK</div>
                  </div>
                  <div className="bg-gray-900 rounded-lg p-4 overflow-hidden">
                    <pre className="text-green-400 text-sm overflow-x-auto font-mono">
{JSON.stringify(uploadResult, null, 2)}
                    </pre>
                  </div>
                </div>
              )}

              {/* Status Response */}
              {statusResult && (
                <div className="card">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-lg font-bold text-gray-800">
                      Status Response
                    </h3>
                    <div className="badge-info">200 OK</div>
                  </div>
                  <div className="bg-gray-900 rounded-lg p-4 overflow-hidden">
                    <pre className="text-blue-400 text-sm overflow-x-auto font-mono">
{JSON.stringify(statusResult, null, 2)}
                    </pre>
                  </div>
                </div>
              )}

              {/* Download Response */}
              {downloadResult && (
                <div className="card">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-lg font-bold text-gray-800">
                      Download Response
                    </h3>
                    <div className="badge-success">200 OK</div>
                  </div>
                  <div className="bg-gray-900 rounded-lg p-4 overflow-hidden">
                    <pre className="text-green-400 text-sm overflow-x-auto font-mono">
{JSON.stringify(downloadResult, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Integration Workflow */}
        <div className="card">
          <h2 className="text-2xl font-bold mb-8 text-gray-900 flex items-center">
            <Link className="mr-3 text-purple-600" size={28} />
            Enterprise Integration Workflow
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center group">
              <div className="relative mb-6">
                <div className="w-20 h-20 bg-orange-gradient rounded-2xl flex items-center justify-center mx-auto shadow-lg group-hover:scale-105 transition-transform duration-300">
                  <Upload className="w-10 h-10 text-white" />
                </div>
                <div className="absolute -top-2 -right-2 w-8 h-8 bg-orange-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
                  1
                </div>
              </div>
              <h3 className="text-lg font-bold text-gray-800 mb-3">Platform Upload</h3>
              <p className=" text-gray-600 mb-4">
                Securely upload educational content to target enterprise platforms via REST API
              </p>
              <div className="text-xs text-gray-500 bg-gray-100 px-3 py-1 rounded-full inline-block">
                POST /integration/upload
              </div>
            </div>
            
            <div className="text-center group">
              <div className="relative mb-6">
                <div className="w-20 h-20 bg-blue-gradient rounded-2xl flex items-center justify-center mx-auto shadow-lg group-hover:scale-105 transition-transform duration-300">
                  <Terminal className="w-10 h-10 text-white" />
                </div>
                <div className="absolute -top-2 -right-2 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
                  2
                </div>
              </div>
              <h3 className="text-lg font-bold text-gray-800 mb-3">Real-time Monitoring</h3>
              <p className=" text-gray-600 mb-4">
                Track localization progress with comprehensive status updates and processing metrics
              </p>
              <div className="text-xs text-gray-500 bg-gray-100 px-3 py-1 rounded-full inline-block">
                GET /integration/status
              </div>
            </div>
            
            <div className="text-center group">
              <div className="relative mb-6">
                <div className="w-20 h-20 bg-green-gradient rounded-2xl flex items-center justify-center mx-auto shadow-lg group-hover:scale-105 transition-transform duration-300">
                  <Download className="w-10 h-10 text-white" />
                </div>
                <div className="absolute -top-2 -right-2 w-8 h-8 bg-green-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
                  3
                </div>
              </div>
              <h3 className="text-lg font-bold text-gray-800 mb-3">Content Delivery</h3>
              <p className=" text-gray-600 mb-4">
                Download professionally localized content ready for deployment across platforms
              </p>
              <div className="text-xs text-gray-500 bg-gray-100 px-3 py-1 rounded-full inline-block">
                GET /integration/download
              </div>
            </div>
          </div>
          
          {/* Integration Benefits */}
          <div className="mt-12 p-6 bg-gray-100">
            <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
              <Zap className="w-5 h-5 text-blue-600 mr-2" />
              Enterprise Integration Benefits
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div className="flex items-start">
                <CheckCircle className="w-4 h-4 text-green-600 mr-2 mt-0.5 flex-shrink-0" />
                <span className="text-gray-700">Automated content delivery to multiple platforms</span>
              </div>
              <div className="flex items-start">
                <CheckCircle className="w-4 h-4 text-green-600 mr-2 mt-0.5 flex-shrink-0" />
                <span className="text-gray-700">Real-time processing status and notifications</span>
              </div>
              <div className="flex items-start">
                <CheckCircle className="w-4 h-4 text-green-600 mr-2 mt-0.5 flex-shrink-0" />
                <span className="text-gray-700">Secure API authentication and data handling</span>
              </div>
              <div className="flex items-start">
                <CheckCircle className="w-4 h-4 text-green-600 mr-2 mt-0.5 flex-shrink-0" />
                <span className="text-gray-700">Scalable architecture for high-volume processing</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Integration;


