import React, { useState, useEffect, useRef } from 'react';
import './TableDialog.css';

/**
 * TableDialog component - Dialog for inserting tables with custom dimensions
 */
export function TableDialog({ isOpen, onClose, onInsert }) {
  const [rows, setRows] = useState(3);
  const [cols, setCols] = useState(3);
  const [hasHeaderRow, setHasHeaderRow] = useState(true);
  const dialogRef = useRef(null);

  // Reset state when dialog opens/closes
  useEffect(() => {
    if (isOpen) {
      setRows(3);
      setCols(3);
      setHasHeaderRow(true);
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

  // Handle Escape key
  useEffect(() => {
    const handleEscape = (event) => {
      if (event.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [isOpen, onClose]);

  const handleInsert = () => {
    if (rows > 0 && cols > 0) {
      onInsert({ rows, cols, withHeaderRow: hasHeaderRow });
      onClose();
    }
  };

  const handleRowsChange = (e) => {
    const value = parseInt(e.target.value, 10);
    if (!isNaN(value) && value > 0 && value <= 20) {
      setRows(value);
    }
  };

  const handleColsChange = (e) => {
    const value = parseInt(e.target.value, 10);
    if (!isNaN(value) && value > 0 && value <= 20) {
      setCols(value);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="arc-table-dialog-overlay">
      <div className="arc-table-dialog" ref={dialogRef}>
        <div className="arc-table-dialog-header">
          <h3>Insert Table</h3>
          <button
            type="button"
            className="arc-table-dialog-close"
            onClick={onClose}
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <div className="arc-table-dialog-content">
          <div className="arc-table-dialog-field">
            <label htmlFor="table-rows">Rows:</label>
            <input
              id="table-rows"
              type="number"
              min="1"
              max="20"
              value={rows}
              onChange={handleRowsChange}
              className="arc-table-dialog-input"
              autoFocus
            />
          </div>

          <div className="arc-table-dialog-field">
            <label htmlFor="table-cols">Columns:</label>
            <input
              id="table-cols"
              type="number"
              min="1"
              max="20"
              value={cols}
              onChange={handleColsChange}
              className="arc-table-dialog-input"
            />
          </div>

          <div className="arc-table-dialog-field">
            <label>
              <input
                type="checkbox"
                checked={hasHeaderRow}
                onChange={(e) => setHasHeaderRow(e.target.checked)}
              />
              <span>Header row</span>
            </label>
          </div>
        </div>

        <div className="arc-table-dialog-actions">
          <button
            type="button"
            className="arc-table-dialog-button arc-table-dialog-button-cancel"
            onClick={onClose}
          >
            Cancel
          </button>
          <button
            type="button"
            className="arc-table-dialog-button arc-table-dialog-button-insert"
            onClick={handleInsert}
          >
            Insert Table
          </button>
        </div>
      </div>
    </div>
  );
}
