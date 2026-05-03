// format.js — number / percent / rank formatters.

export const fmt2  = (x) => (x == null || Number.isNaN(+x)) ? "—" : (+x).toFixed(2);
export const fmt1  = (x) => (x == null || Number.isNaN(+x)) ? "—" : (+x).toFixed(1);
export const fmt0  = (x) => (x == null || Number.isNaN(+x)) ? "—" : Math.round(+x).toLocaleString();
export const fmtPct = (x, dp = 1) =>
  (x == null || Number.isNaN(+x)) ? "—" : ((+x) * 100).toFixed(dp) + "%";

export function fmtRank(r, total) {
  if (r == null || Number.isNaN(+r)) return "—";
  return `${Math.round(+r)}` + (total ? ` / ${total}` : "");
}

export function fmtUSDM(x, dp = 1) {
  if (x == null || Number.isNaN(+x)) return "—";
  const v = +x;
  if (Math.abs(v) >= 1e6) return (v / 1e6).toFixed(dp) + " B";
  if (Math.abs(v) >= 1e3) return (v / 1e3).toFixed(dp) + " M";
  return v.toFixed(0);
}
