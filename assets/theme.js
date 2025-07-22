// assets/theme.js

window.dash_clientside = window.dash_clientside || {};
window.dash_clientside.theme = {
  // called on both the init‐interval and every Switch.toggle
  setScheme: function(n_intervals, checkedList) {
    //  Detect OS pref
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    //  Pull out the Mantine Switches
    //      at startup checkedList == [false]  (init dummy)
    //      after header renders checkedList == [false, <headerChecked>]
    const dummy = checkedList && checkedList.length>0 ? checkedList[0] : false;
    const headerChecked = checkedList && checkedList.length>1 ? checkedList[1] : null;
    //  Decide which to use: header if user has toggled, else OS
    const useDark = headerChecked !== null ? headerChecked : prefersDark;
    //  Apply straight to the <html> tag so Mantine’s CSS-vars flip
    document.documentElement.setAttribute(
      "data-mantine-color-scheme",
      useDark ? "dark" : "light"
    );
    //  Write back into dcc.Store
    return { color_scheme: useDark ? "dark" : "light" };
  }
};
