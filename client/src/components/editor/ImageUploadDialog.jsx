import React, { useState, useRef, useEffect } from 'react';
import { apiClient } from '../../services/api/client';
import './ImageUploadDialog.css';

/**
 * ImageUploadDialog component - Dialog for uploading images with preview
 */
export function ImageUploadDialog({ isOpen, onClose, onInsert, pageId }) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);
  const [uploadedUrl, setUploadedUrl] = useState(null);
  const fileInputRef = useRef(null);
  const dialogRef = useRef(null);

  // Reset state when dialog opens/closes
  useEffect(() => {
    if (isOpen) {
      setFile(null);
      setPreview(null);
      setError(null);
      setUploadedUrl(null);
      setIsUploading(false);
    }
  }, [isOpen]);

  // Handle click outside to close
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dialogRef.current && !dialogRef.current.contains(event.target)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen, onClose]);

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    // Validate file type
    if (!selectedFile.type.startsWith('image/')) {
      setError('Please select an image file');
      return;
    }

    // Validate file size (10MB default)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (selectedFile.size > maxSize) {
      setError(`File is too large. Maximum size is ${maxSize / 1024 / 1024}MB`);
      return;
    }

    setFile(selectedFile);
    setError(null);

    // Create preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setPreview(reader.result);
    };
    reader.readAsDataURL(selectedFile);
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      if (pageId) {
        formData.append('page_id', pageId);
      }

      const response = await apiClient.post('/upload/image', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const imageUrl = response.data.url;
      setUploadedUrl(imageUrl);

      // Auto-insert if URL is available
      if (imageUrl) {
        onInsert(imageUrl);
        onClose();
      }
    } catch (err) {
      setError(
        err.response?.data?.error ||
        err.message ||
        'Failed to upload image'
      );
    } finally {
      setIsUploading(false);
    }
  };

  const handleInsertUrl = () => {
    if (uploadedUrl) {
      onInsert(uploadedUrl);
      onClose();
    }
  };

  const handleUrlInput = (e) => {
    const url = e.target.value;
    setUploadedUrl(url);
    // Keep URL mode active; preview for URLs is shown in the URL tab below
    // Avoid switching to upload mode when typing a URL
    if (file) {
      setPreview(null);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="arc-image-dialog-overlay">
      <div className="arc-image-dialog" ref={dialogRef}>
        <div className="arc-image-dialog-header">
          <h3>Insert Image</h3>
          <button
            type="button"
            className="arc-image-dialog-close"
            onClick={onClose}
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <div className="arc-image-dialog-content">
          <div className="arc-image-dialog-tabs">
            <button
              type="button"
              className="arc-image-dialog-tab"
              onClick={() => {
                setFile(null);
                setPreview(null);
                setUploadedUrl(null);
                fileInputRef.current?.click();
              }}
            >
              Upload
            </button>
            <button
              type="button"
              className="arc-image-dialog-tab"
              onClick={() => {
                setFile(null);
                setPreview(null);
                setUploadedUrl('');
              }}
            >
              URL
            </button>
          </div>

          {error && !file && !preview && (
            <div className="arc-image-dialog-error">{error}</div>
          )}
          {file ? (
            <div className="arc-image-dialog-upload">
              <div className="arc-image-dialog-preview">
                <img src={preview} alt="Preview" />
              </div>
              {file && (
                <div className="arc-image-dialog-file-info">
                  <p>{file.name}</p>
                  <p className="arc-image-dialog-file-size">
                    {(file.size / 1024).toFixed(1)} KB
                  </p>
                </div>
              )}
              {error && (
                <div className="arc-image-dialog-error">{error}</div>
              )}
              {file && !uploadedUrl && (
                <button
                  type="button"
                  className="arc-image-dialog-button arc-image-dialog-button-upload"
                  onClick={handleUpload}
                  disabled={isUploading}
                >
                  {isUploading ? 'Uploading...' : 'Upload Image'}
                </button>
              )}
              {uploadedUrl && file && (
                <div className="arc-image-dialog-success">
                  <p>Image uploaded successfully!</p>
                  <button
                    type="button"
                    className="arc-image-dialog-button arc-image-dialog-button-insert"
                    onClick={handleInsertUrl}
                  >
                    Insert Image
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="arc-image-dialog-url">
              <label htmlFor="image-url">Image URL:</label>
              <input
                id="image-url"
                type="url"
                className="arc-image-dialog-input"
                placeholder="https://example.com/image.jpg or /uploads/images/..."
                value={uploadedUrl || ''}
                onChange={handleUrlInput}
                autoFocus
              />
              {uploadedUrl && (
                <div className="arc-image-dialog-preview">
                  <img src={uploadedUrl} alt="Preview" onError={() => setPreview(null)} />
                </div>
              )}
            </div>
          )}

          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileSelect}
            style={{ display: 'none' }}
          />
        </div>

        <div className="arc-image-dialog-actions">
          <button
            type="button"
            className="arc-image-dialog-button arc-image-dialog-button-cancel"
            onClick={onClose}
          >
            Cancel
          </button>
          {uploadedUrl && !file && (
            <button
              type="button"
              className="arc-image-dialog-button arc-image-dialog-button-insert"
              onClick={handleInsertUrl}
            >
              Insert Image
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
