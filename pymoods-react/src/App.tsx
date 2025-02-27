import Box from '@mui/material/Box';
import AppNavbar from './components/AppNavbar';
import MainGrid from './components/MainGrid';
import SideMenu from './components/SideMenu';

import './App.css'

function App() {

  return (
    <Box sx={{ display: 'flex' }}>
      <SideMenu />
      <AppNavbar />
      {/* Main content */}
      <Box component="main" sx={{ padding: '16px' }}>
        <MainGrid />
      </Box>
    </Box>
  );
}

export default App;
