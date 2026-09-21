/**
 * ProactiveInsightBubble
 *
 * A floating card (bottom-right, above the mooCHAT FAB) that shows a background AI insight.
 * Counts down with a LinearProgress bar and fades out automatically.
 * Clicking it opens the chat panel (the insight is already in chat history).
 */

import { useEffect, useRef, useState } from 'react';
import { Box, Card, CardActionArea, LinearProgress, Typography, alpha, useTheme } from '@mui/material';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import { useDashboardStore } from '../../store/dashboardStore';
import { SIDEBAR_NAVY } from '../../theme';

const DURATION_MS = 8_000;
const TICK_MS     = 50;
const MAX_LINES   = 3;

/** Strip markdown bold markers and collapse to a readable single preview line. */
function toPlainPreview(text: string): string {
  return text
    .split('\n')
    .map((l) => l.replace(/\*\*/g, '').trim())
    .filter(Boolean)
    .slice(0, MAX_LINES)
    .join('  ·  ');
}

interface Props {
  onOpenChat: () => void;
}

export function ProactiveInsightBubble({ onOpenChat }: Props) {
  const theme = useTheme();
  const { proactiveBubble, setProactiveBubble } = useDashboardStore();

  const [progress, setProgress] = useState(100);
  const [leaving, setLeaving]   = useState(false);

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const bubbleIdRef = useRef<string | null>(null);

  const dismiss = () => {
    setLeaving(true);
    setTimeout(() => {
      setProactiveBubble(null);
      setLeaving(false);
    }, 280);
  };

  const handleClick = () => {
    onOpenChat();
    dismiss();
  };

  useEffect(() => {
    if (!proactiveBubble) return;

    if (proactiveBubble.id !== bubbleIdRef.current) {
      bubbleIdRef.current = proactiveBubble.id;
      setProgress(100);
      setLeaving(false);
      if (intervalRef.current) clearInterval(intervalRef.current);
    }

    const step = (TICK_MS / DURATION_MS) * 100;
    intervalRef.current = setInterval(() => {
      setProgress((prev) => {
        const next = prev - step;
        if (next <= 0) {
          clearInterval(intervalRef.current!);
          dismiss();
          return 0;
        }
        return next;
      });
    }, TICK_MS);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [proactiveBubble?.id]);

  if (!proactiveBubble) return null;

  const preview = toPlainPreview(proactiveBubble.text);

  return (
    <Box
      sx={{
        position: 'fixed',
        // Sit just above the FAB: FAB bottom (28) + FAB height (~48) + gap (12) = 88
        bottom: 88,
        right: 24,
        zIndex: 1300,
        width: 300,
        animation: leaving
          ? 'bubbleOut 0.28s ease-in forwards'
          : 'bubbleIn 0.32s cubic-bezier(0.34,1.56,0.64,1) forwards',
        '@keyframes bubbleIn': {
          from: { opacity: 0, transform: 'translateY(14px) scale(0.94)' },
          to:   { opacity: 1, transform: 'translateY(0)    scale(1)'    },
        },
        '@keyframes bubbleOut': {
          from: { opacity: 1, transform: 'translateY(0)    scale(1)'    },
          to:   { opacity: 0, transform: 'translateY(10px) scale(0.96)' },
        },
      }}
    >
      <Card
        elevation={0}
        sx={{
          borderRadius: 3,
          overflow: 'hidden',
          border: `1px solid ${alpha(SIDEBAR_NAVY, 0.14)}`,
          boxShadow: [
            `0 2px 6px ${alpha(SIDEBAR_NAVY, 0.06)}`,
            `0 8px 24px ${alpha(SIDEBAR_NAVY, 0.16)}`,
            `0 20px 48px ${alpha(SIDEBAR_NAVY, 0.08)}`,
          ].join(', '),
        }}
      >
        <CardActionArea onClick={handleClick} sx={{ p: 0 }}>

          {/* ── Header ─────────────────────────────────────────────── */}
          <Box
            sx={{
              px: 1.5,
              py: 1,
              background: `linear-gradient(120deg, ${SIDEBAR_NAVY} 0%, #1a3d72 100%)`,
              display: 'flex',
              alignItems: 'center',
              gap: 1,
            }}
          >
            {/* Icon with soft pulse ring */}
            <Box
              sx={{
                width: 28,
                height: 28,
                borderRadius: '50%',
                bgcolor: alpha('#fff', 0.1),
                border: `1px solid ${alpha('#fff', 0.18)}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                '@keyframes iconPulse': {
                  '0%, 100%': { boxShadow: `0 0 0 0 ${alpha('#fff', 0)}` },
                  '50%':      { boxShadow: `0 0 0 5px ${alpha('#fff', 0.1)}` },
                },
                animation: 'iconPulse 2.8s ease-in-out infinite',
              }}
            >
              <AutoAwesomeIcon sx={{ fontSize: 13, color: '#fff' }} />
            </Box>

            <Box sx={{ flex: 1, minWidth: 0 }}>
              <Typography sx={{ fontSize: '0.75rem', fontWeight: 700, color: '#fff', letterSpacing: 0.5, lineHeight: 1.25 }}>
                mooCHAT
              </Typography>
              <Typography sx={{ fontSize: '0.62rem', color: alpha('#fff', 0.6), letterSpacing: 0.2, lineHeight: 1.1 }}>
                new insight
              </Typography>
            </Box>

            {/* Remaining-time ring */}
            <Box sx={{ position: 'relative', width: 22, height: 22, flexShrink: 0 }}>
              <Box
                component="svg"
                viewBox="0 0 22 22"
                sx={{ position: 'absolute', inset: 0, transform: 'rotate(-90deg)' }}
              >
                <circle cx="11" cy="11" r="9" fill="none" stroke={alpha('#fff', 0.15)} strokeWidth="2" />
                <circle
                  cx="11" cy="11" r="9"
                  fill="none"
                  stroke={alpha('#fff', 0.55)}
                  strokeWidth="2"
                  strokeDasharray={`${2 * Math.PI * 9}`}
                  strokeDashoffset={`${2 * Math.PI * 9 * (1 - progress / 100)}`}
                  strokeLinecap="round"
                  style={{ transition: 'stroke-dashoffset 0.05s linear' }}
                />
              </Box>
            </Box>
          </Box>

          {/* ── Body ───────────────────────────────────────────────── */}
          <Box
            sx={{
              px: 1.75,
              py: 1.25,
              background: theme.palette.mode === 'dark'
                ? theme.palette.background.paper
                : `linear-gradient(180deg, #ffffff 0%, #f8fafd 100%)`,
            }}
          >
            <Typography
              variant="body2"
              sx={{
                fontSize: '0.8rem',
                lineHeight: 1.6,
                color: 'text.primary',
                display: '-webkit-box',
                WebkitLineClamp: MAX_LINES,
                WebkitBoxOrient: 'vertical',
                overflow: 'hidden',
              }}
            >
              {preview}
            </Typography>

            <Box sx={{ display: 'flex', alignItems: 'center', mt: 1, gap: 0.5 }}>
              <Typography variant="caption" sx={{ color: alpha(SIDEBAR_NAVY, 0.45), fontSize: '0.67rem', flex: 1 }}>
                Tap to open mooCHAT
              </Typography>
              <Typography variant="caption" sx={{ color: alpha(SIDEBAR_NAVY, 0.45), fontSize: '0.67rem' }}>
                ↗
              </Typography>
            </Box>
          </Box>
        </CardActionArea>

        {/* Thin countdown strip at bottom */}
        <LinearProgress
          variant="determinate"
          value={progress}
          sx={{
            height: 2,
            bgcolor: alpha(SIDEBAR_NAVY, 0.06),
            '& .MuiLinearProgress-bar': { bgcolor: alpha(SIDEBAR_NAVY, 0.35), transition: 'none' },
          }}
        />
      </Card>

    </Box>
  );
}

export default ProactiveInsightBubble;
