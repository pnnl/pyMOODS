import { styled } from "@mui/material/styles";
import AppBar from "@mui/material/AppBar";
import Stack from "@mui/material/Stack";
import MuiToolbar from "@mui/material/Toolbar";
import { tabsClasses } from "@mui/material/Tabs";
import Typography from "@mui/material/Typography";
import {
  Box, Divider} from "@mui/material";

import ECompLogo from "../assets/e-comp-logo.png";
import PNNLLogo from "../assets/pnnl-logo.svg";
// import pyMOODSLogo from "../assets/pymoods-logo-updated.svg";

const Toolbar = styled(MuiToolbar)({
  display: "flex",
  flexDirection: "row",
  alignItems: "center",
  justifyContent: "space-between",
  paddingLeft: 0,
  paddingRight: 0,
  gap: "8px",
  minHeight: 40,
  [`& ${tabsClasses.flexContainer}`]: {
    gap: "8px",
  },
});

export default function AppNavbar() {
  return (
    <AppBar
      position="static"
      elevation={0}
      sx={{
        bgcolor: "background.paper",
        // borderBottom: "1px solid",
        // borderColor: "divider",
        width: "100%",
        paddingLeft: 0,
        paddingRight: 0, 
      }}
    >
      <Toolbar variant="dense" disableGutters sx={{ px: 1, pb: 0, pt: 0, mt: 2, mb: 0, ml: 2, mr: 1 }}>
        <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
        <Box textAlign="left" sx={{ mb: 3 }}>
  <Typography
    variant="h5"
    sx={{
      fontWeight: 600,
      fontSize: "1.6rem",
      color: "text.primary",
      letterSpacing: "0.3px",
      fontFamily: 'Inter, system-ui, Avenir, Helvetica, Arial, sans-serif',
      lineHeight: 1.3,
    }}
  >
    Visual Reasoning for Decision Making
  </Typography>
  <Typography
    variant="subtitle2"
    sx={{
      fontWeight: 400,
      fontSize: "0.95rem",
      color: "text.secondary",
      letterSpacing: "0.25px",
      fontFamily: 'Inter, system-ui, Avenir, Helvetica, Arial, sans-serif',
      mt: 0.5,
      lineHeight: 1.6,
    }}
  >
    Integrated AI-Enabled Platform for Large Scale Electricity Infrastructure Planning
  </Typography>
</Box>

        </Stack>
        <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
          <img src={PNNLLogo} alt="PNNL Logo" style={{ height: "58px" }} />
          <img src={ECompLogo} alt="e-Comp Logo" style={{ height: "58px"}} />
          
        </Stack>
        
      </Toolbar>
      <Divider sx={{ mt: 1 }} />
    </AppBar>
  );
}
