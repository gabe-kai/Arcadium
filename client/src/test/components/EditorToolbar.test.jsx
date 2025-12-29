import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
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
  addColumnBefore: vi.fn(() => createChainable()),
  addColumnAfter: vi.fn(() => createChainable()),
  deleteColumn: vi.fn(() => createChainable()),
  addRowBefore: vi.fn(() => createChainable()),
  addRowAfter: vi.fn(() => createChainable()),
  deleteRow: vi.fn(() => createChainable()),
  deleteTable: vi.fn(() => createChainable()),
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
    const mockDom = document.createElement('div');
    
    // Track all chainable instances created
    let allChainables = [];
    
    // Create an executable chainable for can() checks (buttons enabled)
    // can() returns a chainable where chain().focus().toggleBold().run() returns true
    const createExecutableCanChain = () => {
      // Create the final chainable where run() returns true
      // This chainable needs all command methods that return itself
      const finalChain = createChainable();
      // Override run() to return true (enables buttons)
      finalChain.run = vi.fn(() => true);
      // All command methods should return finalChain so run() can be called
      finalChain.toggleBold = vi.fn(() => finalChain);
      finalChain.toggleItalic = vi.fn(() => finalChain);
      finalChain.toggleCode = vi.fn(() => finalChain);
      finalChain.toggleBulletList = vi.fn(() => finalChain);
      finalChain.toggleOrderedList = vi.fn(() => finalChain);
      finalChain.toggleCodeBlock = vi.fn(() => finalChain);
      finalChain.undo = vi.fn(() => finalChain);
      finalChain.redo = vi.fn(() => finalChain);
      finalChain.setParagraph = vi.fn(() => finalChain);
      finalChain.toggleHeading = vi.fn(() => finalChain);
      finalChain.addColumnBefore = vi.fn(() => finalChain);
      finalChain.addColumnAfter = vi.fn(() => finalChain);
      finalChain.deleteColumn = vi.fn(() => finalChain);
      finalChain.addRowBefore = vi.fn(() => finalChain);
      finalChain.addRowAfter = vi.fn(() => finalChain);
      finalChain.deleteRow = vi.fn(() => finalChain);
      finalChain.deleteTable = vi.fn(() => finalChain);
      
      // Create the middle chainable with focus() that returns finalChain
      const middleChain = createChainable();
      middleChain.focus = vi.fn(() => finalChain);
      
      // The can() chainable needs chain() method that returns middleChain
      const canChain = createChainable();
      canChain.chain = vi.fn(() => middleChain);
      return canChain;
    };
    
    mockEditor = {
      chain: vi.fn(() => {
        const chainable = createChainable();
        allChainables.push(chainable);
        // Make focus() and all command methods return the same chainable so methods are called on the tracked object
        chainable.focus = vi.fn(() => chainable);
        chainable.toggleBold = vi.fn(() => chainable);
        chainable.toggleItalic = vi.fn(() => chainable);
        chainable.toggleCode = vi.fn(() => chainable);
        chainable.toggleBulletList = vi.fn(() => chainable);
        chainable.toggleOrderedList = vi.fn(() => chainable);
        chainable.toggleCodeBlock = vi.fn(() => chainable);
        chainable.undo = vi.fn(() => chainable);
        chainable.redo = vi.fn(() => chainable);
        chainable.setParagraph = vi.fn(() => chainable);
        chainable.toggleHeading = vi.fn(() => chainable);
        chainable.addColumnBefore = vi.fn(() => chainable);
        chainable.addColumnAfter = vi.fn(() => chainable);
        chainable.deleteColumn = vi.fn(() => chainable);
        chainable.addRowBefore = vi.fn(() => chainable);
        chainable.addRowAfter = vi.fn(() => chainable);
        chainable.deleteRow = vi.fn(() => chainable);
        chainable.deleteTable = vi.fn(() => chainable);
        return chainable;
      }),
      can: vi.fn(() => {
        // can() returns an object that supports both patterns:
        // 1. can().chain().focus().toggleBold().run() for format buttons
        // 2. can().addColumnBefore() for table commands (returns boolean)
        const canChain = createExecutableCanChain();
        // Add direct boolean methods for table commands
        canChain.addColumnBefore = vi.fn(() => true);
        canChain.addColumnAfter = vi.fn(() => true);
        canChain.addRowBefore = vi.fn(() => true);
        canChain.addRowAfter = vi.fn(() => true);
        canChain.deleteColumn = vi.fn(() => true);
        canChain.deleteRow = vi.fn(() => true);
        canChain.deleteTable = vi.fn(() => true);
        return canChain;
      }), // Return chainable with boolean methods for table commands
      isActive: vi.fn(() => false),
      getAttributes: vi.fn((mark) => {
        // Return heading level for format dropdown
        if (mark === 'heading') {
          return { level: null }; // Default to paragraph
        }
        return {};
      }),
      getHTML: vi.fn(() => '<p>Content</p>'),
      state: {
        selection: {
          $anchor: {
            depth: 0,
            node: vi.fn(() => ({ type: { name: 'doc' } })),
          },
        },
      },
      view: {
        dom: mockDom,
      },
      on: vi.fn((event, handler) => {
        // Store handlers for potential manual triggering
        if (!mockEditor._handlers) mockEditor._handlers = {};
        if (!mockEditor._handlers[event]) mockEditor._handlers[event] = [];
        mockEditor._handlers[event].push(handler);
        // For table detection, immediately trigger if conditions are met
        if (event === 'selectionUpdate' || event === 'update' || event === 'focus') {
          setTimeout(() => {
            if (mockEditor.isActive('tableCell') || mockEditor.can().addColumnBefore) {
              handler();
            }
          }, 10);
        }
      }),
      off: vi.fn(),
      _getLastChainable: () => allChainables[allChainables.length - 1], // Helper to get last chainable
      _getAllChainables: () => allChainables, // Helper to get all chainables for debugging
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
    
    // Button should not be disabled
    expect(boldButton).not.toBeDisabled();
    
    fireEvent.click(boldButton);
    
    // The chain should be called
    expect(mockEditor.chain).toHaveBeenCalled();
    // Get the last chainable instance
    const chainable = mockEditor._getLastChainable();
    expect(chainable).toBeTruthy();
    expect(chainable.focus).toHaveBeenCalled();
    expect(chainable.toggleBold).toHaveBeenCalled();
    expect(chainable.run).toHaveBeenCalled();
  });

  it('toggles italic when italic button is clicked', () => {
    render(<EditorToolbar editor={mockEditor} />);
    const italicButton = screen.getByTitle(/Italic/i);
    
    fireEvent.click(italicButton);
    
    const chainable = mockEditor._getLastChainable();
    expect(chainable.toggleItalic).toHaveBeenCalled();
    expect(chainable.run).toHaveBeenCalled();
  });

  it('toggles code when code button is clicked', () => {
    render(<EditorToolbar editor={mockEditor} />);
    const codeButton = screen.getByTitle(/Inline Code/i);
    
    fireEvent.click(codeButton);
    
    const chainable = mockEditor._getLastChainable();
    expect(chainable.toggleCode).toHaveBeenCalled();
    expect(chainable.run).toHaveBeenCalled();
  });

  it('toggles bullet list when bullet list button is clicked', () => {
    render(<EditorToolbar editor={mockEditor} />);
    const bulletButton = screen.getByTitle(/Bullet List/i);
    
    fireEvent.click(bulletButton);
    
    const chainable = mockEditor._getLastChainable();
    expect(chainable.toggleBulletList).toHaveBeenCalled();
    expect(chainable.run).toHaveBeenCalled();
  });

  it('toggles ordered list when numbered list button is clicked', () => {
    render(<EditorToolbar editor={mockEditor} />);
    const numberedButton = screen.getByTitle(/Numbered List/i);
    
    fireEvent.click(numberedButton);
    
    const chainable = mockEditor._getLastChainable();
    expect(chainable.toggleOrderedList).toHaveBeenCalled();
    expect(chainable.run).toHaveBeenCalled();
  });

  it('opens table dialog when table button is clicked', () => {
    render(<EditorToolbar editor={mockEditor} />);
    const tableButton = screen.getByTitle(/Insert Table/i);
    
    fireEvent.click(tableButton);
    
    // Dialog should open - check for dialog heading
    expect(screen.getByRole('heading', { name: /Insert Table/i })).toBeInTheDocument();
  });

  it('shows table controls when cursor is in a table', async () => {
    // Mock table detection - simulate useEffect setting isInTable to true
    // We need to mock can() to return a chainable that indicates table commands are available
    const tableCommandChain = createChainable();
    mockEditor.isActive.mockImplementation((mark) => mark === 'tableCell' || mark === 'tableHeader');
    mockEditor.can.mockImplementation((command) => {
      // Return executable chain for table commands to indicate we're in a table
      if (command === 'addColumnBefore' || command === 'addColumnAfter' || 
          command === 'deleteColumn' || command === 'addRowBefore' || 
          command === 'addRowAfter' || command === 'deleteRow' || 
          command === 'deleteTable') {
        return tableCommandChain;
      }
      return createChainable();
    });
    
    // Mock editor state for node traversal
    mockEditor.state = {
      selection: {
        $anchor: {
          depth: 2,
          node: vi.fn((depth) => {
            if (depth === 2) return { type: { name: 'tableCell' } };
            if (depth === 1) return { type: { name: 'tableRow' } };
            return { type: { name: 'doc' } };
          }),
        },
      },
    };

    render(<EditorToolbar editor={mockEditor} />);
    
    // Wait for useEffect to run and table controls to appear
    // The useEffect will call updateTableState which should detect we're in a table
    await waitFor(() => {
      expect(screen.queryByTitle(/Add Column Before/i)).toBeInTheDocument();
    }, { timeout: 3000 });
    
    // Table controls should appear
    expect(screen.getByTitle(/Add Column Before/i)).toBeInTheDocument();
    expect(screen.getByTitle(/Add Column After/i)).toBeInTheDocument();
    expect(screen.getByTitle(/Delete Column/i)).toBeInTheDocument();
    expect(screen.getByTitle(/Add Row Before/i)).toBeInTheDocument();
    expect(screen.getByTitle(/Add Row After/i)).toBeInTheDocument();
    expect(screen.getByTitle(/Delete Row/i)).toBeInTheDocument();
    expect(screen.getByTitle(/Delete Table/i)).toBeInTheDocument();
  });

  it('hides table controls when cursor is not in a table', async () => {
    mockEditor.isActive.mockReturnValue(false);
    // Mock can() to return an object with chain() method (for format buttons) 
    // and boolean methods for table commands (all returning false)
    // Use the default can() mock and override just the table command methods
    const defaultCan = mockEditor.can();
    defaultCan.addColumnBefore = vi.fn(() => false);
    defaultCan.addColumnAfter = vi.fn(() => false);
    defaultCan.addRowBefore = vi.fn(() => false);
    defaultCan.addRowAfter = vi.fn(() => false);
    mockEditor.can.mockReturnValue(defaultCan);
    
    // Mock editor state - no table in node tree
    mockEditor.state = {
      selection: {
        $anchor: {
          depth: 1,
          node: vi.fn(() => ({ type: { name: 'paragraph' } })),
        },
      },
    };

    render(<EditorToolbar editor={mockEditor} />);
    
    // Wait a bit for useEffect to run
    await waitFor(() => {
      // Table controls should not appear
      expect(screen.queryByTitle(/Add Column Before/i)).toBeNull();
    }, { timeout: 1000 });
  });

  it('calls addColumnBefore when Add Column Before button is clicked', async () => {
    mockEditor.isActive.mockImplementation((mark) => mark === 'tableCell');
    mockEditor.can.mockReturnValue(createChainable());
    
    // Mock editor state for node traversal
    mockEditor.state = {
      selection: {
        $anchor: {
          depth: 2,
          node: vi.fn((depth) => {
            if (depth === 2) return { type: { name: 'tableCell' } };
            return { type: { name: 'doc' } };
          }),
        },
      },
    };

    render(<EditorToolbar editor={mockEditor} />);
    
    // Wait for table controls to appear
    await waitFor(() => {
      expect(screen.queryByTitle(/Add Column Before/i)).toBeInTheDocument();
    }, { timeout: 2000 });
    
    const button = screen.getByTitle(/Add Column Before/i);
    fireEvent.click(button);
    
    const chainable = mockEditor._getLastChainable();
    expect(chainable.focus).toHaveBeenCalled();
    expect(chainable.addColumnBefore).toHaveBeenCalled();
    expect(chainable.run).toHaveBeenCalled();
  });

  it('calls addColumnAfter when Add Column After button is clicked', async () => {
    mockEditor.isActive.mockImplementation((mark) => mark === 'tableCell');
    mockEditor.can.mockReturnValue(createChainable());
    
    mockEditor.state = {
      selection: {
        $anchor: {
          depth: 2,
          node: vi.fn((depth) => {
            if (depth === 2) return { type: { name: 'tableCell' } };
            return { type: { name: 'doc' } };
          }),
        },
      },
    };

    render(<EditorToolbar editor={mockEditor} />);
    
    await waitFor(() => {
      expect(screen.queryByTitle(/Add Column After/i)).toBeInTheDocument();
    }, { timeout: 2000 });
    
    const button = screen.getByTitle(/Add Column After/i);
    fireEvent.click(button);
    
    const chainable = mockEditor._getLastChainable();
    expect(chainable.addColumnAfter).toHaveBeenCalled();
  });

  it('calls deleteColumn when Delete Column button is clicked', async () => {
    mockEditor.isActive.mockImplementation((mark) => mark === 'tableCell');
    mockEditor.can.mockReturnValue(createChainable());
    
    mockEditor.state = {
      selection: {
        $anchor: {
          depth: 2,
          node: vi.fn((depth) => {
            if (depth === 2) return { type: { name: 'tableCell' } };
            return { type: { name: 'doc' } };
          }),
        },
      },
    };

    render(<EditorToolbar editor={mockEditor} />);
    
    await waitFor(() => {
      expect(screen.queryByTitle(/Delete Column/i)).toBeInTheDocument();
    }, { timeout: 2000 });
    
    const button = screen.getByTitle(/Delete Column/i);
    fireEvent.click(button);
    
    const chainable = mockEditor._getLastChainable();
    expect(chainable.deleteColumn).toHaveBeenCalled();
  });

  it('calls addRowBefore when Add Row Before button is clicked', async () => {
    mockEditor.isActive.mockImplementation((mark) => mark === 'tableCell');
    mockEditor.can.mockReturnValue(createChainable());
    
    mockEditor.state = {
      selection: {
        $anchor: {
          depth: 2,
          node: vi.fn((depth) => {
            if (depth === 2) return { type: { name: 'tableCell' } };
            return { type: { name: 'doc' } };
          }),
        },
      },
    };

    render(<EditorToolbar editor={mockEditor} />);
    
    await waitFor(() => {
      expect(screen.queryByTitle(/Add Row Before/i)).toBeInTheDocument();
    }, { timeout: 2000 });
    
    const button = screen.getByTitle(/Add Row Before/i);
    fireEvent.click(button);
    
    const chainable = mockEditor._getLastChainable();
    expect(chainable.addRowBefore).toHaveBeenCalled();
  });

  it('calls addRowAfter when Add Row After button is clicked', async () => {
    mockEditor.isActive.mockImplementation((mark) => mark === 'tableCell');
    mockEditor.can.mockReturnValue(createChainable());
    
    mockEditor.state = {
      selection: {
        $anchor: {
          depth: 2,
          node: vi.fn((depth) => {
            if (depth === 2) return { type: { name: 'tableCell' } };
            return { type: { name: 'doc' } };
          }),
        },
      },
    };

    render(<EditorToolbar editor={mockEditor} />);
    
    await waitFor(() => {
      expect(screen.queryByTitle(/Add Row After/i)).toBeInTheDocument();
    }, { timeout: 2000 });
    
    const button = screen.getByTitle(/Add Row After/i);
    fireEvent.click(button);
    
    const chainable = mockEditor._getLastChainable();
    expect(chainable.addRowAfter).toHaveBeenCalled();
  });

  it('calls deleteRow when Delete Row button is clicked', async () => {
    mockEditor.isActive.mockImplementation((mark) => mark === 'tableCell');
    mockEditor.can.mockReturnValue(createChainable());
    
    mockEditor.state = {
      selection: {
        $anchor: {
          depth: 2,
          node: vi.fn((depth) => {
            if (depth === 2) return { type: { name: 'tableCell' } };
            return { type: { name: 'doc' } };
          }),
        },
      },
    };

    render(<EditorToolbar editor={mockEditor} />);
    
    await waitFor(() => {
      expect(screen.queryByTitle(/Delete Row/i)).toBeInTheDocument();
    }, { timeout: 2000 });
    
    const button = screen.getByTitle(/Delete Row/i);
    fireEvent.click(button);
    
    const chainable = mockEditor._getLastChainable();
    expect(chainable.deleteRow).toHaveBeenCalled();
  });

  it('calls deleteTable when Delete Table button is clicked', async () => {
    mockEditor.isActive.mockImplementation((mark) => mark === 'tableCell');
    mockEditor.can.mockReturnValue(createChainable());
    
    mockEditor.state = {
      selection: {
        $anchor: {
          depth: 2,
          node: vi.fn((depth) => {
            if (depth === 2) return { type: { name: 'tableCell' } };
            return { type: { name: 'doc' } };
          }),
        },
      },
    };

    render(<EditorToolbar editor={mockEditor} />);
    
    await waitFor(() => {
      expect(screen.queryByTitle(/Delete Table/i)).toBeInTheDocument();
    }, { timeout: 2000 });
    
    const button = screen.getByTitle(/Delete Table/i);
    fireEvent.click(button);
    
    const chainable = mockEditor._getLastChainable();
    expect(chainable.deleteTable).toHaveBeenCalled();
  });

  it('disables table control buttons when commands cannot be executed', async () => {
    mockEditor.isActive.mockImplementation((mark) => mark === 'tableCell');
    
    // Mock can() to return an object with chain() method (for format buttons)
    // and boolean methods for table commands
    // Use the default can() mock and override just the table command methods
    const defaultCan = mockEditor.can();
    defaultCan.addColumnBefore = vi.fn(() => false); // Cannot execute - button should be disabled
    defaultCan.addColumnAfter = vi.fn(() => true);
    defaultCan.addRowBefore = vi.fn(() => true);
    defaultCan.addRowAfter = vi.fn(() => true);
    mockEditor.can.mockReturnValue(defaultCan);
    
    // Mock editor state for node traversal
    mockEditor.state = {
      selection: {
        $anchor: {
          depth: 2,
          node: vi.fn((depth) => {
            if (depth === 2) return { type: { name: 'tableCell' } };
            return { type: { name: 'doc' } };
          }),
        },
      },
    };

    render(<EditorToolbar editor={mockEditor} />);
    
    // Wait for table controls to appear (they should appear because canAddRow is true)
    await waitFor(() => {
      expect(screen.queryByTitle(/Add Column Before/i)).toBeInTheDocument();
    }, { timeout: 3000 });
    
    const addColButton = screen.getByTitle(/Add Column Before/i);
    expect(addColButton).toBeDisabled();
  });

  it('shows active state for table button when in table', () => {
    mockEditor.isActive.mockImplementation((mark) => 
      mark === 'tableCell' || mark === 'tableHeader' || mark === 'table'
    );

    render(<EditorToolbar editor={mockEditor} />);
    const tableButton = screen.getByTitle(/Insert Table/i);
    
    expect(tableButton).toHaveClass('arc-editor-toolbar-button-active');
  });

  it('undoes when undo button is clicked', () => {
    render(<EditorToolbar editor={mockEditor} />);
    const undoButton = screen.getByTitle(/Undo/i);
    
    fireEvent.click(undoButton);
    
    const chainable = mockEditor._getLastChainable();
    expect(chainable.undo).toHaveBeenCalled();
    expect(chainable.run).toHaveBeenCalled();
  });

  it('redoes when redo button is clicked', () => {
    render(<EditorToolbar editor={mockEditor} />);
    const redoButton = screen.getByTitle(/Redo/i);
    
    fireEvent.click(redoButton);
    
    const chainable = mockEditor._getLastChainable();
    expect(chainable.redo).toHaveBeenCalled();
    expect(chainable.run).toHaveBeenCalled();
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
    
    const chainable = mockEditor._getLastChainable();
    expect(chainable.setParagraph).toHaveBeenCalled();
    expect(chainable.run).toHaveBeenCalled();
  });

  it('sets heading when format dropdown selects heading level', () => {
    render(<EditorToolbar editor={mockEditor} />);
    const select = screen.getByRole('combobox');
    
    fireEvent.change(select, { target: { value: '2' } });
    
    const chainable = mockEditor._getLastChainable();
    expect(chainable.toggleHeading).toHaveBeenCalledWith({ level: 2 });
    expect(chainable.run).toHaveBeenCalled();
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
    // Check for the dialog title (h3) specifically, not the button text
    const dialogTitle = screen.getByRole('heading', { name: /Insert Link/i });
    expect(dialogTitle).toBeInTheDocument();
    const urlInput = screen.getByPlaceholderText(/https:\/\/example.com/i);
    expect(urlInput).toHaveValue('https://previous.com');
  });
});
