/**
 * D&O Underwriting Dashboard JavaScript
 *
 * Handles Plotly chart loading and htmx fragment re-initialization.
 */

/**
 * Load a Plotly chart from a JSON API endpoint into a DOM element.
 * @param {string} elementId - The DOM element ID for the chart container.
 * @param {string} apiUrl - The URL returning a Plotly JSON spec.
 */
function loadChart(elementId, apiUrl) {
  const el = document.getElementById(elementId);
  if (!el) return;

  fetch(apiUrl)
    .then(function(response) { return response.json(); })
    .then(function(spec) {
      var layout = spec.layout || {};
      layout.autosize = true;
      layout.margin = layout.margin || { l: 40, r: 20, t: 30, b: 40 };

      var config = {
        responsive: true,
        displayModeBar: false,
      };

      Plotly.newPlot(el, spec.data || [], layout, config);
    })
    .catch(function(err) {
      console.warn("Chart load failed for " + elementId + ":", err);
    });
}

/**
 * Find all elements with [data-chart-url] and load their charts.
 */
function loadAllCharts() {
  var chartEls = document.querySelectorAll("[data-chart-url]");
  chartEls.forEach(function(el) {
    var url = el.getAttribute("data-chart-url");
    if (url && el.id) {
      loadChart(el.id, url);
    }
  });
}

// Initialize charts on page load
document.addEventListener("DOMContentLoaded", loadAllCharts);

// Re-initialize charts after htmx swaps new content
document.addEventListener("htmx:afterSwap", function(event) {
  var target = event.detail.target;
  if (target) {
    var charts = target.querySelectorAll("[data-chart-url]");
    charts.forEach(function(el) {
      var url = el.getAttribute("data-chart-url");
      if (url && el.id) {
        loadChart(el.id, url);
      }
    });
  }
});
