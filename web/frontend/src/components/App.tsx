// SpacXT - Professional Spatial Context Intelligence Platform
// Complete redesign with elegant layout and comprehensive spatial context visualization

import React, { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Grid,
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  TextField,
  Button,
  Paper,
  Alert,
  Chip,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  Divider,
  Card,
  CardContent,
  CardHeader,
  Tabs,
  Tab,
  Badge,
  Avatar,
  InputAdornment,
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Psychology as BrainIcon,
  Send as SendIcon,
  Chat as ChatIcon,
  AccountTree as GraphIcon,
  ViewInAr as SceneIcon,
  Timeline as ActivityIcon,
  Hub as RelationsIcon,
  Refresh as RefreshIcon,
  AutoAwesome as SparkleIcon,
} from '@mui/icons-material';
import { ThemeProvider, createTheme } from '@mui/material/styles';

import Scene3D from './Scene3D';
import GraphView2D from './GraphView2D';
import { useWebSocket } from '../hooks/useWebSocket';
import { SpatialAPI } from '../services/api';
import { SpatialObject, CommandResult, QuestionResult } from '../types/spatial';

// Premium dark theme with sophisticated styling
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
    success: { main: '#10b981' },
    warning: { main: '#f59e0b' },
    error: { main: '#ef4444' },
  },
  typography: {
    fontFamily: '"Inter", "SF Pro Display", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    h4: { fontWeight: 700, letterSpacing: '-0.02em' },
    h6: { fontWeight: 600, letterSpacing: '-0.01em' },
    button: { fontWeight: 500, textTransform: 'none' },
  },
  shape: { borderRadius: 12 },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '10px 20px',
          boxShadow: 'none',
          '&:hover': { boxShadow: '0 4px 12px rgba(0, 229, 255, 0.15)' },
        },
        contained: {
          background: 'linear-gradient(135deg, #00e5ff 0%, #0091ea 100%)',
          '&:hover': { background: 'linear-gradient(135deg, #00b2cc 0%, #0277bd 100%)' },
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
            '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(0, 229, 255, 0.5)' },
            '&.Mui-focused .MuiOutlinedInput-notchedOutline': { borderColor: '#00e5ff' },
          },
        },
      },
    },
  },
});

interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  data?: any;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div hidden={value !== index} style={{ height: '100%' }}>
    {value === index && <Box sx={{ height: '100%' }}>{children}</Box>}
  </div>
);

const App: React.FC = () => {
  // Core state
  const [sceneState, setSceneState] = useState<{ objects: Record<string, SpatialObject>; relationships: any[] } | null>(null);
  const [selectedObject, setSelectedObject] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // UI state
  const [activeTab, setActiveTab] = useState(0);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      type: 'system',
      content: '🚀 Welcome to SpacXT! I can help you understand and manipulate spatial contexts using natural language. Try commands like "add a cup on the table" or ask questions like "what objects are near the stove?"',
      timestamp: new Date(),
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [agentActivity, setAgentActivity] = useState<any[]>([]);
  const [spatialRelations, setSpatialRelations] = useState<any[]>([]);

  // WebSocket connection - using a simpler approach for now
  const { connectionStatus } = useWebSocket({
    sessionId: 'default',
    autoConnect: true
  });

  // Load initial scene
  useEffect(() => {
    const loadScene = async () => {
      try {
        const scene = await SpatialAPI.getScene();
        setSceneState(scene);
        setSpatialRelations(scene.relationships || []);
        // Load initial activity logs
        if (scene.activity_logs) {
          setAgentActivity(scene.activity_logs);
        }
      } catch (err) {
        setError('Failed to load scene');
        console.error(err);
      }
    };
    loadScene();
  }, []);

  // Handle message submission
  const handleSendMessage = useCallback(async () => {
    if (!inputMessage.trim() || loading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date(),
    };

    setChatMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);

    try {
      // Determine if it's a question or command
      const isQuestion = inputMessage.includes('?') ||
        inputMessage.toLowerCase().startsWith('what') ||
        inputMessage.toLowerCase().startsWith('where') ||
        inputMessage.toLowerCase().startsWith('how') ||
        inputMessage.toLowerCase().startsWith('which');

      let response: CommandResult | QuestionResult;

      if (isQuestion) {
        response = await SpatialAPI.askQuestion({ question: inputMessage });
      } else {
        response = await SpatialAPI.executeCommand({ command: inputMessage });
      }

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: response.message,
        timestamp: new Date(),
        data: response,
      };

      setChatMessages(prev => [...prev, assistantMessage]);

      // Trigger scene refresh
      const updatedScene = await SpatialAPI.getScene();
      setSceneState(updatedScene);
      setSpatialRelations(updatedScene.relationships || []);

    } catch (err: any) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 2).toString(),
        type: 'system',
        content: `❌ Error: ${err.message || 'Something went wrong'}`,
        timestamp: new Date(),
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  }, [inputMessage, loading]);

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  const runSimulation = async () => {
    try {
      await SpatialAPI.runSimulation();
      // Activity will be automatically logged by the backend and broadcast via WebSocket
    } catch (err) {
      console.error('Simulation failed:', err);
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <Box sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        background: 'radial-gradient(ellipse at top, rgba(0, 229, 255, 0.05) 0%, rgba(10, 14, 26, 1) 50%)',
      }}>
        {/* Header */}
        <AppBar
          position="static"
          sx={{
            background: 'rgba(10, 14, 26, 0.95)',
            backdropFilter: 'blur(20px)',
            borderBottom: '1px solid rgba(148, 163, 184, 0.1)',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.15)',
          }}
        >
          <Toolbar sx={{ px: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mr: 3 }}>
              <Avatar
                sx={{
                  width: 40,
                  height: 40,
                  background: 'linear-gradient(135deg, #00e5ff 0%, #0091ea 100%)',
                  mr: 2,
                  boxShadow: '0 4px 12px rgba(0, 229, 255, 0.3)',
                }}
              >
                <BrainIcon />
              </Avatar>
              <Box>
                <Typography variant="h6" sx={{
                  fontWeight: 700,
                  background: 'linear-gradient(135deg, #00e5ff 0%, #ffffff 100%)',
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}>
                  SpacXT
                </Typography>
                <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                  Spatial Intelligence Platform
                </Typography>
              </Box>
            </Box>

            <Box sx={{ flexGrow: 1 }} />

            <Badge
              color={connectionStatus === 'connected' ? 'success' : 'error'}
              variant="dot"
              sx={{ mr: 2 }}
            >
              <Chip
                label={connectionStatus}
                size="small"
                variant="outlined"
                sx={{ textTransform: 'capitalize' }}
              />
            </Badge>

            <IconButton color="inherit">
              <SettingsIcon />
            </IconButton>
          </Toolbar>
        </AppBar>

        {/* Main Content */}
        <Box sx={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
          <Grid container sx={{ height: '100%' }}>
            {/* Left Panel - Chat Interface */}
            <Grid item xs={12} md={4} sx={{
              borderRight: '1px solid rgba(148, 163, 184, 0.1)',
              display: 'flex',
              flexDirection: 'column',
            }}>
              <Paper sx={{
                m: 2,
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                background: 'rgba(15, 23, 42, 0.98)',
              }}>
                {/* Chat Header */}
                <Box sx={{
                  p: 2,
                  borderBottom: '1px solid rgba(148, 163, 184, 0.1)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 2,
                }}>
                  <ChatIcon sx={{ color: 'primary.main' }} />
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    Spatial Assistant
                  </Typography>
                  <SparkleIcon sx={{ color: 'secondary.main', fontSize: 20 }} />
                </Box>

                {/* Chat Messages */}
                <Box sx={{
                  flex: 1,
                  overflow: 'auto',
                  p: 2,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 2,
                }}>
                  {chatMessages.map((message) => (
                    <Box
                      key={message.id}
                      sx={{
                        display: 'flex',
                        justifyContent: message.type === 'user' ? 'flex-end' : 'flex-start',
                      }}
                    >
                      <Paper
                        sx={{
                          p: 2,
                          maxWidth: '80%',
                          background: message.type === 'user'
                            ? 'linear-gradient(135deg, #00e5ff 0%, #0091ea 100%)'
                            : message.type === 'system'
                            ? 'rgba(59, 130, 246, 0.1)'
                            : 'rgba(30, 41, 59, 0.8)',
                          border: message.type === 'system' ? '1px solid rgba(59, 130, 246, 0.2)' : 'none',
                        }}
                      >
                        <Typography variant="body2" sx={{
                          color: message.type === 'user' ? 'white' : 'text.primary',
                          whiteSpace: 'pre-wrap',
                        }}>
                          {message.content}
                        </Typography>
                        <Typography variant="caption" sx={{
                          color: message.type === 'user' ? 'rgba(255,255,255,0.7)' : 'text.secondary',
                          mt: 1,
                          display: 'block',
                        }}>
                          {message.timestamp.toLocaleTimeString()}
                        </Typography>
                      </Paper>
                    </Box>
                  ))}
                  {loading && (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <CircularProgress size={16} />
                      <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                        Processing...
                      </Typography>
                    </Box>
                  )}
                </Box>

                {/* Chat Input */}
                <Box sx={{ p: 2, borderTop: '1px solid rgba(148, 163, 184, 0.1)' }}>
                  <TextField
                    fullWidth
                    multiline
                    maxRows={3}
                    placeholder="Ask a question or give a command..."
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    disabled={loading}
                    InputProps={{
                      endAdornment: (
                        <InputAdornment position="end">
                          <IconButton
                            onClick={handleSendMessage}
                            disabled={loading || !inputMessage.trim()}
                            sx={{ color: 'primary.main' }}
                          >
                            <SendIcon />
                          </IconButton>
                        </InputAdornment>
                      ),
                    }}
                  />
                </Box>
              </Paper>
            </Grid>

            {/* Right Panel - Visualization */}
            <Grid item xs={12} md={8} sx={{
              display: 'flex',
              flexDirection: 'column',
            }}>
              {/* Visualization Tabs */}
              <Paper sx={{ m: 2, mb: 1 }}>
                <Tabs
                  value={activeTab}
                  onChange={(_, newValue) => setActiveTab(newValue)}
                  sx={{ borderBottom: '1px solid rgba(148, 163, 184, 0.1)' }}
                >
                  <Tab
                    icon={<SceneIcon />}
                    label="3D Scene"
                    iconPosition="start"
                  />
                  <Tab
                    icon={<GraphIcon />}
                    label="Relationship Graph"
                    iconPosition="start"
                  />
                </Tabs>
              </Paper>

              {/* Visualization Content */}
              <Paper sx={{
                m: 2,
                mt: 0,
                flex: 1,
                overflow: 'hidden',
                display: 'flex',
                flexDirection: 'column',
                // Account for the bottom panel height (approximately 180px)
                maxHeight: 'calc(100vh - 280px)',
              }}>
                <TabPanel value={activeTab} index={0}>
                  {sceneState && (
                    <Scene3D
                      objects={Object.values(sceneState.objects)}
                      relationships={sceneState.relationships}
                      selectedObject={selectedObject}
                      onObjectClick={setSelectedObject}
                    />
                  )}
                </TabPanel>
                <TabPanel value={activeTab} index={1}>
                  {sceneState && (
                    <GraphView2D
                      objects={Object.values(sceneState.objects)}
                      relationships={sceneState.relationships}
                      selectedObject={selectedObject}
                      onObjectClick={setSelectedObject}
                    />
                  )}
                </TabPanel>
              </Paper>
            </Grid>
          </Grid>
        </Box>

        {/* Bottom Panel - Spatial Context Information */}
        <Paper sx={{
          m: 2,
          mt: 0,
          background: 'rgba(15, 23, 42, 0.98)',
          minHeight: 160,
          maxHeight: 180,
        }}>
          <Grid container sx={{ height: '100%' }}>
            {/* Spatial Relations */}
            <Grid item xs={12} md={6}>
              <Card sx={{ background: 'transparent', boxShadow: 'none', height: '100%' }}>
                <CardHeader
                  avatar={<RelationsIcon sx={{ color: 'secondary.main' }} />}
                  title="Spatial Relations"
                  titleTypographyProps={{ variant: 'subtitle1', fontWeight: 600 }}
                  action={
                    <IconButton size="small" onClick={runSimulation}>
                      <RefreshIcon />
                    </IconButton>
                  }
                  sx={{ pb: 1 }}
                />
                <CardContent sx={{ pt: 0, pb: 2, maxHeight: 100, overflow: 'auto' }}>
                  {spatialRelations.filter(r => r.type !== 'in').length > 0 ? (
                    <List dense sx={{ py: 0 }}>
                      {spatialRelations.filter(r => r.type !== 'in').slice(0, 3).map((rel, idx) => (
                        <ListItem key={idx} sx={{ py: 0.25, px: 0 }}>
                          <ListItemText
                            primary={`${rel.from} ${rel.type.replace(/_/g, ' ')} ${rel.to}`}
                            secondary={`Confidence: ${(rel.confidence * 100).toFixed(1)}%`}
                            primaryTypographyProps={{ variant: 'body2', fontSize: '0.85rem' }}
                            secondaryTypographyProps={{ variant: 'caption', fontSize: '0.75rem' }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Typography variant="body2" sx={{ color: 'text.secondary', fontStyle: 'italic', fontSize: '0.85rem' }}>
                      No spatial relations detected
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>

            {/* Agent Activity */}
            <Grid item xs={12} md={6}>
              <Card sx={{ background: 'transparent', boxShadow: 'none', height: '100%' }}>
                <CardHeader
                  avatar={<ActivityIcon sx={{ color: 'success.main' }} />}
                  title="Agent Activity"
                  titleTypographyProps={{ variant: 'subtitle1', fontWeight: 600 }}
                  sx={{ pb: 1 }}
                />
                <CardContent sx={{ pt: 0, pb: 2, maxHeight: 100, overflow: 'auto' }}>
                  {agentActivity.length > 0 ? (
                    <List dense sx={{ py: 0 }}>
                      {agentActivity.slice(-3).map((activity, idx) => (
                        <ListItem key={idx} sx={{ py: 0.25, px: 0 }}>
                          <ListItemText
                            primary={activity.message || activity}
                            secondary={activity.timestamp ? new Date(activity.timestamp).toLocaleTimeString() : ''}
                            primaryTypographyProps={{
                              variant: 'body2',
                              fontSize: '0.85rem',
                              color: activity.type === 'error' ? 'error.main' :
                                     activity.type === 'agent' ? 'success.main' :
                                     activity.type === 'command' ? 'primary.main' : 'text.primary'
                            }}
                            secondaryTypographyProps={{ variant: 'caption', fontSize: '0.7rem' }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Typography variant="body2" sx={{ color: 'text.secondary', fontStyle: 'italic', fontSize: '0.85rem' }}>
                      No recent agent activity
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Paper>

        {/* Error Display */}
        {error && (
          <Alert
            severity="error"
            onClose={() => setError(null)}
            sx={{ m: 2, mt: 0 }}
          >
            {error}
          </Alert>
        )}
      </Box>
    </ThemeProvider>
  );
};

export default App;