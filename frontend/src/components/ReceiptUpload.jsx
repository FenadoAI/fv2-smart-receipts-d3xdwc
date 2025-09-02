import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { 
  Upload, 
  FileText, 
  AlertCircle, 
  CheckCircle, 
  X, 
  Eye,
  Loader2,
  Image as ImageIcon,
  FileIcon
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { receiptAPI } from '../services/api';

const ReceiptUpload = () => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});
  const [uploadResults, setUploadResults] = useState([]);

  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    // Handle accepted files
    const newFiles = acceptedFiles.map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      file,
      status: 'pending',
      preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : null
    }));

    setFiles(prev => [...prev, ...newFiles]);

    // Handle rejected files
    if (rejectedFiles.length > 0) {
      const rejectedFile = rejectedFiles[0];
      console.error('File rejected:', rejectedFile.errors);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg'],
      'application/pdf': ['.pdf']
    },
    maxSize: 10 * 1024 * 1024, // 10MB
    multiple: true
  });

  const removeFile = (fileId) => {
    setFiles(prev => {
      const updated = prev.filter(f => f.id !== fileId);
      // Revoke URL for preview
      const fileToRemove = prev.find(f => f.id === fileId);
      if (fileToRemove?.preview) {
        URL.revokeObjectURL(fileToRemove.preview);
      }
      return updated;
    });
    
    // Remove from progress tracking
    setUploadProgress(prev => {
      const updated = { ...prev };
      delete updated[fileId];
      return updated;
    });
  };

  const uploadFiles = async () => {
    if (files.length === 0) return;

    setUploading(true);
    setUploadResults([]);
    
    const results = [];

    for (const fileItem of files) {
      try {
        setUploadProgress(prev => ({ ...prev, [fileItem.id]: 0 }));
        
        // Simulate progress updates
        const progressInterval = setInterval(() => {
          setUploadProgress(prev => ({
            ...prev,
            [fileItem.id]: Math.min((prev[fileItem.id] || 0) + Math.random() * 30, 90)
          }));
        }, 200);

        const response = await receiptAPI.upload(fileItem.file);
        
        clearInterval(progressInterval);
        setUploadProgress(prev => ({ ...prev, [fileItem.id]: 100 }));

        results.push({
          id: fileItem.id,
          filename: fileItem.file.name,
          status: 'success',
          data: response.data
        });

        // Update file status
        setFiles(prev => prev.map(f => 
          f.id === fileItem.id ? { ...f, status: 'success' } : f
        ));

      } catch (error) {
        console.error('Upload failed:', error);
        
        results.push({
          id: fileItem.id,
          filename: fileItem.file.name,
          status: 'error',
          error: error.response?.data?.detail || 'Upload failed'
        });

        // Update file status
        setFiles(prev => prev.map(f => 
          f.id === fileItem.id ? { ...f, status: 'error' } : f
        ));
      }
    }

    setUploadResults(results);
    setUploading(false);
  };

  const clearAll = () => {
    // Revoke all preview URLs
    files.forEach(file => {
      if (file.preview) {
        URL.revokeObjectURL(file.preview);
      }
    });
    
    setFiles([]);
    setUploadProgress({});
    setUploadResults([]);
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (file) => {
    if (file.type.startsWith('image/')) {
      return <ImageIcon className="h-8 w-8 text-blue-500" />;
    }
    if (file.type === 'application/pdf') {
      return <FileIcon className="h-8 w-8 text-red-500" />;
    }
    return <FileText className="h-8 w-8 text-gray-500" />;
  };

  return (
    <div className="p-8 space-y-8 max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Upload Receipts</h1>
        <p className="text-gray-600 mt-1">
          Upload your receipts and let our AI extract all the important information automatically.
        </p>
      </div>

      {/* Upload Area */}
      <Card>
        <CardContent className="p-8">
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
              isDragActive
                ? 'border-blue-400 bg-blue-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            <input {...getInputProps()} />
            <div className="space-y-4">
              <div className="mx-auto w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center">
                <Upload className="h-8 w-8 text-blue-600" />
              </div>
              {isDragActive ? (
                <div>
                  <p className="text-lg font-semibold text-blue-600">Drop the files here</p>
                  <p className="text-sm text-gray-500">Release to upload your receipts</p>
                </div>
              ) : (
                <div>
                  <p className="text-lg font-semibold text-gray-900">
                    Drag & drop receipts here, or click to select
                  </p>
                  <p className="text-sm text-gray-500">
                    Supports JPG, PNG, and PDF files up to 10MB each
                  </p>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* File List */}
      {files.length > 0 && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Selected Files ({files.length})</CardTitle>
            <div className="space-x-2">
              <Button 
                variant="outline" 
                size="sm" 
                onClick={clearAll}
                disabled={uploading}
              >
                Clear All
              </Button>
              <Button 
                onClick={uploadFiles} 
                disabled={uploading || files.length === 0}
                className="bg-blue-600 hover:bg-blue-700"
              >
                {uploading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="h-4 w-4 mr-2" />
                    Upload All
                  </>
                )}
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {files.map((fileItem) => (
                <div key={fileItem.id} className="flex items-center space-x-4 p-4 border rounded-lg">
                  {/* File Icon/Preview */}
                  <div className="flex-shrink-0">
                    {fileItem.preview ? (
                      <img
                        src={fileItem.preview}
                        alt="Preview"
                        className="w-12 h-12 object-cover rounded border"
                      />
                    ) : (
                      getFileIcon(fileItem.file)
                    )}
                  </div>

                  {/* File Info */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {fileItem.file.name}
                    </p>
                    <p className="text-sm text-gray-500">
                      {formatFileSize(fileItem.file.size)}
                    </p>
                    
                    {/* Progress Bar */}
                    {uploadProgress[fileItem.id] !== undefined && (
                      <div className="mt-2">
                        <Progress value={uploadProgress[fileItem.id]} className="h-2" />
                        <p className="text-xs text-gray-500 mt-1">
                          {Math.round(uploadProgress[fileItem.id])}% uploaded
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Status & Actions */}
                  <div className="flex items-center space-x-2">
                    {fileItem.status === 'success' && (
                      <CheckCircle className="h-5 w-5 text-green-500" />
                    )}
                    {fileItem.status === 'error' && (
                      <AlertCircle className="h-5 w-5 text-red-500" />
                    )}
                    {fileItem.status === 'pending' && !uploading && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeFile(fileItem.id)}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Upload Results */}
      {uploadResults.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Upload Results</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {uploadResults.map((result) => (
                <Alert key={result.id} className={result.status === 'success' ? 'border-green-200' : 'border-red-200'}>
                  <div className="flex items-center space-x-2">
                    {result.status === 'success' ? (
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    ) : (
                      <AlertCircle className="h-4 w-4 text-red-600" />
                    )}
                    <AlertDescription>
                      <span className="font-medium">{result.filename}</span>
                      {result.status === 'success' ? (
                        <span className="text-green-600 ml-2">
                          Successfully uploaded and processed
                          {result.data?.extracted_data?.vendor_name && (
                            <span className="text-gray-600">
                              {' '}• Vendor: {result.data.extracted_data.vendor_name}
                            </span>
                          )}
                          {result.data?.extracted_data?.total_amount && (
                            <span className="text-gray-600">
                              {' '}• Amount: ${result.data.extracted_data.total_amount}
                            </span>
                          )}
                        </span>
                      ) : (
                        <span className="text-red-600 ml-2">{result.error}</span>
                      )}
                    </AlertDescription>
                  </div>
                </Alert>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tips */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-semibold">Tips for Best Results</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <h4 className="font-medium text-gray-900">Image Quality</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Ensure receipts are well-lit and in focus</li>
                <li>• Avoid shadows and glare on the receipt</li>
                <li>• Capture the entire receipt including all edges</li>
              </ul>
            </div>
            <div className="space-y-2">
              <h4 className="font-medium text-gray-900">File Formats</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• JPG, PNG images up to 10MB</li>
                <li>• PDF files are also supported</li>
                <li>• Multiple files can be uploaded at once</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ReceiptUpload;