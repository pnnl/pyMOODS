import { styled } from "@mui/material/styles";
import AppBar from "@mui/material/AppBar";
import Stack from "@mui/material/Stack";
import MuiToolbar from "@mui/material/Toolbar";
import { tabsClasses } from "@mui/material/Tabs";
import Typography from "@mui/material/Typography";

import ECompLogo from "../assets/e-comp-logo.png";
import PNNLLogo from "../assets/pnnl-logo.svg";
import pyMOODSLogo from "../assets/pymoods-logo.svg";

const Toolbar = styled(MuiToolbar)({
  display: "flex",
  flexDirection: "row",
  alignItems: "center",
  justifyContent: "space-between",
  paddingLeft: 0,
  paddingRight: 0,
  gap: "8px",
  minHeight: 48,
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
        borderBottom: "1px solid",
        borderColor: "divider",
      }}
    >
      <Toolbar variant="dense" disableGutters sx={{ px: 1, pb: 1, pt: 1 }}>
        <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
          <img
            src={pyMOODSLogo}
            alt="pyMOODS Logo"
            style={{ height: "56px" }}
          />
          <Typography
            variant="h6"
            sx={{
              fontWeight: 700,
              color: "text.primary",
              letterSpacing: 0.5,
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            pyMOODS Decision Support System
          </Typography>
        </Stack>
        <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
          <img src={PNNLLogo} alt="PNNL Logo" style={{ height: "56px" }} />
          <img src={ECompLogo} alt="e-Comp Logo" style={{ height: "56px" }} />
        </Stack>
      </Toolbar>
    </AppBar>
  );
}
