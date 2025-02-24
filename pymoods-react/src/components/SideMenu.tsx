import { styled } from '@mui/material/styles';
import MuiDrawer, { drawerClasses } from '@mui/material/Drawer';
import Box from '@mui/material/Box';
import { Typography, Select, MenuItem, FormControl, InputLabel } from '@mui/material';
const drawerWidth = 220;

const Drawer = styled(MuiDrawer)({
  width: drawerWidth,
  flexShrink: 0,
  boxSizing: 'border-box',
  mt: 10,
  [`& .${drawerClasses.paper}`]: {
    width: drawerWidth,
    boxSizing: 'border-box',
  },
});

const SidebarSelect = styled(Select)({
  color: 'black',
  backgroundColor: 'white',
  height: '32px',
  '.MuiOutlinedInput-input': {
    padding: '6px 14px',
  },
  '.MuiOutlinedInput-notchedOutline': {
    borderColor: '#f7f7f7',
  },
  '&:hover .MuiOutlinedInput-notchedOutline': {
    borderColor: '#ccc',
  },
  '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
    borderColor: 'white',
  },
  '& .MuiSvgIcon-root': {
    color: '#616265',
  }
});

const SidebarInputLabel = styled(InputLabel)({
  color: 'white',
  position: 'relative',
  fontSize: '14px',
  top: 'unset',
  left: 'unset',
  transform: 'none',
  marginBottom: '4px',
  textAlign: 'left',
  whiteSpace: 'normal',
  overflowWrap: 'break-word',
  '&.Mui-focused': {
    color: 'white',
  }
});

export default function SideMenu() {
  return (
    <Drawer
      variant="permanent"
      sx={{
      display: { xs: 'none', md: 'block' },
      [`& .${drawerClasses.paper}`]: {
        backgroundColor: '#1B293B',
      },
      }}
    >
      <Box
        sx={{
          overflow: 'auto',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* <Button variant="contained">Upload Data</Button> */}
        <Box sx={{ p: 2 }}>
          <Typography variant="h6" sx={{ color: 'white', textAlign: 'left' }}>
            Use Cases
          </Typography>
          <FormControl fullWidth sx={{ mt: 1, minWidth: 120 }} size="small">
            <SidebarInputLabel>
              Select Use Case
            </SidebarInputLabel>
            <SidebarSelect>
              <MenuItem value={10}>Use Case 1</MenuItem>
              <MenuItem value={20}>Use Case 2</MenuItem>
              <MenuItem value={30}>Use Case 3</MenuItem>
            </SidebarSelect >
          </FormControl>
        </Box>

        <Box sx={{ p: 2 }}>
          <Typography variant="h6" sx={{ color: 'white', textAlign: 'left' }}>
            Filters
          </Typography>
          <FormControl fullWidth sx={{ mt: 1, minWidth: 120 }} size="small">
            <SidebarInputLabel sx={{ color: 'white' }}>Battery Technology</SidebarInputLabel>
            <SidebarSelect>
              <MenuItem value={10}>Option 1</MenuItem>
              <MenuItem value={20}>Option 2</MenuItem>
              <MenuItem value={30}>Option 3</MenuItem>
            </SidebarSelect>
          </FormControl>
          <FormControl fullWidth sx={{ mt: 2, minWidth: 120 }} size="small">
            <SidebarInputLabel sx={{ color: 'white' }}>Battery Power Rating (MW)</SidebarInputLabel>
            <SidebarSelect>
              <MenuItem value={10}>Option 1</MenuItem>
              <MenuItem value={20}>Option 2</MenuItem>
              <MenuItem value={30}>Option 3</MenuItem>
            </SidebarSelect>
          </FormControl>
          <FormControl fullWidth sx={{ mt: 2, minWidth: 120 }} size="small">
            <SidebarInputLabel sx={{ color: 'white' }}>Battery Duration (Hours)</SidebarInputLabel>
            <SidebarSelect>
              <MenuItem value={10}>Option 1</MenuItem>
              <MenuItem value={20}>Option 2</MenuItem>
              <MenuItem value={30}>Option 3</MenuItem>
            </SidebarSelect>
          </FormControl>
          <FormControl fullWidth sx={{ mt: 2, minWidth: 120 }} size="small">
            <SidebarInputLabel sx={{ color: 'white' }}>Location</SidebarInputLabel>
            <SidebarSelect>
              <MenuItem value={10}>Option 1</MenuItem>
              <MenuItem value={20}>Option 2</MenuItem>
              <MenuItem value={30}>Option 3</MenuItem>
            </SidebarSelect>
          </FormControl>
        </Box>

        <Box sx={{ p: 2 }}>
          <Typography variant="h6" sx={{ color: 'white', textAlign: 'left' }}>
            Summary
          </Typography>
          {/* Add summary content here */}
        </Box>
      </Box>
    </Drawer>
  );
}