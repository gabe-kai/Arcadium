# Wiki Image Upload Implementation Guide

**Status**: Backend API ✅ Complete | Frontend UI ❌ Not Started
**Temporary File**: This guide will be removed after implementation is complete

## Overview

Image upload functionality allows writers and admins to upload images and insert them into pages. The backend API is fully implemented and ready to consume.

## Backend API Status

✅ **All endpoints implemented** in `services/wiki/app/routes/upload_routes.py`:
- `POST /api/upload/image` - Upload image file
- `GET /api/uploads/images/{filename}` - Serve uploaded images (public)

**Permissions**:
- Upload requires writer or admin role (`@require_role(["writer", "admin"])`)
- Viewing images is public (no authentication required)

**Features**:
- File size validation (configurable via admin dashboard)
- File type validation (images only)
- UUID-based filename storage
- Optional page association
- Original filename preserved in database

---

## Frontend Implementation Plan

### Phase 1: Image Upload Dialog Component

**Goal**: Create dialog component for uploading and inserting images

#### Tasks:
- [ ] Create `ImageUploadDialog` component (enhance existing or create new)
- [ ] Two input methods:
  - File upload (drag & drop or file picker)
  - URL input (for external images)
- [ ] File validation:
  - Check file type (images only: jpg, jpeg, png, gif, webp, svg)
  - Check file size (against admin-configured limit)
  - Show error messages for invalid files
- [ ] Image preview:
  - Show preview of selected/uploaded image
  - Display file size and dimensions
- [ ] Optional page association:
  - Current page ID (if editing)
  - Can be left unassociated
- [ ] Insert button:
  - Inserts image into editor at cursor position
  - Uses markdown image syntax: `![alt text](url)`
- [ ] Loading state during upload
- [ ] Success/error notifications

#### Component Structure:
```jsx
// client/src/components/editor/ImageUploadDialog.jsx
export function ImageUploadDialog({
  isOpen,
  onClose,
  onInsert,
  pageId,
}) {
  const [uploadMethod, setUploadMethod] = useState('upload'); // 'upload' or 'url'
  const [selectedFile, setSelectedFile] = useState(null);
  const [imageUrl, setImageUrl] = useState('');
  const [altText, setAltText] = useState('');
  const [preview, setPreview] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  const uploadMutation = useUploadImage();
  const { showSuccess, showError } = useNotificationContext();

  // File selection handler
  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml'];
    if (!validTypes.includes(file.type)) {
      showError('Invalid file type. Please select an image file.');
      return;
    }

    // Validate file size (get from config or use default)
    const maxSize = 10 * 1024 * 1024; // 10MB default
    if (file.size > maxSize) {
      showError(`File too large. Maximum size: ${maxSize / 1024 / 1024}MB`);
      return;
    }

    setSelectedFile(file);

    // Create preview
    const reader = new FileReader();
    reader.onload = (e) => {
      setPreview(e.target.result);
    };
    reader.readAsDataURL(file);
  };

  // Upload handler
  const handleUpload = async () => {
    if (uploadMethod === 'upload' && !selectedFile) {
      showError('Please select a file');
      return;
    }
    if (uploadMethod === 'url' && !imageUrl.trim()) {
      showError('Please enter an image URL');
      return;
    }

    if (uploadMethod === 'upload') {
      // Upload file
      const formData = new FormData();
      formData.append('file', selectedFile);
      if (pageId) {
        formData.append('page_id', pageId);
      }

      uploadMutation.mutate(
        { formData },
        {
          onSuccess: (data) => {
            // Insert image into editor
            const imageMarkdown = `![${altText || 'Image'}](${data.url})`;
            onInsert(imageMarkdown);
            showSuccess('Image uploaded and inserted');
            onClose();
          },
          onError: (error) => {
            showError(error.response?.data?.error || 'Failed to upload image');
          },
        }
      );
    } else {
      // Use URL directly
      const imageMarkdown = `![${altText || 'Image'}](${imageUrl})`;
      onInsert(imageMarkdown);
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="arc-image-upload-dialog-overlay">
      <div className="arc-image-upload-dialog">
        <div className="arc-image-upload-header">
          <h3>Insert Image</h3>
          <button onClick={onClose} className="arc-dialog-close">×</button>
        </div>

        <div className="arc-image-upload-tabs">
          <button
            className={uploadMethod === 'upload' ? 'active' : ''}
            onClick={() => setUploadMethod('upload')}
          >
            Upload File
          </button>
          <button
            className={uploadMethod === 'url' ? 'active' : ''}
            onClick={() => setUploadMethod('url')}
          >
            From URL
          </button>
        </div>

        {uploadMethod === 'upload' ? (
          <div className="arc-image-upload-file">
            <div className="arc-file-dropzone">
              <input
                type="file"
                accept="image/*"
                onChange={handleFileSelect}
                id="image-file-input"
                style={{ display: 'none' }}
              />
              <label htmlFor="image-file-input" className="arc-file-dropzone-label">
                {selectedFile ? (
                  <div className="arc-file-selected">
                    <img src={preview} alt="Preview" className="arc-image-preview" />
                    <p>{selectedFile.name}</p>
                    <p className="arc-file-size">
                      {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                ) : (
                  <div className="arc-file-dropzone-empty">
                    <span>📷</span>
                    <p>Click to select or drag and drop</p>
                    <p className="arc-file-hint">PNG, JPG, GIF, WebP, SVG up to 10MB</p>
                  </div>
                )}
              </label>
            </div>
          </div>
        ) : (
          <div className="arc-image-upload-url">
            <label>
              Image URL:
              <input
                type="url"
                value={imageUrl}
                onChange={(e) => {
                  setImageUrl(e.target.value);
                  setPreview(e.target.value);
                }}
                placeholder="https://example.com/image.jpg"
              />
            </label>
            {preview && (
              <div className="arc-image-preview">
                <img src={preview} alt="Preview" onError={() => setPreview(null)} />
              </div>
            )}
          </div>
        )}

        <div className="arc-image-upload-alt">
          <label>
            Alt Text (optional):
            <input
              type="text"
              value={altText}
              onChange={(e) => setAltText(e.target.value)}
              placeholder="Describe the image"
            />
          </label>
        </div>

        <div className="arc-image-upload-actions">
          <button onClick={onClose}>Cancel</button>
          <button
            onClick={handleUpload}
            disabled={
              uploadMutation.isPending ||
              (uploadMethod === 'upload' && !selectedFile) ||
              (uploadMethod === 'url' && !imageUrl.trim())
            }
          >
            {uploadMutation.isPending ? 'Uploading...' : 'Insert Image'}
          </button>
        </div>

        {uploadMutation.isPending && (
          <div className="arc-upload-progress">
            <progress value={uploadProgress} max={100} />
            <span>Uploading... {uploadProgress}%</span>
          </div>
        )}
      </div>
    </div>
  );
}
```

---

### Phase 2: Image Upload API Functions

**Goal**: Create API functions for image upload

#### Tasks:
- [ ] Create `uploadImage` function
- [ ] Create `useUploadImage` mutation hook
- [ ] Handle file upload with FormData
- [ ] Track upload progress (optional)
- [ ] Handle errors (file too large, invalid type, network errors)

#### API Functions:
```javascript
// client/src/services/api/upload.js
export async function uploadImage(formData, onProgress) {
  const response = await apiClient.post('/upload/image', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        onProgress(percentCompleted);
      }
    },
  });
  return response.data;
}

export function useUploadImage() {
  const { token } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ formData, onProgress }) => uploadImage(formData, onProgress),
    onSuccess: () => {
      // Optionally invalidate any image-related queries
      queryClient.invalidateQueries({ queryKey: ['images'] });
    },
  });
}
```

---

### Phase 3: Editor Integration

**Goal**: Integrate image upload into editor toolbar

#### Tasks:
- [ ] Update `EditorToolbar` component
- [ ] Image button opens `ImageUploadDialog`
- [ ] On image insert, add to editor at cursor position
- [ ] Handle both markdown and HTML image insertion
- [ ] Support drag & drop images into editor (optional enhancement)

#### Implementation:
```jsx
// client/src/components/editor/EditorToolbar.jsx
const [showImageDialog, setShowImageDialog] = useState(false);

const handleImageInsert = (imageMarkdown) => {
  if (!editor) return;

  // Insert markdown at cursor position
  editor.chain().focus().insertContent(imageMarkdown).run();
  setShowImageDialog(false);
};

// In toolbar:
<button
  onClick={() => setShowImageDialog(true)}
  title="Insert image"
>
  🖼️ Image
</button>

<ImageUploadDialog
  isOpen={showImageDialog}
  onClose={() => setShowImageDialog(false)}
  onInsert={handleImageInsert}
  pageId={pageId}
/>
```

---

### Phase 4: Image Preview Enhancement

**Goal**: Show uploaded images in editor preview

#### Tasks:
- [ ] Ensure images render correctly in editor preview
- [ ] Handle both uploaded images (relative URLs) and external URLs
- [ ] Image styling in preview matches view mode
- [ ] Responsive image handling

#### Implementation:
```jsx
// client/src/pages/EditPage.jsx
// In preview mode, ensure images are processed
useEffect(() => {
  if (showPreview && previewRef.current) {
    // Process images in preview
    const images = previewRef.current.querySelectorAll('img');
    images.forEach(img => {
      // Handle relative URLs (uploaded images)
      if (img.src.startsWith('/api/uploads/images/')) {
        // Already correct
      } else if (img.src.startsWith('/uploads/images/')) {
        // Convert to API URL
        img.src = img.src.replace('/uploads/images/', '/api/uploads/images/');
      }
    });
  }
}, [showPreview]);
```

---

### Phase 5: Image Management (Optional Enhancement)

**Goal**: View and manage uploaded images

#### Tasks:
- [ ] Create image gallery page (optional)
- [ ] List all uploaded images
- [ ] Filter by page association
- [ ] Delete unused images (admin only)
- [ ] View image details (size, upload date, associated pages)

---

## Component Structure

```
client/src/
  components/
    editor/
      ImageUploadDialog.jsx (enhanced)
      ImageUploadDialog.css
      EditorToolbar.jsx (enhanced)
  services/
    api/
      upload.js (new file)
```

---

## API Integration

### Request Format

**Upload Image:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body:
  - `file` (File) - Image file
  - `page_id` (string, optional) - Page UUID to associate with

### Response Format

**Success:**
```json
{
  "url": "/api/uploads/images/{uuid}.{ext}",
  "uuid": "image-uuid",
  "original_filename": "image.jpg",
  "size": 123456,
  "mime_type": "image/jpeg",
  "page_id": "page-uuid" // or null
}
```

**Error:**
```json
{
  "error": "File too large",
  "max_size_bytes": 10485760,
  "size_bytes": 15728640
}
```

### Image Serving

- Images are served from `/api/uploads/images/{filename}`
- Public endpoint (no authentication required)
- CORS headers included
- Supports: jpg, jpeg, png, gif, webp, svg

---

## File Size Configuration

The maximum upload size is configured via the admin dashboard:
- Default: 10MB
- Configurable presets: 1MB, 2MB, 5MB, 10MB
- Custom size option
- Stored in `WikiConfig` table as `upload_max_size_mb`

**Frontend should:**
- Fetch current limit from admin config (or use default)
- Validate file size before upload
- Show clear error if file exceeds limit
- Display current limit in upload dialog

---

## Testing Strategy

### Unit Tests
- ImageUploadDialog component tests
- File validation tests
- URL validation tests
- Preview rendering tests
- API function tests (mocked)

### Integration Tests
- Image upload flow
- Image insertion into editor
- Error handling (file too large, invalid type)
- URL image insertion
- Preview rendering

### Manual Testing Checklist
- [ ] Upload image via file picker
- [ ] Upload image via drag & drop
- [ ] Insert image from URL
- [ ] File type validation works
- [ ] File size validation works
- [ ] Image preview displays correctly
- [ ] Image inserts into editor
- [ ] Image renders in preview mode
- [ ] Image renders in view mode
- [ ] Alt text is preserved
- [ ] Page association works (optional)
- [ ] Error messages are clear
- [ ] Loading states work

---

## Styling Notes

- Upload dialog should match existing dialog styles
- File dropzone should be visually clear (dashed border, hover effect)
- Image preview should be responsive (max-width: 100%)
- Progress bar should be visible during upload
- Error messages should be prominent
- Match existing form input styling

---

## Drag & Drop Enhancement (Optional)

```jsx
// Enhanced file dropzone with drag & drop
const [isDragging, setIsDragging] = useState(false);

const handleDragOver = (e) => {
  e.preventDefault();
  setIsDragging(true);
};

const handleDragLeave = () => {
  setIsDragging(false);
};

const handleDrop = (e) => {
  e.preventDefault();
  setIsDragging(false);

  const file = e.dataTransfer.files[0];
  if (file) {
    handleFileSelect({ target: { files: [file] } });
  }
};

<div
  className={`arc-file-dropzone ${isDragging ? 'dragging' : ''}`}
  onDragOver={handleDragOver}
  onDragLeave={handleDragLeave}
  onDrop={handleDrop}
>
  {/* Dropzone content */}
</div>
```

---

## Related Documentation

- [Wiki Admin Dashboard](wiki-admin-dashboard.md) - File upload configuration
- [Wiki API Documentation](api/wiki-api.md) - Complete API reference
- [Wiki UI Implementation Guide](wiki-ui-implementation-guide.md) - General UI patterns
