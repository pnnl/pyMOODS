import { createTheme } from '@mui/material/styles';

/**
 * Dashboard brand colors.
 * SIDEBAR_NAVY is the dominant brand colour (SideMenu background).
 * Exported so non-MUI components (e.g. the chat header) can reference it
 * without hard-coding the hex string in multiple files.
 */
export const SIDEBAR_NAVY = '#1B293B';

const theme = createTheme({
  palette: {
    primary: {
      // Keep the MUI default blue so existing buttons, tabs, and progress bars
      // are unchanged.
      main: '#1976d2',
    },
    background: {
      default: '#f8f9fa',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: 'Inter, system-ui, Avenir, Helvetica, Arial, sans-serif',
  },
  shape: {
    borderRadius: 8,
  },
});

export default theme;
