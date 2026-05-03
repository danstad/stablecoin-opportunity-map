// router.js — read ?iso3= from the URL into a reactive variable.

export function getIso3() {
  if (typeof window === "undefined") return "HTI";
  const params = new URLSearchParams(window.location.search);
  const v = params.get("iso3");
  return (v || "HTI").toUpperCase();
}

// Build a country-link href consistent with the Quarto output structure.
// Country detail page lives at "country.html"; appending ?iso3= triggers
// the client-side router on load.
export function countryHref(iso3) {
  return `country.html?iso3=${encodeURIComponent(iso3)}`;
}
