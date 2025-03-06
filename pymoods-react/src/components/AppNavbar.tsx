import { styled } from '@mui/material/styles';
import AppBar from '@mui/material/AppBar';
import Stack from '@mui/material/Stack';
import MuiToolbar from '@mui/material/Toolbar';
import { tabsClasses } from '@mui/material/Tabs';
import Typography from '@mui/material/Typography';

import ECompLogo from '../assets/e-comp-logo.png';
import PNNLLogo from '../assets/pnnl-logo.svg';

const Toolbar = styled(MuiToolbar)({
  width: '100%',
  display: 'flex',
  flexDirection: 'row',
  alignItems: 'center',
  justifyContent: 'space-between',
  gap: '12px',
  flexShrink: 0,
  [`& ${tabsClasses.flexContainer}`]: {
    gap: '8px',
    p: '8px',
    pb: 0,
  },
});

const drawerWidth = 200;
const navbarHeight= 64;

export default function AppNavbar() {
  return (
    <AppBar
        position="fixed"
        sx={{ 
          width: `calc(100% - ${drawerWidth}px)`, 
          height: `${navbarHeight}px`,
          ml: `${drawerWidth}px`,
          boxShadow: 0,
          bgcolor: 'background.paper',
          borderBottom: '1px solid',
          borderColor: 'divider',
          top: 'var(--template-frame-height, 0px)',
        }}
      >
      <Toolbar variant="regular">
        <Typography variant="h5" sx={{ color: 'text.primary' }}>
          pyMOODS Decision Support System
        </Typography>
        <Stack direction="row" spacing={2} sx={{ ml: 'auto', alignItems: 'center', pr: 4.5 }}>
          <img 
            src={PNNLLogo} 
            alt="Logo 1" 
            style={{ height: '48px', width: 'auto' }} 
          />
          <img 
            src={ECompLogo} 
            alt="Logo 2" 
            style={{ height: '48px', width: 'auto' }} 
          />
        </Stack>
      </Toolbar>
    </AppBar>
  );
}
