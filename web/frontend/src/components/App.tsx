// Main SpacXT Web Application Component

import React, { useState, useCallback, useEffect } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  Drawer,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Paper,
  TextField,
  Button,
  IconButton,
  Chip,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControlLabel,
  Switch,
  Grid,
  Card,
  CardContent,
  CardHeader
} from '@mui/material';
import {
  Menu as MenuIcon,
  Send as SendIcon,
  QuestionAnswer as QuestionIcon,
  ViewIn3D as ViewIcon,
  Psychology as BrainIcon,
  Settings as SettingsIcon,
  Refresh as RefreshIcon,
  PlayArrow as PlayIcon,
  Add as AddIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';
import { ThemeProvider, createTheme } from '@mui/material/styles';

import Scene3D from './Scene3D';
import GraphView3D from './GraphView3D';
import { useWebSocket } from '../hooks/useWebSocket';
import { SpatialAPI } from '../services/api';
import { SpatialObject, CommandResult, QuestionResult } from '../types/spatial';

// Premium dark theme with better colors and typography
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#00e5ff',
      light: '#62efff',
      dark: '#00b2cc',
    },
    secondary: {
      main: '#ff6b35',
      light: '#ff9a64',
      dark: '#c53d08',
    },
    background: {
      default: '#0a0e1a',
      paper: 'rgba(15, 23, 42, 0.95)',
    },
    text: {
      primary: '#f8fafc',
      secondary: '#cbd5e1',
    },
    divider: 'rgba(148, 163, 184, 0.12)',
    success: {
      main: '#10b981',
    },
    warning: {
      main: '#f59e0b',
    },
    error: {
      main: '#ef4444',
    },
  },
  typography: {
    fontFamily: '"Inter", "SF Pro Display", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    h4: {
      fontWeight: 700,
      letterSpacing: '-0.02em',
    },
    h6: {
      fontWeight: 600,
      letterSpacing: '-0.01em',
    },
    button: {
      fontWeight: 500,
      textTransform: 'none',
      letterSpacing: '0.01em',
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '10px 20px',
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0 4px 12px rgba(0, 229, 255, 0.15)',
          },
        },
        contained: {
          background: 'linear-gradient(135deg, #00e5ff 0%, #0091ea 100%)',
          '&:hover': {
            background: 'linear-gradient(135deg, #00b2cc 0%, #0277bd 100%)',
          },
        },
        outlined: {
          borderColor: 'rgba(0, 229, 255, 0.3)',
          '&:hover': {
            borderColor: '#00e5ff',
            backgroundColor: 'rgba(0, 229, 255, 0.08)',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: 'rgba(15, 23, 42, 0.95)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(148, 163, 184, 0.1)',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
            backgroundColor: 'rgba(30, 41, 59, 0.5)',
            '&:hover .MuiOutlinedInput-notchedOutline': {
              borderColor: 'rgba(0, 229, 255, 0.5)',
            },
            '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
              borderColor: '#00e5ff',
            },
          },
        },
      },
    },
  },
});

const DRAWER_WIDTH = 420;

interface ChatMessage {
  id: string;
  type: 'command' | 'question' | 'result' | 'error';
  content: string;
  timestamp: Date;
  data?: any;
}

const App: React.FC = () => {
  // State management
  const [drawerOpen, setDrawerOpen] = useState(true);
  const [selectedObject, setSelectedObject] = useState<string>('');
  const [commandInput, setCommandInput] = useState('');
  const [questionInput, setQuestionInput] = useState('');
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [showRelationships, setShowRelationships] = useState(true);
  const [showGrid, setShowGrid] = useState(true);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [currentView, setCurrentView] = useState<'3d' | 'graph' | 'split'>('split');

  // WebSocket connection
  const { sceneState, connectionStatus, error, sendCommand } = useWebSocket({
    sessionId: 'default',
    autoConnect: true
  });

  // Add message to chat
  const addChatMessage = useCallback((message: Omit<ChatMessage, 'id' | 'timestamp'>) => {
    setChatMessages(prev => [...prev, {
      ...message,
      id: Date.now().toString(),
      timestamp: new Date()
    }]);
  }, []);

  // Execute natural language command
  const executeCommand = useCallback(async (command: string) => {
    if (!command.trim()) return;

    setLoading(true);
    addChatMessage({ type: 'command', content: command });

    try {
      const result: CommandResult = await SpatialAPI.executeCommand({ command });

      if (result.success) {
        addChatMessage({
          type: 'result',
          content: result.result || 'Command executed successfully',
          data: result
        });
      } else {
        addChatMessage({
          type: 'error',
          content: result.message || 'Command failed'
        });
      }
    } catch (error) {
      console.error('Command execution error:', error);
      addChatMessage({
        type: 'error',
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`
      });
    } finally {
      setLoading(false);
    }
  }, [addChatMessage]);

  // Ask spatial question
  const askQuestion = useCallback(async (question: string) => {
    if (!question.trim()) return;

    setLoading(true);
    addChatMessage({ type: 'question', content: question });

    try {
      const result: QuestionResult = await SpatialAPI.askQuestion({ question });

      if (result.success) {
        addChatMessage({
          type: 'result',
          content: result.answer,
          data: result
        });
      } else {
        addChatMessage({
          type: 'error',
          content: 'Failed to get answer'
        });
      }
    } catch (error) {
      console.error('Question processing error:', error);
      addChatMessage({
        type: 'error',
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`
      });
    } finally {
      setLoading(false);
    }
  }, [addChatMessage]);

  // Handle command input
  const handleCommandSubmit = useCallback(() => {
    if (commandInput.trim()) {
      executeCommand(commandInput);
      setCommandInput('');
    }
  }, [commandInput, executeCommand]);

  // Handle question input
  const handleQuestionSubmit = useCallback(() => {
    if (questionInput.trim()) {
      askQuestion(questionInput);
      setQuestionInput('');
    }
  }, [questionInput, askQuestion]);

  // Handle object selection
  const handleObjectClick = useCallback((objectId: string) => {
    setSelectedObject(objectId === selectedObject ? '' : objectId);
  }, [selectedObject]);

  // Run simulation step
  const runSimulation = useCallback(async () => {
    try {
      await SpatialAPI.runSimulationStep();
    } catch (error) {
      console.error('Simulation error:', error);
    }
  }, []);

  // Quick command buttons
  const quickCommands = [
    'add a cup on the table',
    'add a book on the chair',
    'move the cup to the stove',
    'What objects are on the table?',
    'What if I remove the table?'
  ];

  return (
    <ThemeProvider theme={theme}>
      <Box sx={{ display: 'flex', height: '100vh' }}>
        {/* App Bar */}
        <AppBar
          position="fixed"
          sx={{
            zIndex: theme.zIndex.drawer + 1,
            background: 'rgba(10, 14, 26, 0.95)',
            backdropFilter: 'blur(20px)',
            borderBottom: '1px solid rgba(148, 163, 184, 0.1)',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.15)',
          }}
        >
          <Toolbar sx={{ px: 3, py: 1 }}>
            <IconButton
              color="inherit"
              edge="start"
              onClick={() => setDrawerOpen(!drawerOpen)}
              sx={{
                mr: 3,
                p: 1.5,
                borderRadius: 2,
                '&:hover': {
                  backgroundColor: 'rgba(0, 229, 255, 0.1)',
                },
              }}
            >
              <MenuIcon />
            </IconButton>

            <Box sx={{ display: 'flex', alignItems: 'center', mr: 3 }}>
              <Box
                sx={{
                  width: 40,
                  height: 40,
                  borderRadius: 2,
                  background: 'linear-gradient(135deg, #00e5ff 0%, #0091ea 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  mr: 2,
                  boxShadow: '0 4px 12px rgba(0, 229, 255, 0.3)',
                }}
              >
                <BrainIcon sx={{ color: 'white', fontSize: 24 }} />
              </Box>
              <Box>
                <Typography
                  variant="h6"
                  component="div"
                  sx={{
                    fontWeight: 700,
                    background: 'linear-gradient(135deg, #00e5ff 0%, #ffffff 100%)',
                    backgroundClip: 'text',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    lineHeight: 1.2,
                  }}
                >
                  SpacXT
                </Typography>
                <Typography
                  variant="caption"
                  sx={{
                    color: theme.palette.text.secondary,
                    fontWeight: 500,
                    letterSpacing: '0.05em',
                  }}
                >
                  Spatial Intelligence
                </Typography>
              </Box>
            </Box>

            <Box sx={{ flexGrow: 1 }} />

            {/* Connection status */}
            <Chip
              label={connectionStatus}
              color={connectionStatus === 'connected' ? 'success' : 'error'}
              size="small"
              sx={{
                mr: 2,
                borderRadius: 2,
                fontWeight: 600,
                fontSize: '0.75rem',
                height: 28,
                '& .MuiChip-label': {
                  px: 1.5,
                },
              }}
            />

            <IconButton
              color="inherit"
              onClick={() => setSettingsOpen(true)}
              sx={{
                p: 1.5,
                borderRadius: 2,
                '&:hover': {
                  backgroundColor: 'rgba(0, 229, 255, 0.1)',
                },
              }}
            >
              <SettingsIcon />
            </IconButton>
          </Toolbar>
        </AppBar>

        {/* Side Drawer */}
        <Drawer
          variant="persistent"
          anchor="left"
          open={drawerOpen}
          sx={{
            width: DRAWER_WIDTH,
            flexShrink: 0,
            '& .MuiDrawer-paper': {
              width: DRAWER_WIDTH,
              boxSizing: 'border-box',
              background: 'rgba(10, 14, 26, 0.98)',
              backdropFilter: 'blur(20px)',
              borderRight: '1px solid rgba(148, 163, 184, 0.1)',
            },
          }}
        >
          <Toolbar />
          <Box sx={{ overflow: 'auto', p: 3 }}>

            {/* Natural Language Commands */}
            <Paper sx={{ p: 3, mb: 3, borderRadius: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2.5 }}>
                <Box
                  sx={{
                    width: 32,
                    height: 32,
                    borderRadius: 2,
                    background: 'linear-gradient(135deg, #00e5ff 0%, #0091ea 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    mr: 2,
                  }}
                >
                  <SendIcon sx={{ color: 'white', fontSize: 18 }} />
                </Box>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Natural Language Commands
                </Typography>
              </Box>
              <TextField
                fullWidth
                variant="outlined"
                placeholder="e.g., add a cup on the table"
                value={commandInput}
                onChange={(e) => setCommandInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleCommandSubmit()}
                disabled={loading}
                sx={{
                  mb: 2.5,
                  '& .MuiOutlinedInput-input': {
                    py: 1.5,
                  },
                }}
              />
              <Button
                fullWidth
                variant="contained"
                onClick={handleCommandSubmit}
                disabled={loading || !commandInput.trim()}
                startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
                sx={{
                  py: 1.5,
                  fontSize: '0.95rem',
                  fontWeight: 600,
                }}
              >
                Execute Command
              </Button>
            </Paper>

            {/* Spatial Questions */}
            <Paper sx={{ p: 3, mb: 3, borderRadius: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2.5 }}>
                <Box
                  sx={{
                    width: 32,
                    height: 32,
                    borderRadius: 2,
                    background: 'linear-gradient(135deg, #ff6b35 0%, #f59e0b 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    mr: 2,
                  }}
                >
                  <QuestionIcon sx={{ color: 'white', fontSize: 18 }} />
                </Box>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Spatial Questions
                </Typography>
              </Box>
              <TextField
                fullWidth
                variant="outlined"
                placeholder="e.g., What objects are on the table?"
                value={questionInput}
                onChange={(e) => setQuestionInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleQuestionSubmit()}
                disabled={loading}
                sx={{
                  mb: 2.5,
                  '& .MuiOutlinedInput-input': {
                    py: 1.5,
                  },
                }}
              />
              <Button
                fullWidth
                variant="outlined"
                onClick={handleQuestionSubmit}
                disabled={loading || !questionInput.trim()}
                startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <QuestionIcon />}
                sx={{
                  py: 1.5,
                  fontSize: '0.95rem',
                  fontWeight: 600,
                  borderColor: 'rgba(255, 107, 53, 0.3)',
                  color: '#ff6b35',
                  '&:hover': {
                    borderColor: '#ff6b35',
                    backgroundColor: 'rgba(255, 107, 53, 0.08)',
                  },
                }}
              >
                Ask Question
              </Button>
            </Paper>

            {/* Quick Actions */}
            <Paper sx={{ p: 3, mb: 3, borderRadius: 3 }}>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 2.5 }}>
                Quick Actions
              </Typography>
              {quickCommands.map((cmd, index) => (
                <Button
                  key={index}
                  fullWidth
                  variant="text"
                  onClick={() => cmd.includes('?') ? askQuestion(cmd) : executeCommand(cmd)}
                  disabled={loading}
                  sx={{
                    mb: 1.5,
                    textTransform: 'none',
                    justifyContent: 'flex-start',
                    py: 1.5,
                    px: 2,
                    borderRadius: 2,
                    fontSize: '0.9rem',
                    color: theme.palette.text.secondary,
                    '&:hover': {
                      backgroundColor: 'rgba(0, 229, 255, 0.08)',
                      color: '#00e5ff',
                    },
                  }}
                >
                  {cmd}
                </Button>
              ))}
            </Paper>

            {/* Scene Controls */}
            <Paper sx={{ p: 3, mb: 3, borderRadius: 3 }}>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 2.5 }}>
                Scene Controls
              </Typography>

              {/* View Mode Selection */}
              <Typography variant="body2" sx={{ mb: 2, color: theme.palette.text.secondary, fontWeight: 500 }}>
                View Mode:
              </Typography>
              <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 1, mb: 3 }}>
                <Button
                  size="small"
                  variant={currentView === '3d' ? 'contained' : 'outlined'}
                  onClick={() => setCurrentView('3d')}
                  sx={{
                    py: 1.2,
                    fontSize: '0.85rem',
                    fontWeight: 600,
                  }}
                >
                  3D Scene
                </Button>
                <Button
                  size="small"
                  variant={currentView === 'graph' ? 'contained' : 'outlined'}
                  onClick={() => setCurrentView('graph')}
                  sx={{
                    py: 1.2,
                    fontSize: '0.85rem',
                    fontWeight: 600,
                  }}
                >
                  Graph
                </Button>
                <Button
                  size="small"
                  variant={currentView === 'split' ? 'contained' : 'outlined'}
                  onClick={() => setCurrentView('split')}
                  sx={{
                    py: 1.2,
                    fontSize: '0.85rem',
                    fontWeight: 600,
                  }}
                >
                  Split
                </Button>
              </Box>

              <Button
                fullWidth
                variant="outlined"
                onClick={runSimulation}
                startIcon={<PlayIcon />}
                sx={{
                  py: 1.5,
                  fontSize: '0.95rem',
                  fontWeight: 600,
                }}
              >
                Run Simulation Step
              </Button>
            </Paper>

            {/* Selected Object Info */}
            {selectedObject && sceneState?.objects[selectedObject] && (
              <Paper sx={{ p: 3, mb: 3, borderRadius: 3, border: '2px solid rgba(0, 229, 255, 0.3)' }}>
                <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, color: '#00e5ff', mb: 2.5 }}>
                  Selected Object
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                  <Box>
                    <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                      ID
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {selectedObject}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                      Type
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 500, textTransform: 'capitalize' }}>
                      {sceneState.objects[selectedObject].type}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                      Position
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 500, fontFamily: 'monospace' }}>
                      [{sceneState.objects[selectedObject].position.map(p => p.toFixed(2)).join(', ')}]
                    </Typography>
                  </Box>
                </Box>
              </Paper>
            )}

          </Box>
        </Drawer>

        {/* Main Content */}
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            transition: theme.transitions.create('margin', {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.leavingScreen,
            }),
            marginLeft: drawerOpen ? 0 : `-${DRAWER_WIDTH}px`,
            background: 'radial-gradient(ellipse at top, rgba(0, 229, 255, 0.05) 0%, rgba(10, 14, 26, 1) 50%)',
            position: 'relative',
          }}
        >
          <Toolbar />

          {error && (
            <Alert
              severity="error"
              sx={{
                m: 3,
                borderRadius: 3,
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid rgba(239, 68, 68, 0.2)',
                '& .MuiAlert-icon': {
                  color: '#ef4444',
                },
              }}
            >
              {error}
            </Alert>
          )}

          {/* Main View Area */}
          <Box sx={{ height: 'calc(100vh - 64px)', display: 'flex' }}>
            {sceneState ? (
              <>
                {/* 3D Scene View */}
                {(currentView === '3d' || currentView === 'split') && (
                  <Box sx={{
                    flex: currentView === 'split' ? 1 : '1 1 100%',
                    height: '100%',
                    borderRight: currentView === 'split' ? '1px solid #333' : 'none'
                  }}>
                    <Scene3D
                      objects={sceneState.objects}
                      relationships={sceneState.relationships}
                      selectedObject={selectedObject}
                      onObjectClick={handleObjectClick}
                      showRelationships={showRelationships}
                      showGrid={showGrid}
                    />
                  </Box>
                )}

                {/* Graph View */}
                {(currentView === 'graph' || currentView === 'split') && (
                  <Box sx={{
                    flex: currentView === 'split' ? 1 : '1 1 100%',
                    height: '100%',
                    position: 'relative'
                  }}>
                    <GraphView3D
                      objects={sceneState.objects}
                      relationships={sceneState.relationships}
                      selectedObject={selectedObject}
                      onObjectClick={handleObjectClick}
                    />

                    {/* Graph View Label */}
                    <Box
                      sx={{
                        position: 'absolute',
                        top: 16,
                        left: 16,
                        background: 'rgba(0,0,0,0.7)',
                        color: 'white',
                        padding: '8px 12px',
                        borderRadius: '4px',
                        fontSize: '14px',
                        fontWeight: 'bold',
                        pointerEvents: 'none'
                      }}
                    >
                      🔗 Spatial Relationship Graph
                    </Box>
                  </Box>
                )}
              </>
            ) : (
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  height: '100%',
                  width: '100%'
                }}
              >
                <CircularProgress size={60} />
                <Typography variant="h6" sx={{ ml: 2 }}>
                  Loading spatial context...
                </Typography>
              </Box>
            )}
          </Box>
        </Box>

        {/* Settings Dialog */}
        <Dialog open={settingsOpen} onClose={() => setSettingsOpen(false)}>
          <DialogTitle>Display Settings</DialogTitle>
          <DialogContent>
            <FormControlLabel
              control={
                <Switch
                  checked={showRelationships}
                  onChange={(e) => setShowRelationships(e.target.checked)}
                />
              }
              label="Show Relationships"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={showGrid}
                  onChange={(e) => setShowGrid(e.target.checked)}
                />
              }
              label="Show Grid"
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setSettingsOpen(false)}>Close</Button>
          </DialogActions>
        </Dialog>
      </Box>
    </ThemeProvider>
  );
};

export default App;
