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

describe('EditorToolbar', () => {
  let mockEditor;

  beforeEach(() => {
    mockEditor = {
      chain: vi.fn(() => mockEditor),
      focus: vi.fn(() => mockEditor),
      extendMarkRange: vi.fn(() => mockEditor),
      toggleBold: vi.fn(() => mockEditor),
      toggleItalic: vi.fn(() => mockEditor),
      toggleCode: vi.fn(() => mockEditor),
      toggleBulletList: vi.fn(() => mockEditor),
      toggleOrderedList: vi.fn(() => mockEditor),
      toggleCodeBlock: vi.fn(() => mockEditor),
      insertTable: vi.fn(() => mockEditor),
      undo: vi.fn(() => mockEditor),
      redo: vi.fn(() => mockEditor),
      setParagraph: vi.fn(() => mockEditor),
      toggleHeading: vi.fn(() => mockEditor),
      setLink: vi.fn(() => mockEditor),
      unsetLink: vi.fn(() => mockEditor),
      setImage: vi.fn(() => mockEditor),
      run: vi.fn(),
      can: vi.fn(() => mockEditor),
      isActive: vi.fn(() => false),
      getAttributes: vi.fn(() => ({})),
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
    mockEditor.can.mockReturnValue({ chain: () => ({ focus: () => ({ toggleBold: () => ({ run: () => false }) }) }) });
    
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

  it('opens prompt for link URL when link button is clicked', () => {
    const promptSpy = vi.spyOn(window, 'prompt').mockReturnValue('https://example.com');
    
    render(<EditorToolbar editor={mockEditor} />);
    const linkButton = screen.getByTitle(/Insert Link/i);
    
    fireEvent.click(linkButton);
    
    expect(promptSpy).toHaveBeenCalled();
    expect(mockEditor.setLink).toHaveBeenCalledWith({ href: 'https://example.com' });
    expect(mockEditor.run).toHaveBeenCalled();
    
    promptSpy.mockRestore();
  });

  it('removes link when link button is clicked with empty URL', () => {
    const promptSpy = vi.spyOn(window, 'prompt').mockReturnValue('');
    
    render(<EditorToolbar editor={mockEditor} />);
    const linkButton = screen.getByTitle(/Insert Link/i);
    
    fireEvent.click(linkButton);
    
    expect(mockEditor.unsetLink).toHaveBeenCalled();
    expect(mockEditor.run).toHaveBeenCalled();
    
    promptSpy.mockRestore();
  });

  it('does not set link when prompt is cancelled', () => {
    const promptSpy = vi.spyOn(window, 'prompt').mockReturnValue(null);
    
    render(<EditorToolbar editor={mockEditor} />);
    const linkButton = screen.getByTitle(/Insert Link/i);
    
    fireEvent.click(linkButton);
    
    expect(mockEditor.setLink).not.toHaveBeenCalled();
    expect(mockEditor.unsetLink).not.toHaveBeenCalled();
    
    promptSpy.mockRestore();
  });

  it('opens prompt for image URL when image button is clicked', () => {
    const promptSpy = vi.spyOn(window, 'prompt').mockReturnValue('https://example.com/image.jpg');
    
    render(<EditorToolbar editor={mockEditor} />);
    const imageButton = screen.getByTitle(/Insert Image/i);
    
    fireEvent.click(imageButton);
    
    expect(promptSpy).toHaveBeenCalled();
    expect(mockEditor.setImage).toHaveBeenCalledWith({ src: 'https://example.com/image.jpg' });
    expect(mockEditor.run).toHaveBeenCalled();
    
    promptSpy.mockRestore();
  });

  it('does not set image when prompt is cancelled', () => {
    const promptSpy = vi.spyOn(window, 'prompt').mockReturnValue(null);
    
    render(<EditorToolbar editor={mockEditor} />);
    const imageButton = screen.getByTitle(/Insert Image/i);
    
    fireEvent.click(imageButton);
    
    expect(mockEditor.setImage).not.toHaveBeenCalled();
    
    promptSpy.mockRestore();
  });

  it('uses previous URL when setting link', () => {
    mockEditor.getAttributes.mockReturnValue({ href: 'https://previous.com' });
    const promptSpy = vi.spyOn(window, 'prompt').mockReturnValue('https://new.com');
    
    render(<EditorToolbar editor={mockEditor} />);
    const linkButton = screen.getByTitle(/Insert Link/i);
    
    fireEvent.click(linkButton);
    
    expect(promptSpy).toHaveBeenCalledWith('URL', 'https://previous.com');
    
    promptSpy.mockRestore();
  });
});
