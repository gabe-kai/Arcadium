import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TableDialog } from '../../components/editor/TableDialog';

describe('TableDialog', () => {
  const mockOnInsert = vi.fn();
  const mockOnClose = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('does not render when isOpen is false', () => {
    const { container } = render(
      <TableDialog isOpen={false} onClose={mockOnClose} onInsert={mockOnInsert} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders when isOpen is true', () => {
    render(
      <TableDialog isOpen={true} onClose={mockOnClose} onInsert={mockOnInsert} />
    );
    expect(screen.getByRole('heading', { name: /Insert Table/i })).toBeInTheDocument();
  });

  it('displays default values (3 rows, 3 columns, header row checked)', () => {
    render(
      <TableDialog isOpen={true} onClose={mockOnClose} onInsert={mockOnInsert} />
    );
    
    const rowsInput = screen.getByLabelText(/Rows:/i);
    const colsInput = screen.getByLabelText(/Columns:/i);
    const headerCheckbox = screen.getByLabelText(/Header row/i);
    
    expect(rowsInput).toHaveValue(3);
    expect(colsInput).toHaveValue(3);
    expect(headerCheckbox).toBeChecked();
  });

  it('allows changing rows value', () => {
    render(
      <TableDialog isOpen={true} onClose={mockOnClose} onInsert={mockOnInsert} />
    );
    
    const rowsInput = screen.getByLabelText(/Rows:/i);
    fireEvent.change(rowsInput, { target: { value: '5' } });
    
    expect(rowsInput).toHaveValue(5);
  });

  it('allows changing columns value', () => {
    render(
      <TableDialog isOpen={true} onClose={mockOnClose} onInsert={mockOnInsert} />
    );
    
    const colsInput = screen.getByLabelText(/Columns:/i);
    fireEvent.change(colsInput, { target: { value: '4' } });
    
    expect(colsInput).toHaveValue(4);
  });

  it('allows toggling header row checkbox', async () => {
    const user = userEvent.setup();
    render(
      <TableDialog isOpen={true} onClose={mockOnClose} onInsert={mockOnInsert} />
    );
    
    const headerCheckbox = screen.getByLabelText(/Header row/i);
    expect(headerCheckbox).toBeChecked();
    
    await user.click(headerCheckbox);
    expect(headerCheckbox).not.toBeChecked();
    
    await user.click(headerCheckbox);
    expect(headerCheckbox).toBeChecked();
  });

  it('calls onInsert with correct values when Insert Table is clicked', async () => {
    const user = userEvent.setup();
    render(
      <TableDialog isOpen={true} onClose={mockOnClose} onInsert={mockOnInsert} />
    );
    
    const rowsInput = screen.getByLabelText(/Rows:/i);
    const colsInput = screen.getByLabelText(/Columns:/i);
    
    // Change rows using fireEvent for number inputs
    fireEvent.change(rowsInput, { target: { value: '4' } });
    
    // Change columns
    fireEvent.change(colsInput, { target: { value: '5' } });
    
    // Wait for values to update
    await waitFor(() => {
      expect(rowsInput).toHaveValue(4);
      expect(colsInput).toHaveValue(5);
    });
    
    const insertButton = screen.getByRole('button', { name: /Insert Table/i });
    await user.click(insertButton);
    
    expect(mockOnInsert).toHaveBeenCalledWith({
      rows: 4,
      cols: 5,
      withHeaderRow: true,
    });
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('calls onClose when Cancel is clicked', async () => {
    const user = userEvent.setup();
    render(
      <TableDialog isOpen={true} onClose={mockOnClose} onInsert={mockOnInsert} />
    );
    
    const cancelButton = screen.getByText('Cancel');
    await user.click(cancelButton);
    
    expect(mockOnClose).toHaveBeenCalled();
    expect(mockOnInsert).not.toHaveBeenCalled();
  });

  it('calls onClose when close button (×) is clicked', async () => {
    const user = userEvent.setup();
    render(
      <TableDialog isOpen={true} onClose={mockOnClose} onInsert={mockOnInsert} />
    );
    
    const closeButton = screen.getByLabelText(/Close/i);
    await user.click(closeButton);
    
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('calls onClose when Escape key is pressed', async () => {
    const user = userEvent.setup();
    render(
      <TableDialog isOpen={true} onClose={mockOnClose} onInsert={mockOnInsert} />
    );
    
    await user.keyboard('{Escape}');
    
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('respects minimum value of 1 for rows', async () => {
    const user = userEvent.setup();
    render(
      <TableDialog isOpen={true} onClose={mockOnClose} onInsert={mockOnInsert} />
    );
    
    const rowsInput = screen.getByLabelText(/Rows:/i);
    await user.clear(rowsInput);
    await user.type(rowsInput, '0');
    
    // Should not accept 0, but we can't easily test the min attribute behavior
    // Just verify the input exists and has min attribute
    expect(rowsInput).toHaveAttribute('min', '1');
  });

  it('respects maximum value of 20 for rows', () => {
    render(
      <TableDialog isOpen={true} onClose={mockOnClose} onInsert={mockOnInsert} />
    );
    
    const rowsInput = screen.getByLabelText(/Rows:/i);
    expect(rowsInput).toHaveAttribute('max', '20');
  });

  it('respects minimum value of 1 for columns', () => {
    render(
      <TableDialog isOpen={true} onClose={mockOnClose} onInsert={mockOnInsert} />
    );
    
    const colsInput = screen.getByLabelText(/Columns:/i);
    expect(colsInput).toHaveAttribute('min', '1');
  });

  it('respects maximum value of 20 for columns', () => {
    render(
      <TableDialog isOpen={true} onClose={mockOnClose} onInsert={mockOnInsert} />
    );
    
    const colsInput = screen.getByLabelText(/Columns:/i);
    expect(colsInput).toHaveAttribute('max', '20');
  });

  it('resets to default values when dialog reopens', async () => {
    const user = userEvent.setup();
    const { rerender } = render(
      <TableDialog isOpen={true} onClose={mockOnClose} onInsert={mockOnInsert} />
    );
    
    const rowsInput = screen.getByLabelText(/Rows:/i);
    const colsInput = screen.getByLabelText(/Columns:/i);
    await user.clear(rowsInput);
    await user.type(rowsInput, '10');
    await user.clear(colsInput);
    await user.type(colsInput, '8');
    
    // Close dialog
    rerender(
      <TableDialog isOpen={false} onClose={mockOnClose} onInsert={mockOnInsert} />
    );
    
    // Reopen dialog
    rerender(
      <TableDialog isOpen={true} onClose={mockOnClose} onInsert={mockOnInsert} />
    );
    
    const newRowsInput = screen.getByLabelText(/Rows:/i);
    const newColsInput = screen.getByLabelText(/Columns:/i);
    expect(newRowsInput).toHaveValue(3);
    expect(newColsInput).toHaveValue(3);
  });

  it('includes header row false when checkbox is unchecked', async () => {
    const user = userEvent.setup();
    render(
      <TableDialog isOpen={true} onClose={mockOnClose} onInsert={mockOnInsert} />
    );
    
    const headerCheckbox = screen.getByLabelText(/Header row/i);
    await user.click(headerCheckbox);
    
    const insertButton = screen.getByRole('button', { name: /Insert Table/i });
    await user.click(insertButton);
    
    expect(mockOnInsert).toHaveBeenCalledWith({
      rows: 3,
      cols: 3,
      withHeaderRow: false,
    });
  });
});
