import { styled } from '@mui/material/styles';
import MuiDrawer, { drawerClasses } from '@mui/material/Drawer';
import Box from '@mui/material/Box';
import Divider from '@mui/material/Divider';
import { Typography, Select, MenuItem, FormControl, InputLabel, Input } from '@mui/material';
const drawerWidth = 240;

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
  '.MuiOutlinedInput-notchedOutline': {
    borderColor: '#f7f7f7', // White outline
  },
  '&:hover .MuiOutlinedInput-notchedOutline': {
    borderColor: '#ccc', // Lighter white on hover
  },
  '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
    borderColor: 'white', // White when focused
  },
  '& .MuiSvgIcon-root': {
    color: '#616265', // White dropdown icon
  }
});

const SidebarInputLabel = styled(InputLabel)({
  color: 'white',
  position: 'relative',
  top: 'unset',
  left: 'unset',
  transform: 'none',
  marginBottom: '4px',
  textAlign: 'left',
  paddingLeft: '8px',
  '&.Mui-focused': {
    color: 'white', // Keep the label white when focused
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
          <Typography variant="h6" sx={{ color: 'white' }}>
            Use Cases
          </Typography>
          <FormControl fullWidth sx={{ mt: 2, minWidth: 120 }} size="small">
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

        <Divider sx={{ my: 2 }} />

        <Box sx={{ p: 2 }}>
          <Typography variant="h6" sx={{ color: 'white' }}>
            Filters
          </Typography>
          {[...Array(4)].map((_, index) => (
            <FormControl fullWidth sx={{ mt: 2 }} key={index}>
              <InputLabel sx={{ color: 'white' }}>Filter {index + 1}</InputLabel>
              <Select defaultValue="">
                <MenuItem value={10}>Option 1</MenuItem>
                <MenuItem value={20}>Option 2</MenuItem>
                <MenuItem value={30}>Option 3</MenuItem>
              </Select>
            </FormControl>
          ))}
        </Box>

        <Divider sx={{ my: 2 }} />

        <Box sx={{ p: 2 }}>
          <Typography variant="h6" sx={{ color: 'white' }}>
            Summary
          </Typography>
          {/* Add summary content here */}
        </Box>
      </Box>
      <Divider />
    </Drawer>
  );
}