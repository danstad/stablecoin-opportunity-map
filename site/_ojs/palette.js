// palette.js — color tokens for the Stablecoin Opportunity Map site.
// Use viridis everywhere score-encoded; Set2 for categorical accent (FATF/FDI/AMLD).

export const VIRIDIS = "viridis";

export const COLOR_FATF = "#FC8D62";
export const COLOR_FDI  = "#8DA0CB";
export const COLOR_AMLD = "#66C2A5";

export const SERIF_FONT = "'Source Serif Pro', Georgia, 'Times New Roman', serif";

// Shared Plot configuration block applied via {style: PLOT_STYLE}.
export const PLOT_STYLE = {
  fontFamily: SERIF_FONT,
  fontSize:   "13px",
  background: "transparent",
  color:      "#1a1a1a"
};
