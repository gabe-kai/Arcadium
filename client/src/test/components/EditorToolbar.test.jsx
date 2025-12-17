import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { EditorToolbar } from '../../components/editor/EditorToolbar';
import { useEditor } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';

// Mock Tiptap
vi.mock('@tiptap/react', () => ({
  useEditor: vi.fn(),
  EditorContent: () => <div data-testid="editor-content" />,
}));

// Create a chainable mock that supports the full Tiptap API
const createChainable = () => ({
  chain: vi.fn(() => createChainable()),
  focus: vi.fn(() => createChainable()),
  extendMarkRange: vi.fn(() => createChainable()),
  toggleBold: vi.fn(() => createChainable()),
  toggleItalic: vi.fn(() => createChainable()),
  toggleCode: vi.fn(() => createChainable()),
  toggleBulletList: vi.fn(() => createChainable()),
  toggleOrderedList: vi.fn(() => createChainable()),
  toggleCodeBlock: vi.fn(() => createChainable()),
  insertTable: vi.fn(() => createChainable()),
  undo: vi.fn(() => createChainable()),
  redo: vi.fn(() => createChainable()),
  setParagraph: vi.fn(() => createChainable()),
  toggleHeading: vi.fn(() => createChainable()),
  setLink: vi.fn(() => createChainable()),
  unsetLink: vi.fn(() => createChainable()),
  setImage: vi.fn(() => createChainable()),
  run: vi.fn(),
});

describe('EditorToolbar', () => {
  let mockEditor;

  beforeEach(() => {
    mockEditor = {
      ...createChainable(),
      can: vi.fn(() => createChainable()),
      isActive: vi.fn(() => false),
      getAttributes: vi.fn(() => ({})),
      getHTML: vi.fn(() => '<p>Content</p>'),
    };

    useEditor.mockReturnValue(mockEditor);
  });

  it('returns null when editor is not provided', () => {
    const { container } = render(<EditorToolbar editor={null} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders format dropdown', () => {
    render(<EditorToolbar editor={mockEditor} />);
    const select = screen.getByRole('combobox');
    expect(select).toBeInTheDocument();
    expect(select).toHaveValue('paragraph');
  });

  it('renders bold button', () => {
    render(<EditorToolbar editor={mockEditor} />);
    const boldButton = screen.getByTitle(/Bold/i);
    expect(boldButton).toBeInTheDocument();
  });

  it('renders italic button', () => {
    render(<EditorToolbar editor={mockEditor} />);
    const italicButton = screen.getByTitle(/Italic/i);
    expect(italicButton).toBeInTheDocument();
  });

  it('renders code button', () => {
    render(<EditorToolbar editor={mockEditor} />);
    const codeButton = screen.getByTitle(/Inline Code/i);
    expect(codeButton).toBeInTheDocument();
  });

  it('renders bullet list button', () => {
    render(<EditorToolbar editor={mockEditor} />);
    const bulletButton = screen.getByTitle(/Bullet List/i);
    expect(bulletButton).toBeInTheDocument();
  });

  it('renders numbered list button', () => {
    render(<EditorToolbar editor={mockEditor} />);
    const numberedButton = screen.getByTitle(/Numbered List/i);
    expect(numberedButton).toBeInTheDocument();
  });

  it('renders link button', () => {
    render(<EditorToolbar editor={mockEditor} />);
    const linkButton = screen.getByTitle(/Insert Link/i);
    expect(linkButton).toBeInTheDocument();
  });

  it('renders image button', () => {
    render(<EditorToolbar editor={mockEditor} />);
    const imageButton = screen.getByTitle(/Insert Image/i);
    expect(imageButton).toBeInTheDocument();
  });

  it('renders code block button', () => {
    render(<EditorToolbar editor={mockEditor} />);
    const codeBlockButton = screen.getByTitle(/Code Block/i);
    expect(codeBlockButton).toBeInTheDocument();
  });

  it('renders table button', () => {
    render(<EditorToolbar editor={mockEditor} />);
    const tableButton = screen.getByTitle(/Insert Table/i);
    expect(tableButton).toBeInTheDocument();
  });

  it('renders undo button', () => {
    render(<EditorToolbar editor={mockEditor} />);
    const undoButton = screen.getByTitle(/Undo/i);
    expect(undoButton).toBeInTheDocument();
  });

  it('renders redo button', () => {
    render(<EditorToolbar editor={mockEditor} />);
    const redoButton = screen.getByTitle(/Redo/i);
    expect(redoButton).toBeInTheDocument();
  });

  it('toggles bold when bold button is clicked', () => {
    render(<EditorToolbar editor={mockEditor} />);
    const boldButton = screen.getByTitle(/Bold/i);
    
    fireEvent.click(boldButton);
    
    expect(mockEditor.chain).toHaveBeenCalled();
    expect(mockEditor.focus).toHaveBeenCalled();
    expect(mockEditor.toggleBold).toHaveBeenCalled();
    expect(mockEditor.run).toHaveBeenCalled();
  });

  it('toggles italic when italic button is clicked', () => {
    render(<EditorToolbar editor={mockEditor} />);
    const italicButton = screen.getByTitle(/Italic/i);
    
    fireEvent.click(italicButton);
    
    expect(mockEditor.toggleItalic).toHaveBeenCalled();
    expect(mockEditor.run).toHaveBeenCalled();
  });

  it('toggles code when code button is clicked', () => {
    render(<EditorToolbar editor={mockEditor} />);
    const codeButton = screen.getByTitle(/Inline Code/i);
    
    fireEvent.click(codeButton);
    
    expect(mockEditor.toggleCode).toHaveBeenCalled();
    expect(mockEditor.run).toHaveBeenCalled();
  });

  it('toggles bullet list when bullet list button is clicked', () => {
    render(<EditorToolbar editor={mockEditor} />);
    const bulletButton = screen.getByTitle(/Bullet List/i);
    
    fireEvent.click(bulletButton);
    
    expect(mockEditor.toggleBulletList).toHaveBeenCalled();
    expect(mockEditor.run).toHaveBeenCalled();
  });

  it('toggles ordered list when numbered list button is clicked', () => {
    render(<EditorToolbar editor={mockEditor} />);
    const numberedButton = screen.getByTitle(/Numbered List/i);
    
    fireEvent.click(numberedButton);
    
    expect(mockEditor.toggleOrderedList).toHaveBeenCalled();
    expect(mockEditor.run).toHaveBeenCalled();
  });

  it('inserts table when table button is clicked', () => {
    render(<EditorToolbar editor={mockEditor} />);
    const tableButton = screen.getByTitle(/Insert Table/i);
    
    fireEvent.click(tableButton);
    
    expect(mockEditor.insertTable).toHaveBeenCalledWith({ rows: 3, cols: 3, withHeaderRow: true });
    expect(mockEditor.run).toHaveBeenCalled();
  });

  it('undoes when undo button is clicked', () => {
    render(<EditorToolbar editor={mockEditor} />);
    const undoButton = screen.getByTitle(/Undo/i);
    
    fireEvent.click(undoButton);
    
    expect(mockEditor.undo).toHaveBeenCalled();
    expect(mockEditor.run).toHaveBeenCalled();
  });

  it('redoes when redo button is clicked', () => {
    render(<EditorToolbar editor={mockEditor} />);
    const redoButton = screen.getByTitle(/Redo/i);
    
    fireEvent.click(redoButton);
    
    expect(mockEditor.redo).toHaveBeenCalled();
    expect(mockEditor.run).toHaveBeenCalled();
  });

  it('disables buttons when command cannot be executed', () => {
    // The disabled check is: !editor.can().chain().focus().toggleBold().run()
    // So we need can() to return a chainable where run() returns false
    // Create a chainable that supports all commands but run() returns false
    const cannotExecuteChain = createChainable();
    // Override run to return false (cannot execute)
    cannotExecuteChain.run = vi.fn(() => false);
    mockEditor.can.mockReturnValue(cannotExecuteChain);

    render(<EditorToolbar editor={mockEditor} />);
    const boldButton = screen.getByTitle(/Bold/i);

    expect(boldButton).toBeDisabled();
  });

  it('shows active state for bold when active', () => {
    mockEditor.isActive.mockImplementation((mark) => mark === 'bold');
    
    render(<EditorToolbar editor={mockEditor} />);
    const boldButton = screen.getByTitle(/Bold/i);
    
    expect(boldButton).toHaveClass('arc-editor-toolbar-button-active');
  });

  it('shows active state for italic when active', () => {
    mockEditor.isActive.mockImplementation((mark) => mark === 'italic');
    
    render(<EditorToolbar editor={mockEditor} />);
    const italicButton = screen.getByTitle(/Italic/i);
    
    expect(italicButton).toHaveClass('arc-editor-toolbar-button-active');
  });

  it('shows active state for code when active', () => {
    mockEditor.isActive.mockImplementation((mark) => mark === 'code');
    
    render(<EditorToolbar editor={mockEditor} />);
    const codeButton = screen.getByTitle(/Inline Code/i);
    
    expect(codeButton).toHaveClass('arc-editor-toolbar-button-active');
  });

  it('shows active state for bullet list when active', () => {
    mockEditor.isActive.mockImplementation((mark) => mark === 'bulletList');
    
    render(<EditorToolbar editor={mockEditor} />);
    const bulletButton = screen.getByTitle(/Bullet List/i);
    
    expect(bulletButton).toHaveClass('arc-editor-toolbar-button-active');
  });

  it('shows active state for ordered list when active', () => {
    mockEditor.isActive.mockImplementation((mark) => mark === 'orderedList');
    
    render(<EditorToolbar editor={mockEditor} />);
    const numberedButton = screen.getByTitle(/Numbered List/i);
    
    expect(numberedButton).toHaveClass('arc-editor-toolbar-button-active');
  });

  it('shows active state for code block when active', () => {
    mockEditor.isActive.mockImplementation((mark) => mark === 'codeBlock');
    
    render(<EditorToolbar editor={mockEditor} />);
    const codeBlockButton = screen.getByTitle(/Code Block/i);
    
    expect(codeBlockButton).toHaveClass('arc-editor-toolbar-button-active');
  });

  it('shows active state for link when active', () => {
    mockEditor.isActive.mockImplementation((mark) => mark === 'link');
    mockEditor.getAttributes.mockReturnValue({ href: 'https://example.com' });
    
    render(<EditorToolbar editor={mockEditor} />);
    const linkButton = screen.getByTitle(/Insert Link/i);
    
    expect(linkButton).toHaveClass('arc-editor-toolbar-button-active');
  });

  it('sets paragraph when format dropdown selects paragraph', () => {
    render(<EditorToolbar editor={mockEditor} />);
    const select = screen.getByRole('combobox');
    
    fireEvent.change(select, { target: { value: 'paragraph' } });
    
    expect(mockEditor.setParagraph).toHaveBeenCalled();
    expect(mockEditor.run).toHaveBeenCalled();
  });

  it('sets heading when format dropdown selects heading level', () => {
    render(<EditorToolbar editor={mockEditor} />);
    const select = screen.getByRole('combobox');
    
    fireEvent.change(select, { target: { value: '2' } });
    
    expect(mockEditor.toggleHeading).toHaveBeenCalledWith({ level: 2 });
    expect(mockEditor.run).toHaveBeenCalled();
  });


  it('opens image dialog when image button is clicked', () => {
    render(<EditorToolbar editor={mockEditor} />);
    const imageButton = screen.getByTitle(/Insert Image/i);
    
    fireEvent.click(imageButton);
    
    // Dialog should open
    expect(screen.getByText('Insert Image')).toBeInTheDocument();
  });

  it('opens link dialog when link button is clicked', () => {
    mockEditor.getAttributes.mockReturnValue({ href: 'https://previous.com' });
    
    render(<EditorToolbar editor={mockEditor} />);
    const linkButton = screen.getByTitle(/Insert Link/i);
    
    fireEvent.click(linkButton);
    
    // Dialog should open with previous URL pre-filled
    expect(screen.getByText('Insert Link')).toBeInTheDocument();
    const urlInput = screen.getByPlaceholderText(/https:\/\/example.com/i);
    expect(urlInput).toHaveValue('https://previous.com');
  });
});
