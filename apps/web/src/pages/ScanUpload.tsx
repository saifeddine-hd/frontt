import React, { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Upload, FileType, AlertCircle, CheckCircle, X } from 'lucide-react';
import { toast } from 'sonner';

import { createScan } from '../lib/api';

export default function ScanUpload() {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const droppedFiles = Array.from(e.dataTransfer.files);
    const zipFile = droppedFiles.find(file => file.name.endsWith('.zip'));
    
    if (zipFile) {
      setFile(zipFile);
    } else {
      toast.error('Please upload a ZIP file');
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (selectedFile.name.endsWith('.zip')) {
        setFile(selectedFile);
      } else {
        toast.error('Please select a ZIP file');
      }
    }
  };

  const removeFile = () => {
    setFile(null);
  };

  const handleUpload = async () => {
    if (!file) {
      toast.error('Please select a file to upload');
      return;
    }

    if (file.size > 50 * 1024 * 1024) { // 50MB limit
      toast.error('File size must be less than 50MB');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    // Simulate upload progress
    const progressInterval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return prev;
        }
        return prev + 10;
      });
    }, 200);

    try {
      const response = await createScan(file);
      
      setUploadProgress(100);
      setTimeout(() => {
        toast.success('Scan started successfully!');
        navigate(`/findings/${response.job_id}`);
      }, 500);
    } catch (error: any) {
      clearInterval(progressInterval);
      toast.error(error.message || 'Upload failed');
    } finally {
      setIsUploading(false);
      setTimeout(() => setUploadProgress(0), 1000);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-3xl font-bold text-gray-900">Upload & Scan</h1>
        <p className="text-gray-600 mt-2">Upload your codebase to scan for exposed secrets</p>
      </motion.div>

      <div className="max-w-4xl mx-auto">
        {/* Upload Area */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-lg shadow-sm p-8"
        >
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Upload Your Project</h2>

          {/* File Drop Zone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
              isDragOver
                ? 'border-blue-400 bg-blue-50'
                : file
                ? 'border-green-400 bg-green-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            {file ? (
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="space-y-4"
              >
                <CheckCircle className="w-12 h-12 text-green-500 mx-auto" />
                <div className="space-y-2">
                  <p className="text-lg font-medium text-gray-900">{file.name}</p>
                  <p className="text-gray-500">{formatFileSize(file.size)}</p>
                </div>
                <button
                  onClick={removeFile}
                  className="text-red-500 hover:text-red-700 font-medium flex items-center mx-auto"
                >
                  <X className="w-4 h-4 mr-1" />
                  Remove file
                </button>
              </motion.div>
            ) : (
              <div className="space-y-4">
                <Upload className={`w-12 h-12 mx-auto ${isDragOver ? 'text-blue-500' : 'text-gray-400'}`} />
                <div className="space-y-2">
                  <p className="text-lg font-medium text-gray-900">
                    {isDragOver ? 'Drop your file here' : 'Drag and drop your ZIP file here'}
                  </p>
                  <p className="text-gray-500">or</p>
                  <label className="inline-block bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg cursor-pointer transition-colors">
                    Browse Files
                    <input
                      type="file"
                      accept=".zip"
                      onChange={handleFileSelect}
                      className="hidden"
                      disabled={isUploading}
                    />
                  </label>
                </div>
                <p className="text-sm text-gray-500">
                  Maximum file size: 50MB. Only ZIP files are supported.
                </p>
              </div>
            )}
          </div>

          {/* Upload Progress */}
          {isUploading && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="mt-6"
            >
              <div className="bg-gray-200 rounded-full h-3 overflow-hidden">
                <motion.div
                  className="bg-blue-600 h-full rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${uploadProgress}%` }}
                  transition={{ duration: 0.3 }}
                />
              </div>
              <p className="text-center text-sm text-gray-600 mt-2">
                Uploading... {uploadProgress}%
              </p>
            </motion.div>
          )}

          {/* Upload Button */}
          {file && !isUploading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mt-6 flex justify-center"
            >
              <button
                onClick={handleUpload}
                className="bg-green-600 hover:bg-green-700 text-white px-8 py-3 rounded-lg font-semibold transition-colors"
              >
                Start Scan
              </button>
            </motion.div>
          )}
        </motion.div>

        {/* Info Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8"
        >
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <div className="flex items-start">
              <FileType className="w-6 h-6 text-blue-600 mt-1 mr-3 flex-shrink-0" />
              <div>
                <h3 className="font-semibold text-blue-900 mb-2">What we scan</h3>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• AWS access keys and secrets</li>
                  <li>• GitHub personal access tokens</li>
                  <li>• Stripe API keys</li>
                  <li>• Private keys and certificates</li>
                  <li>• Database connection strings</li>
                  <li>• JWT tokens and more</li>
                </ul>
              </div>
            </div>
          </div>

          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <div className="flex items-start">
              <AlertCircle className="w-6 h-6 text-green-600 mt-1 mr-3 flex-shrink-0" />
              <div>
                <h3 className="font-semibold text-green-900 mb-2">Security & Privacy</h3>
                <ul className="text-sm text-green-800 space-y-1">
                  <li>• Files deleted after scanning</li>
                  <li>• Secrets automatically masked</li>
                  <li>• No data retention policy</li>
                  <li>• GDPR compliant processing</li>
                  <li>• Secure JWT authentication</li>
                  <li>• End-to-end encryption</li>
                </ul>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}