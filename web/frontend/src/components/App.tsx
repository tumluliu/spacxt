// SpacXT - Professional Spatial Context Intelligence Platform
// Web experience inspired by the desktop demo to showcase spatial reasoning elegantly

import React, { useState, useCallback, useEffect, useRef, useMemo } from 'react';
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
  Tabs,
  Tab,
  Avatar,
  InputAdornment,
  Tooltip
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Psychology as BrainIcon,
  Chat as ChatIcon,
  Send as SendIcon,
  Hub as RelationsIcon,
  Timeline as TimelineIcon,
  AutoAwesome as SparkleIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  SkipNext as StepIcon,
  RestartAlt as ResetIcon,
  Science as ScienceIcon,
  Tour as TourIcon,
  LocalCafe as CoffeeIcon,
  EventSeat as SeatIcon
} from '@mui/icons-material';
import { ThemeProvider, createTheme } from '@mui/material/styles';

import Scene3D from './Scene3D';
import GraphView2D from './GraphView2D';
import { useWebSocket } from '../hooks/useWebSocket';
import { SpatialAPI } from '../services/api';
import {
  CommandResult,
  QuestionResult,
  SpatialRelationship,
  SceneState
} from '../types/spatial';

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
    info: { main: '#38bdf8' }
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
  data?: CommandResult | QuestionResult;
}

interface TabDefinition {
  id: string;
  label: string;
  title: string;
  subtitle: string;
  icon: React.ElementType;
  iconColor: string;
}

const TAB_CONFIG: TabDefinition[] = [
  {
    id: 'scene',
    label: '3D Scene',
    title: 'Immersive 3D Scene',
    subtitle: 'Orbit, inspect, and select objects to reveal their context',
    icon: SparkleIcon,
    iconColor: 'primary.main'
  },
  {
    id: 'graph',
    label: 'Graph View',
    title: 'Relationship Graph',
    subtitle: 'Force-directed map of spatial dependencies and proximity',
    icon: RelationsIcon,
    iconColor: 'secondary.main'
  }
];

const HEADER_HEIGHT = 84;

const TabPanel: React.FC<{ value: number; index: number; children?: React.ReactNode }> = ({
  value,
  index,
  children
}) => (
  <Box
    role="tabpanel"
    hidden={value !== index}
    sx={{
      flex: 1,
      height: '100%',
      minHeight: 0,
      display: 'flex',
      flexDirection: 'column'
    }}
  >
    {value === index && (
      <Box sx={{ flex: 1, height: '100%', minHeight: 0 }}>
        {children}
      </Box>
    )}
  </Box>
);

const CORE_OBJECTS = new Set(['table_1', 'chair_1', 'stove_1']);

const QUICK_QUESTIONS = [
  { id: 'on-table', label: 'On the table', question: 'What objects are on the table?' },
  { id: 'where-cups', label: 'Where are the cups?', question: 'Where are all the cups in the scene?' },
  { id: 'remove-table', label: 'What if table removed?', question: 'What if I remove the table?' },
  { id: 'reachability', label: 'Reachability', question: 'Which objects can I easily reach?' },
  { id: 'overview', label: 'Scene overview', question: 'Tell me about the overall scene layout.' }
];

const CONNECTION_CHIP_COLOR: Record<'connecting' | 'connected' | 'disconnected' | 'error', 'warning' | 'success' | 'default' | 'error'> = {
  connecting: 'warning',
  connected: 'success',
  disconnected: 'default',
  error: 'error'
};

const createMessageId = () => `${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;

const getWelcomeMessages = (): ChatMessage[] => [
  {
    id: createMessageId(),
    type: 'system',
    content: '🧭 Welcome to SpacXT Web Studio. Orchestrate the spatial context engine with natural language and interactive controls.',
    timestamp: new Date(),
  },
  {
    id: createMessageId(),
    type: 'system',
    content: '💡 Quick start: load the demo scene, trigger a guided Q&A tour, or ask for relationships like "What objects are on the table?"',
    timestamp: new Date(),
  }
];

const App: React.FC = () => {
  const [sceneState, setSceneState] = useState<SceneState | null>(null);
  const [spatialRelations, setSpatialRelations] = useState<SpatialRelationship[]>([]);
  const [agentActivity, setAgentActivity] = useState<SceneState['activity_logs']>([]);
  const [selectedObject, setSelectedObject] = useState<string | undefined>();
  const [activeTab, setActiveTab] = useState(0);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>(() => getWelcomeMessages());
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);

  const chatMessagesEndRef = useRef<HTMLDivElement>(null);
  const simulationIntervalRef = useRef<number>();

  const { sceneState: liveScene, connectionStatus } = useWebSocket({ sessionId: 'default', autoConnect: true });

  const pushSystemMessage = useCallback((content: string) => {
    setChatMessages(prev => [
      ...prev,
      {
        id: createMessageId(),
        type: 'system',
        content,
        timestamp: new Date(),
      }
    ]);
  }, []);

  const refreshScene = useCallback(async () => {
    try {
      const scene = await SpatialAPI.getScene();
      setSceneState(scene);
      setSpatialRelations(scene.relationships || []);
      if (Array.isArray(scene.activity_logs)) {
        setAgentActivity(scene.activity_logs);
      }
    } catch (err) {
      console.error('Failed to load scene', err);
      setError('Failed to load scene');
    }
  }, []);

  useEffect(() => {
    refreshScene();
  }, [refreshScene]);

  useEffect(() => {
    if (liveScene) {
      setSceneState(liveScene);
      setSpatialRelations(liveScene.relationships || []);
      if (Array.isArray(liveScene.activity_logs)) {
        setAgentActivity(liveScene.activity_logs);
      }
    }
  }, [liveScene]);

  useEffect(() => {
    if (chatMessagesEndRef.current) {
      chatMessagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages]);

  useEffect(() => () => {
    if (simulationIntervalRef.current) {
      window.clearInterval(simulationIntervalRef.current);
    }
  }, []);

  const extractAssistantCopy = useCallback((response: CommandResult | QuestionResult): string => {
    if ('answer' in response) {
      const answerPayload = (response as QuestionResult).answer as any;
      if (typeof answerPayload === 'string') {
        return answerPayload;
      }
      if (answerPayload && typeof answerPayload === 'object') {
        if (typeof answerPayload.answer === 'string') {
          return answerPayload.answer;
        }
        if (typeof answerPayload.summary === 'string') {
          return answerPayload.summary;
        }
        return JSON.stringify(answerPayload, null, 2);
      }
    }

    if (typeof (response as CommandResult).message === 'string') {
      return (response as CommandResult).message as string;
    }

    if (typeof (response as CommandResult).result === 'string') {
      return (response as CommandResult).result as string;
    }

    return 'Completed.';
  }, []);

  const processMessage = useCallback(async (
    message: string,
    options: { forceQuestion?: boolean } = {}
  ): Promise<CommandResult | QuestionResult | undefined> => {
    const trimmed = message.trim();
    if (!trimmed || loading) {
      return undefined;
    }

    const userMessage: ChatMessage = {
      id: createMessageId(),
      type: 'user',
      content: trimmed,
      timestamp: new Date(),
    };

    setChatMessages(prev => [...prev, userMessage]);
    setLoading(true);
    setError(null);

    try {
      const lower = trimmed.toLowerCase();
      const isQuestion = options.forceQuestion !== undefined
        ? options.forceQuestion
        : trimmed.includes('?') ||
          lower.startsWith('what') ||
          lower.startsWith('where') ||
          lower.startsWith('how') ||
          lower.startsWith('which');

      let response: CommandResult | QuestionResult;

      response = isQuestion
        ? await SpatialAPI.askQuestion({ question: trimmed })
        : await SpatialAPI.executeCommand({ command: trimmed });

      const assistantContent = extractAssistantCopy(response);

      const assistantMessage: ChatMessage = {
        id: createMessageId(),
        type: 'assistant',
        content: assistantContent,
        timestamp: new Date(),
        data: response,
      };
      setChatMessages(prev => [...prev, assistantMessage]);

      await refreshScene();
      return response;
    } catch (err: any) {
      const messageText = err?.response?.data?.detail || err?.message || 'Something went wrong';
      const errorMessage: ChatMessage = {
        id: createMessageId(),
        type: 'system',
        content: `❌ Error: ${messageText}`,
        timestamp: new Date(),
      };
      setChatMessages(prev => [...prev, errorMessage]);
      setError(messageText);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [loading, refreshScene, extractAssistantCopy]);

  const handleSendMessage = useCallback(async () => {
    const message = inputMessage.trim();
    if (!message || loading) {
      return;
    }
    setInputMessage('');
    try {
      await processMessage(message);
    } catch (err) {
      console.debug('Message processing failed', err);
    }
  }, [inputMessage, loading, processMessage]);

  const handleInputKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      void handleSendMessage();
    }
  };

  const handleClearChat = () => {
    setChatMessages(getWelcomeMessages());
  };

  const runSimulationTick = useCallback(async () => {
    try {
      await SpatialAPI.runSimulationStep();
      await refreshScene();
    } catch (err: any) {
      const messageText = err?.response?.data?.detail || err?.message || 'Simulation failed';
      pushSystemMessage(`⚠️ Simulation update failed: ${messageText}`);
      setError(messageText);
      throw err;
    }
  }, [refreshScene, pushSystemMessage]);

  const handleSimulationStep = useCallback(async () => {
    setActionLoading('step');
    try {
      await runSimulationTick();
    } catch (err) {
      console.debug('Simulation step failed', err);
    } finally {
      setActionLoading(null);
    }
  }, [runSimulationTick]);

  const toggleSimulation = useCallback(async () => {
    if (isSimulating) {
      setIsSimulating(false);
      if (simulationIntervalRef.current) {
        window.clearInterval(simulationIntervalRef.current);
        simulationIntervalRef.current = undefined;
      }
      pushSystemMessage('⏹️ Live negotiation paused.');
      return;
    }

    setIsSimulating(true);
    pushSystemMessage('▶️ Live negotiation engaged. Agents will negotiate every few seconds.');

    try {
      await runSimulationTick();
    } catch (err) {
      console.debug('Initial simulation tick failed', err);
      setIsSimulating(false);
      return;
    }

    simulationIntervalRef.current = window.setInterval(() => {
      runSimulationTick().catch(intervalError => {
        console.error('Simulation tick failed', intervalError);
        pushSystemMessage('⚠️ Simulation paused due to an error.');
        setIsSimulating(false);
        if (simulationIntervalRef.current) {
          window.clearInterval(simulationIntervalRef.current);
          simulationIntervalRef.current = undefined;
        }
      });
    }, 5000);
  }, [isSimulating, runSimulationTick, pushSystemMessage]);

  const handleResetScene = useCallback(async () => {
    if (!sceneState) {
      await refreshScene();
    }

    setActionLoading('reset');
    try {
      const objects = sceneState?.objects || {};
      const extras = Object.keys(objects).filter(id => !CORE_OBJECTS.has(id));

      for (const id of extras) {
        await SpatialAPI.deleteObject(id);
      }

      setSelectedObject(undefined);
      await refreshScene();

      pushSystemMessage(
        extras.length
          ? `🔄 Scene reset: removed ${extras.length} supplemental object${extras.length === 1 ? '' : 's'}.`
          : '🔄 Scene already at base configuration.'
      );
    } catch (err: any) {
      const messageText = err?.response?.data?.detail || err?.message || 'Scene reset failed';
      pushSystemMessage(`❌ Scene reset failed: ${messageText}`);
      setError(messageText);
    } finally {
      setActionLoading(null);
    }
  }, [sceneState, refreshScene, pushSystemMessage]);

  const loadDemoScene = useCallback(async ({ silent = false }: { silent?: boolean } = {}) => {
    if (!silent) {
      setActionLoading('demo');
    }

    try {
      const baseline: SceneState = sceneState ?? await SpatialAPI.getScene();
      const baseObjects = baseline.objects || {};
      const extras = Object.keys(baseObjects).filter(id => !CORE_OBJECTS.has(id));

      for (const id of extras) {
        await SpatialAPI.deleteObject(id);
      }

      const additions = [
        { object_type: 'coffee_cup', target_object: 'table_1', spatial_relation: 'on_top_of' },
        { object_type: 'coffee_cup', target_object: 'table_1', spatial_relation: 'on_top_of' },
        { object_type: 'book', target_object: 'table_1', spatial_relation: 'on_top_of' },
        { object_type: 'lamp', target_object: 'stove_1', spatial_relation: 'near' }
      ];

      for (const addition of additions) {
        await SpatialAPI.createObject({ ...addition, quantity: 1 });
      }

      setSelectedObject(undefined);
      await refreshScene();

      if (!silent) {
        pushSystemMessage('🎬 Demo scene loaded with stacked cups, a book, and an ambient lamp to explore spatial reasoning.');
      }
    } catch (err: any) {
      const messageText = err?.response?.data?.detail || err?.message || 'Unable to load demo scene';
      if (!silent) {
        pushSystemMessage(`❌ Demo scene failed: ${messageText}`);
        setError(messageText);
      }
      throw err;
    } finally {
      if (!silent) {
        setActionLoading(null);
      }
    }
  }, [sceneState, refreshScene, pushSystemMessage]);

  const handleLoadDemoScene = useCallback(async () => {
    try {
      await loadDemoScene();
    } catch (err) {
      console.debug('Demo scene load failed', err);
    }
  }, [loadDemoScene]);

  const handleMoveChair = useCallback(async () => {
    if (loading) {
      return;
    }
    setActionLoading('move-chair');
    try {
      await processMessage('move chair_1 next to table_1', { forceQuestion: false });
    } catch (err) {
      console.debug('Move chair action failed', err);
    } finally {
      setActionLoading(null);
    }
  }, [loading, processMessage]);

  const handleAddCoffeeCup = useCallback(async () => {
    setActionLoading('add-cup');
    try {
      await SpatialAPI.createObject({
        object_type: 'coffee_cup',
        target_object: 'table_1',
        spatial_relation: 'on_top_of',
        quantity: 1
      });
      await refreshScene();
      pushSystemMessage('☕ Added a coffee cup onto table_1. Ask about its relationships!');
    } catch (err: any) {
      const messageText = err?.response?.data?.detail || err?.message || 'Unable to add coffee cup';
      pushSystemMessage(`❌ Action failed: ${messageText}`);
      setError(messageText);
    } finally {
      setActionLoading(null);
    }
  }, [refreshScene, pushSystemMessage]);

  const handleQuickQuestion = useCallback(async (question: string, id: string) => {
    if (loading) {
      return;
    }
    setActionLoading(id);
    try {
      await processMessage(question, { forceQuestion: true });
    } catch (err) {
      console.debug('Quick question failed', err);
    } finally {
      setActionLoading(null);
    }
  }, [loading, processMessage]);

  const handleStartTour = useCallback(async () => {
    if (actionLoading || loading) {
      return;
    }

    setActionLoading('tour');
    try {
      pushSystemMessage('🎯 Starting guided Q&A tour.');
      await loadDemoScene({ silent: true });
      await refreshScene();
      pushSystemMessage('📦 Curated demo scene prepared with cups, a book, and a lamp.');

      const steps = [
        { intro: 'Relationship awareness', question: 'What objects are on the table?' },
        { intro: 'Object localization', question: 'Where are all the cups in the scene?' },
        { intro: 'What-if planning', question: 'What if I remove the table?' },
        { intro: 'Accessibility analysis', question: 'Which objects can I easily reach?' },
        { intro: 'Scene overview', question: 'Tell me about the overall scene layout.' }
      ];

      for (const step of steps) {
        pushSystemMessage(`📍 ${step.intro}`);
        await processMessage(step.question, { forceQuestion: true });
        await new Promise(resolve => setTimeout(resolve, 350));
      }

      pushSystemMessage('🎉 Tour complete. Continue exploring with your own questions or commands.');
    } catch (err: any) {
      const messageText = err?.response?.data?.detail || err?.message || 'Tour interrupted';
      pushSystemMessage(`❌ Tour stopped: ${messageText}`);
      setError(messageText);
    } finally {
      setActionLoading(null);
    }
  }, [actionLoading, loading, loadDemoScene, refreshScene, processMessage, pushSystemMessage]);

  const sceneInsights = useMemo(() => {
    const totalObjects = sceneState ? Object.keys(sceneState.objects || {}).length : 0;
    const relationshipCount = spatialRelations.filter(rel => rel.type !== 'in').length;
    const supportCount = sceneState?.support_relationships?.total_supported_objects
      ?? Object.keys(sceneState?.support_relationships?.support_relationships || {}).length;

    return { totalObjects, relationshipCount, supportCount };
  }, [sceneState, spatialRelations]);

  const featuredRelations = useMemo(() => {
    const baseRelations = spatialRelations.filter(rel => rel.type !== 'in');
    if (selectedObject) {
      const relevant = baseRelations.filter(rel => rel.from === selectedObject || rel.to === selectedObject);
      if (relevant.length > 0) {
        return relevant;
      }
    }
    return baseRelations.slice(-8);
  }, [spatialRelations, selectedObject]);

  const selectedDetails = useMemo(() => {
    if (!selectedObject || !sceneState?.objects?.[selectedObject]) {
      return null;
    }

    const obj = sceneState.objects[selectedObject];
    const supportInfo = sceneState.support_relationships?.support_relationships || {};
    const dependentsInfo = sceneState.support_relationships?.dependents || {};

    return {
      id: obj.id,
      type: obj.type,
      position: obj.position,
      supportedBy: supportInfo[obj.id],
      supporting: dependentsInfo[obj.id] || [],
    };
  }, [selectedObject, sceneState]);

  const activeTabConfig = TAB_CONFIG[activeTab] ?? TAB_CONFIG[0];
  const ActiveTabIcon = activeTabConfig.icon;

  const connectionChipColor = CONNECTION_CHIP_COLOR[connectionStatus] ?? 'default';

  useEffect(() => {
    if (activeTab === 1) {
      const resizeEvent = new Event('resize');
      window.dispatchEvent(resizeEvent);
      const rafId = window.requestAnimationFrame(() => {
        window.dispatchEvent(resizeEvent);
      });
      return () => window.cancelAnimationFrame(rafId);
    }
    return undefined;
  }, [activeTab]);

  return (
    <ThemeProvider theme={theme}>
      <Box sx={{
        minHeight: '100vh',
        background: 'radial-gradient(ellipse at top, rgba(0, 229, 255, 0.05) 0%, rgba(10, 14, 26, 1) 60%)'
      }}>
        <AppBar
          position="fixed"
          sx={{
            top: 0,
            zIndex: (theme) => theme.zIndex.appBar,
            background: 'rgba(10, 14, 26, 0.95)',
            backdropFilter: 'blur(20px)',
            borderBottom: '1px solid rgba(148, 163, 184, 0.1)',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.15)'
          }}
        >
          <Toolbar sx={{ px: { xs: 2, md: 3 }, minHeight: HEADER_HEIGHT }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mr: 3 }}>
              <Avatar
                sx={{
                  width: 44,
                  height: 44,
                  background: 'linear-gradient(135deg, #00e5ff 0%, #0091ea 100%)',
                  mr: 2,
                  boxShadow: '0 4px 12px rgba(0, 229, 255, 0.3)'
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

            <Chip
              label={connectionStatus}
              size="small"
              color={connectionChipColor}
              variant={connectionStatus === 'connected' ? 'filled' : 'outlined'}
              sx={{ textTransform: 'capitalize', mr: 2 }}
            />

            <IconButton color="inherit">
              <SettingsIcon />
            </IconButton>
          </Toolbar>
        </AppBar>
        <Box sx={{ height: HEADER_HEIGHT }} />

        <Box
          sx={{
            height: `calc(100vh - ${HEADER_HEIGHT}px)`,
            display: 'flex',
            flexDirection: 'column',
            overflowX: 'hidden',
            overflowY: 'auto',
            px: { xs: 2, md: 3 },
            pb: 3
          }}
        >
          <Grid container spacing={2} sx={{ mb: 2 }}>
            {[
              { label: 'Objects in Scene', value: sceneInsights.totalObjects, caption: 'Active spatial entities' },
              { label: 'Spatial Links', value: sceneInsights.relationshipCount, caption: 'Contextual relationships' },
              { label: 'Physics Dependents', value: sceneInsights.supportCount, caption: 'Objects relying on support' }
            ].map((stat) => (
              <Grid item xs={12} md={4} key={stat.label}>
                <Paper sx={{ p: 2.5 }}>
                  <Typography variant="overline" sx={{ color: 'text.secondary', letterSpacing: 1.5 }}>
                    {stat.label}
                  </Typography>
                  <Typography variant="h4" sx={{ mt: 0.5 }}>
                    {stat.value}
                  </Typography>
                  <Typography variant="body2" sx={{ color: 'text.secondary', mt: 1 }}>
                    {stat.caption}
                  </Typography>
                </Paper>
              </Grid>
            ))}
          </Grid>

          <Grid
            container
            spacing={2}
            sx={{
              flex: 1,
              minHeight: 0,
              alignItems: 'stretch'
            }}
          >
            <Grid
              item
              xs={12}
              md={8}
              sx={{
                display: 'flex',
                flexDirection: 'column',
                gap: 2,
                minHeight: 0,
                flexShrink: 0
              }}
            >
              <Paper
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  height: { xs: 500, md: '62vh' },
                  maxHeight: 720,
                  overflow: 'hidden'
                }}
              >
                <Box sx={{
                  px: 2.5,
                  pt: 1.5,
                  pb: 0,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 1.5
                }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                    <Box sx={{
                      width: 36,
                      height: 36,
                      borderRadius: '50%',
                      background: 'rgba(0, 229, 255, 0.08)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <ActiveTabIcon sx={{ color: activeTabConfig.iconColor }} />
                    </Box>
                    <Box>
                      <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                        {activeTabConfig.title}
                      </Typography>
                      <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                        {activeTabConfig.subtitle}
                      </Typography>
                    </Box>
                  </Box>
                </Box>

                <Tabs
                  value={activeTab}
                  onChange={(_, next) => setActiveTab(next as number)}
                  sx={{
                    mt: 1,
                    px: 1.5,
                    borderBottom: '1px solid rgba(148, 163, 184, 0.1)',
                    '& .MuiTab-root': { minHeight: 44, fontSize: '0.9rem' }
                  }}
                >
                  {TAB_CONFIG.map((tab, index) => {
                    const Icon = tab.icon;
                    return (
                      <Tab
                        key={tab.id}
                        icon={<Icon fontSize="small" sx={{ color: tab.iconColor }} />}
                        label={tab.label}
                        iconPosition="start"
                        value={index}
                      />
                    );
                  })}
                </Tabs>
                <Divider sx={{ opacity: 0.4 }} />

                <Box sx={{ flex: 1, minHeight: 0, px: 1.5, pb: 1.5 }}>
                  {TAB_CONFIG.map((tab, index) => (
                    <TabPanel key={tab.id} value={activeTab} index={index}>
                      {sceneState ? (
                        index === 0 ? (
                          <Scene3D
                            objects={sceneState.objects}
                            relationships={sceneState.relationships}
                            selectedObject={selectedObject}
                            onObjectClick={setSelectedObject}
                          />
                        ) : (
                      <GraphView2D
                        objects={Object.values(sceneState.objects)}
                        relationships={sceneState.relationships}
                        selectedObject={selectedObject}
                        onObjectClick={setSelectedObject}
                        isActive={activeTab === 1}
                      />
                    )
                  ) : (
                        <Box sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          <CircularProgress />
                        </Box>
                      )}
                    </TabPanel>
                  ))}
                </Box>
              </Paper>
            </Grid>

            <Grid
              item
              xs={12}
              md={4}
              sx={{
                display: 'flex',
                flexDirection: 'column',
                gap: 2,
                minHeight: 0,
                flex: 1
              }}
            >
              <Paper sx={{ p: 2.5 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                  <Box sx={{
                    width: 36,
                    height: 36,
                    borderRadius: '50%',
                    background: 'rgba(0, 229, 255, 0.12)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <PlayIcon sx={{ color: 'primary.main' }} />
                  </Box>
                  <Box>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                      Live Simulation Controls
                    </Typography>
                    <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                      Drive agent negotiations and physics updates
                    </Typography>
                  </Box>
                </Box>

                <Grid container spacing={1}>
                  <Grid item xs={12}>
                    <Button
                      fullWidth
                      variant={isSimulating ? 'outlined' : 'contained'}
                      color={isSimulating ? 'secondary' : 'primary'}
                      startIcon={isSimulating ? <PauseIcon /> : <PlayIcon />}
                      onClick={toggleSimulation}
                    >
                      {isSimulating ? 'Pause Live Negotiation' : 'Start Live Negotiation'}
                    </Button>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Button
                      fullWidth
                      variant="outlined"
                      startIcon={<StepIcon />}
                      onClick={handleSimulationStep}
                      disabled={actionLoading === 'step'}
                    >
                      Single Step
                    </Button>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Button
                      fullWidth
                      variant="outlined"
                      color="secondary"
                      startIcon={<ResetIcon />}
                      onClick={handleResetScene}
                      disabled={actionLoading === 'reset'}
                    >
                      Reset Add-ons
                    </Button>
                  </Grid>
                </Grid>
              </Paper>

              <Paper sx={{ p: 2.5 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                  <Box sx={{
                    width: 36,
                    height: 36,
                    borderRadius: '50%',
                    background: 'rgba(255, 107, 53, 0.12)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <ScienceIcon sx={{ color: 'secondary.main' }} />
                  </Box>
                  <Box>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                      Scene Spotlights
                    </Typography>
                    <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                      Recreate signature demos from the desktop experience
                    </Typography>
                  </Box>
                </Box>

                <Grid container spacing={1}>
                  <Grid item xs={12}>
                    <Button
                      fullWidth
                      variant="contained"
                      startIcon={<ScienceIcon />}
                      onClick={handleLoadDemoScene}
                      disabled={actionLoading === 'demo' || actionLoading === 'tour'}
                    >
                      Load Q&A Demo Scene
                    </Button>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Button
                      fullWidth
                      variant="outlined"
                      startIcon={<SeatIcon />}
                      onClick={handleMoveChair}
                      disabled={loading || actionLoading === 'move-chair'}
                    >
                      Align Chair
                    </Button>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Button
                      fullWidth
                      variant="outlined"
                      startIcon={<CoffeeIcon />}
                      onClick={handleAddCoffeeCup}
                      disabled={actionLoading === 'add-cup'}
                    >
                      Add Coffee Cup
                    </Button>
                  </Grid>
                </Grid>
              </Paper>

              <Paper sx={{
                flex: 1.2,
                display: 'flex',
                flexDirection: 'column',
                minHeight: 0
              }}>
                <Box sx={{
                  px: 2.5,
                  py: 1.5,
                  borderBottom: '1px solid rgba(148, 163, 184, 0.1)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                    <ChatIcon sx={{ color: 'primary.main' }} />
                    <Box>
                      <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                        Spatial Assistant
                      </Typography>
                      <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                        Ask natural language questions or issue commands
                      </Typography>
                    </Box>
                  </Box>
                  <Button size="small" onClick={handleClearChat} disabled={chatMessages.length <= 2}>
                    Clear
                  </Button>
                </Box>

                <Box
                  sx={{
                    flex: 1,
                    overflowY: 'auto',
                    p: 2,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 1.5,
                    minHeight: 0,
                    '&::-webkit-scrollbar': { width: '6px' },
                    '&::-webkit-scrollbar-thumb': {
                      background: 'rgba(148, 163, 184, 0.3)',
                      borderRadius: '3px'
                    }
                  }}
                >
                  {chatMessages.map(message => (
                    <Box
                      key={message.id}
                      sx={{
                        display: 'flex',
                        justifyContent: message.type === 'user' ? 'flex-end' : 'flex-start'
                      }}
                    >
                      <Paper
                        sx={{
                          p: 1.5,
                          maxWidth: '85%',
                          background: message.type === 'user'
                            ? 'linear-gradient(135deg, #00e5ff 0%, #0091ea 100%)'
                            : message.type === 'system'
                            ? 'rgba(59, 130, 246, 0.1)'
                            : 'rgba(30, 41, 59, 0.8)',
                          border: message.type === 'system' ? '1px solid rgba(59, 130, 246, 0.2)' : 'none'
                        }}
                      >
                        <Typography
                          variant="body2"
                          sx={{
                            color: message.type === 'user' ? '#fff' : 'text.primary',
                            whiteSpace: 'pre-wrap',
                            fontSize: '0.9rem',
                            lineHeight: 1.45
                          }}
                        >
                          {message.content}
                        </Typography>
                        <Typography
                          variant="caption"
                          sx={{
                            color: message.type === 'user' ? 'rgba(255,255,255,0.75)' : 'text.secondary',
                            mt: 0.75,
                            display: 'block',
                            fontSize: '0.7rem'
                          }}
                        >
                          {message.timestamp.toLocaleTimeString()}
                        </Typography>
                      </Paper>
                    </Box>
                  ))}
                  {loading && (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, justifyContent: 'center', color: 'text.secondary' }}>
                      <CircularProgress size={16} />
                      <Typography variant="body2">Processing...</Typography>
                    </Box>
                  )}
                  <div ref={chatMessagesEndRef} />
                </Box>

                <Box sx={{
                  borderTop: '1px solid rgba(148, 163, 184, 0.1)',
                  p: 1.5
                }}>
                  <TextField
                    fullWidth
                    multiline
                    minRows={1}
                    maxRows={4}
                    placeholder="Ask a question or give a command..."
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyDown={handleInputKeyDown}
                    disabled={loading}
                    InputProps={{
                      endAdornment: (
                        <InputAdornment position="end">
                          <Tooltip title="Send">
                            <span>
                              <IconButton
                                onClick={() => void handleSendMessage()}
                                disabled={loading || !inputMessage.trim()}
                                sx={{ color: 'primary.main' }}
                              >
                                <SendIcon fontSize="small" />
                              </IconButton>
                            </span>
                          </Tooltip>
                        </InputAdornment>
                      ),
                    }}
                  />
                </Box>
              </Paper>

              <Paper sx={{ p: 2.5 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                    <SparkleIcon sx={{ color: 'info.main' }} />
                    <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                      Guided Q&A
                    </Typography>
                  </Box>
                  <Button
                    size="small"
                    startIcon={<TourIcon />}
                    onClick={handleStartTour}
                    disabled={actionLoading === 'tour' || loading}
                  >
                    Start Tour
                  </Button>
                </Box>

                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                  {QUICK_QUESTIONS.map(item => (
                    <Button
                      key={item.id}
                      variant="outlined"
                      size="small"
                      onClick={() => handleQuickQuestion(item.question, item.id)}
                      disabled={loading || actionLoading === item.id}
                      sx={{ flexGrow: 1 }}
                    >
                      {item.label}
                    </Button>
                  ))}
                </Box>
              </Paper>

              <Paper sx={{
                flex: 0.7,
                display: 'flex',
                flexDirection: 'column',
                minHeight: 0
              }}>
                <Box sx={{
                  px: 2.5,
                  py: 1.5,
                  borderBottom: '1px solid rgba(148, 163, 184, 0.1)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                    <RelationsIcon sx={{ color: 'secondary.main' }} />
                    <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                      Spatial Relationships
                    </Typography>
                  </Box>
                </Box>

                <Box sx={{ px: 2.5, py: 1.5 }}>
                  {selectedDetails ? (
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.75 }}>
                      <Typography variant="body1" sx={{ fontWeight: 600 }}>
                        {selectedDetails.name || selectedDetails.id}
                      </Typography>
                      <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                        Type: {selectedDetails.type}
                      </Typography>
                      <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                        Position: {selectedDetails.position.map(v => v.toFixed(2)).join(', ')}
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 0.5 }}>
                        {selectedDetails.supportedBy && (
                          <Chip
                            size="small"
                            label={`Supported by ${selectedDetails.supportedBy}`}
                            color="success"
                            variant="outlined"
                          />
                        )}
                        {selectedDetails.supporting.length > 0 && (
                          <Chip
                            size="small"
                            label={`Supports ${selectedDetails.supporting.length} object${selectedDetails.supporting.length === 1 ? '' : 's'}`}
                            color="info"
                            variant="outlined"
                          />
                        )}
                      </Box>
                    </Box>
                  ) : (
                    <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                      Select an object in the 3D view or graph to inspect its relationships.
                    </Typography>
                  )}
                </Box>

                <Divider />

                <Box sx={{
                  flex: 1,
                  overflowY: 'auto',
                  px: 2.5,
                  py: 1.5,
                  '&::-webkit-scrollbar': { width: '4px' },
                  '&::-webkit-scrollbar-thumb': {
                    background: 'rgba(148, 163, 184, 0.3)',
                    borderRadius: '2px'
                  }
                }}>
                  {featuredRelations.length > 0 ? (
                    <List dense sx={{ py: 0 }}>
                      {featuredRelations.map((rel, idx) => (
                        <ListItem key={`${rel.from}-${rel.to}-${rel.type}-${idx}`} sx={{ py: 0.35, px: 0 }}>
                          <ListItemText
                            primary={`${rel.from} ${rel.type.replace(/_/g, ' ')} ${rel.to}`}
                            secondary={`Confidence ${(rel.confidence * 100).toFixed(1)}%`}
                            primaryTypographyProps={{ variant: 'body2', fontSize: '0.85rem' }}
                            secondaryTypographyProps={{ variant: 'caption' }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                      No spatial relations detected yet.
                    </Typography>
                  )}
                </Box>
              </Paper>

              <Paper sx={{
                flex: 0.7,
                display: 'flex',
                flexDirection: 'column',
                minHeight: 0
              }}>
                <Box sx={{
                  px: 2.5,
                  py: 1.5,
                  borderBottom: '1px solid rgba(148, 163, 184, 0.1)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                    <TimelineIcon sx={{ color: 'success.main' }} />
                    <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                      Agent Activity
                    </Typography>
                  </Box>
                </Box>

                <Box sx={{
                  flex: 1,
                  overflowY: 'auto',
                  px: 2.5,
                  py: 1.5,
                  '&::-webkit-scrollbar': { width: '4px' },
                  '&::-webkit-scrollbar-thumb': {
                    background: 'rgba(148, 163, 184, 0.3)',
                    borderRadius: '2px'
                  }
                }}>
                  {agentActivity && agentActivity.length > 0 ? (
                    <List dense sx={{ py: 0 }}>
                      {agentActivity.slice(-12).reverse().map((activity, idx) => (
                        <ListItem key={`${activity.timestamp}-${idx}`} sx={{ py: 0.4, px: 0 }}>
                          <ListItemText
                            primary={activity.message}
                            secondary={new Date(activity.timestamp).toLocaleTimeString()}
                            primaryTypographyProps={{
                              variant: 'body2',
                              fontSize: '0.85rem',
                              color:
                                activity.type === 'error'
                                  ? 'error.main'
                                  : activity.type === 'agent'
                                  ? 'success.main'
                                  : activity.type === 'command'
                                  ? 'primary.main'
                                  : activity.type === 'question'
                                  ? 'info.main'
                                  : 'text.primary'
                            }}
                            secondaryTypographyProps={{ variant: 'caption' }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                      Agent negotiations will appear here as you interact with the scene.
                    </Typography>
                  )}
                </Box>
              </Paper>
            </Grid>
          </Grid>

          {error && (
            <Box sx={{ px: { xs: 2, md: 3 }, pb: 3 }}>
              <Alert severity="error" onClose={() => setError(null)}>
                {error}
              </Alert>
            </Box>
          )}
        </Box>
      </Box>
    </ThemeProvider>
  );
};

export default App;
