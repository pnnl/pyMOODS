import { styled } from "@mui/material/styles";
import AppBar from "@mui/material/AppBar";
import Stack from "@mui/material/Stack";
import MuiToolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import { Box } from "@mui/material";
import ECompLogo from "../assets/e-comp-logo.png";
import PNNLLogo from "../assets/pnnl-logo.svg";

const Toolbar = styled(MuiToolbar)({
  justifyContent: "space-between",
});

export default function AppNavbar() {
  return (
    <AppBar
      className="app-navbar"
      position="static"
      elevation={0}
      sx={{
        bgcolor: "background.paper",
        width: "100%",
        borderBottom: "1px solid",
        borderColor: "divider",
      }}
    >
      <Toolbar
        className="app-navbar__toolbar"
        variant="dense"
        disableGutters
        sx={{ px: 1, pt: 1, pb: 1, ml: 2, mr: 1 }}
      >
        <Stack className="app-navbar__title-group" direction="row">
          <Box className="app-navbar__title-block" textAlign="left">
            <Typography
              className="app-navbar__title"
              variant="h6"
              sx={{ fontWeight: 600, fontSize: "1.2rem", color: "text.primary", lineHeight: 1.2 }}
            >
              Visual Reasoning for Decision Making
            </Typography>
            <Typography
              className="app-navbar__subtitle"
              variant="caption"
              noWrap
              sx={{
                fontWeight: 400,
                fontSize: "0.78rem",
                color: "text.secondary",
                display: "block",
                overflow: "hidden",
                textOverflow: "ellipsis",
                maxWidth: "60vw",
              }}
            >
              Integrated AI-Enabled Platform for Large Scale Electricity Infrastructure Planning
            </Typography>
          </Box>
        </Stack>
        <Stack className="app-navbar__logo-group" direction="row" spacing={1} sx={{ alignItems: "center", flexShrink: 0 }}>
          <img src={PNNLLogo} alt="PNNL Logo" style={{ height: "48px" }} />
          <img src={ECompLogo} alt="e-Comp Logo" style={{ height: "48px" }} />
        </Stack>
      </Toolbar>
    </AppBar>
  );
}
