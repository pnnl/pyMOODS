import { useEffect, useRef, useState, KeyboardEvent } from 'react';
import {
  Box,
  CircularProgress,
  Divider,
  IconButton,
  InputAdornment,
  Paper,
  TextField,
  Tooltip,
  Typography,
  useTheme,
  alpha,
} from '@mui/material';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import CloseIcon from '@mui/icons-material/Close';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import SendIcon from '@mui/icons-material/Send';
import { useAgentChat } from '../../hooks/useAgentChat';
import { useDashboardStore } from '../../store/dashboardStore';
import { SIDEBAR_NAVY } from '../../theme';
import type { ChatMessage } from '../../types/agent';

// ---------------------------------------------------------------------------
// Inline markdown renderer
// ---------------------------------------------------------------------------

function MarkdownText({ text, color }: { text: string; color?: string }) {
  // Normalise bullets that the model emits mid-line (". • ") onto their own lines.
  const normalised = text.replace(/([^\n])\s*•\s*/g, '$1\n• ');

  return (
    <Box sx={{ display: 'block', color }}>
      {normalised.split('\n').map((line, li, arr) => {
        const isBullet  = line.trimStart().startsWith('•');
        const isBlank   = line.trim() === '';
        // Extra spacing after a blank line (separates Part 1 from Part 2).
        const prevBlank = li > 0 && arr[li - 1].trim() === '';

        const segments = line.split(/(\*\*[^*]+\*\*)/g);
        const rendered = segments.map((seg, si) =>
          seg.startsWith('**') && seg.endsWith('**')
            ? <strong key={si}>{seg.slice(2, -2)}</strong>
            : <span key={si}>{seg}</span>
        );
        return (
          <Box
            key={li}
            sx={{
              display: isBlank ? 'none' : 'block',
              pl: isBullet ? 1 : 0,
              mt: prevBlank ? 1 : li > 0 ? 0.5 : 0,
              lineHeight: 1.65,
            }}
          >
            {rendered}
          </Box>
        );
      })}
    </Box>
  );
}

// ---------------------------------------------------------------------------
// MessageBubble
// ---------------------------------------------------------------------------

interface MessageBubbleProps {
  message: ChatMessage;
  onSuggestionClick?: (q: string) => void;
}

function MessageBubble({ message, onSuggestionClick: _ }: MessageBubbleProps) {
  const theme = useTheme();
  const isUser  = message.role === 'user';
  const isError = message.role === 'error';

  const bubbleBg = isError
    ? alpha(theme.palette.error.main, 0.08)   // light tint — less alarming than error.light
    : isUser
      ? alpha(theme.palette.primary.main, 0.1)
      : theme.palette.background.paper;

  const borderColor = isError
    ? alpha(theme.palette.error.main, 0.35)
    : isUser
      ? alpha(theme.palette.primary.main, 0.25)
      : theme.palette.divider;

  const labelColor = isError
    ? theme.palette.error.main
    : theme.palette.primary.main;

  // Natural casing — no CSS uppercase
  const senderLabel = isUser ? 'You' : isError ? 'Error' : 'mooCHAT';

  return (
    <Box sx={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start', mb: 1.5 }}>
      {/* Avatar for AI / error messages */}
      {!isUser && (
        <Box
          sx={{
            width: 28,
            height: 28,
            borderRadius: '50%',
            bgcolor: isError ? alpha(theme.palette.error.main, 0.12) : SIDEBAR_NAVY,
            border: isError ? `1.5px solid ${alpha(theme.palette.error.main, 0.4)}` : 'none',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            mr: 1,
            flexShrink: 0,
            mt: 0.3,
          }}
        >
          {isError ? (
            <Typography sx={{ fontSize: '0.78rem', color: theme.palette.error.main, fontWeight: 700, lineHeight: 1 }}>!</Typography>
          ) : (
            <AutoAwesomeIcon sx={{ fontSize: 15, color: '#fff' }} />
          )}
        </Box>
      )}

      <Box
        sx={{
          maxWidth: '78%',
          px: 1.5,
          py: 1,
          borderRadius: isUser ? '14px 14px 4px 14px' : '4px 14px 14px 14px',
          bgcolor: bubbleBg,
          border: `1px solid ${borderColor}`,
          boxShadow: isError ? 'none' : theme.shadows[1],
        }}
      >
        {/* Sender label — natural casing, no uppercase */}
        <Typography
          variant="caption"
          sx={{
            fontWeight: 700,
            fontSize: '0.72rem',
            letterSpacing: 0.3,
            color: labelColor,
          }}
        >
          {senderLabel}
        </Typography>

        <Typography
          variant="body2"
          component="div"
          color={isError ? 'error.main' : 'text.primary'}
          sx={{ mt: 0.25 }}
        >
          <MarkdownText text={message.text} />
        </Typography>

        {import.meta.env.DEV && message.command && (
          <Typography
            variant="caption"
            color="text.disabled"
            sx={{ display: 'block', mt: 0.5, fontFamily: 'monospace', fontSize: '0.62rem' }}
          >
            ⚙ {JSON.stringify(message.command)}
          </Typography>
        )}
      </Box>
    </Box>
  );
}

// ---------------------------------------------------------------------------
// Main panel
// ---------------------------------------------------------------------------

interface AgentChatPanelProps {
  onClose?: () => void;
}

export function AgentChatPanel({ onClose }: AgentChatPanelProps) {
  const theme = useTheme();
  const { chatHistory, isGenerating, submitMessage, initChat, clearChat } = useAgentChat();
  const [inputValue, setInputValue] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  const availableMetadata = useDashboardStore((s) => s.dashboardState.availableMetadata);
  useEffect(() => {
    if (availableMetadata) void initChat();
  }, [availableMetadata]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  const handleSend = () => {
    const text = inputValue.trim();
    if (!text || isGenerating) return;
    setInputValue('');
    void submitMessage(text);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Paper
      elevation={0}
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        borderRadius: `${theme.shape.borderRadius}px`,
        overflow: 'hidden',
        border: `1px solid ${theme.palette.divider}`,
      }}
    >
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <Box
        sx={{
          px: 2,
          py: 1.25,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          bgcolor: SIDEBAR_NAVY,
          color: '#fff',
          flexShrink: 0,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              width: 32,
              height: 32,
              borderRadius: '50%',
              bgcolor: 'rgba(255,255,255,0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <AutoAwesomeIcon sx={{ fontSize: 17, color: '#fff' }} />
          </Box>
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#fff', lineHeight: 1.2 }}>
              mooCHAT
            </Typography>
            <Typography variant="caption" sx={{ opacity: 0.7, fontSize: '0.72rem', color: '#fff' }}>
              AI-powered analysis assistant
            </Typography>
          </Box>
        </Box>

        {/* Header action buttons — clear and close */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.25 }}>
          <Tooltip title="Clear conversation">
            <span>
              <IconButton
                size="small"
                onClick={clearChat}
                disabled={chatHistory.length === 0}
                sx={{
                  color: 'rgba(255,255,255,0.7)',
                  '&:hover': { color: '#fff', bgcolor: 'rgba(255,255,255,0.12)' },
                  '&.Mui-disabled': { color: 'rgba(255,255,255,0.3)' },
                }}
              >
                <DeleteOutlineIcon fontSize="small" />
              </IconButton>
            </span>
          </Tooltip>

          {onClose && (
            <Tooltip title="Close">
              <IconButton
                size="small"
                onClick={onClose}
                sx={{
                  color: 'rgba(255,255,255,0.7)',
                  '&:hover': { color: '#fff', bgcolor: 'rgba(255,255,255,0.12)' },
                }}
              >
                <CloseIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
        </Box>
      </Box>

      <Divider />

      {/* ── Message list ─────────────────────────────────────────────────── */}
      <Box
        sx={{
          flex: 1,
          overflowY: 'auto',
          px: 2,
          py: 2,
          display: 'flex',
          flexDirection: 'column',
          bgcolor: theme.palette.background.default,
        }}
      >
        {chatHistory.length === 0 && (
          <Box sx={{ textAlign: 'center', mt: 6 }}>
            <AutoAwesomeIcon sx={{ fontSize: 32, color: alpha(SIDEBAR_NAVY, 0.2), mb: 1 }} />
            <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.6 }}>
              Ask about your data, apply filters,
              <br />or explore trade-off solutions.
            </Typography>
          </Box>
        )}

        {chatHistory.map((msg) => (
          <MessageBubble
            key={msg.id}
            message={msg}
            onSuggestionClick={(q) => { if (!isGenerating) void submitMessage(q); }}
          />
        ))}

        {isGenerating && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, pl: 0.5, mb: 1 }}>
            <Box
              sx={{
                width: 28,
                height: 28,
                borderRadius: '50%',
                bgcolor: SIDEBAR_NAVY,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
              }}
            >
              <AutoAwesomeIcon sx={{ fontSize: 15, color: '#fff' }} />
            </Box>
            <CircularProgress size={14} thickness={5} sx={{ color: SIDEBAR_NAVY }} />
            <Typography variant="caption" color="text.secondary">
              mooCHAT is thinking…
            </Typography>
          </Box>
        )}

        <div ref={bottomRef} />
      </Box>

      <Divider />

      {/* ── Input row ────────────────────────────────────────────────────── */}
      <Box sx={{ px: 2, py: 1.25, bgcolor: theme.palette.background.paper, flexShrink: 0 }}>
        <TextField
          fullWidth
          size="small"
          multiline
          maxRows={4}
          placeholder="Ask about filters, objectives, or solutions…"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isGenerating}
          sx={{
            '& .MuiOutlinedInput-root': {
              borderRadius: `${theme.shape.borderRadius * 1.5}px`,
              fontSize: '0.875rem',
              '&.Mui-focused fieldset': { borderColor: SIDEBAR_NAVY },
            },
          }}
          slotProps={{
            input: {
              endAdornment: (
                <InputAdornment position="end">
                  <Tooltip title="Send (Enter)">
                    <span>
                      <IconButton
                        edge="end"
                        onClick={handleSend}
                        disabled={!inputValue.trim() || isGenerating}
                        sx={{
                          color: inputValue.trim() && !isGenerating
                            ? SIDEBAR_NAVY
                            : theme.palette.action.disabled,
                        }}
                      >
                        <SendIcon fontSize="small" />
                      </IconButton>
                    </span>
                  </Tooltip>
                </InputAdornment>
              ),
            },
          }}
        />
        <Typography
          variant="caption"
          color="text.disabled"
          sx={{ display: 'block', textAlign: 'center', mt: 0.75, fontSize: '0.65rem' }}
        >
          Powered by PNNL AI Incubator · Enter to send · Shift+Enter for newline
        </Typography>
      </Box>
    </Paper>
  );
}

export default AgentChatPanel;
