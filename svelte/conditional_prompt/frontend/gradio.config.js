import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const deepmergeShimPath = path
  .resolve(__dirname, "shims/deepmerge-esm.js")
  .replace(/\\/g, "/");

const unresolvedConfigPattern =
  /<script>\s*window\.gradio_config\s*=\s*\{\{\s*config\s*\|\s*toorjson\s*\}\};\s*<\/script>\s*<script>\s*window\.gradio_api_info\s*=\s*\{\{\s*gradio_api_info\s*\|\s*toorjson\s*\}\};\s*<\/script>/m;

const gradioTemplateGlobalsPlugin = {
  name: "gradio-template-globals-fix",
  enforce: "pre",
  transformIndexHtml(html) {
    if (!html.includes("{{ config | toorjson }}")) {
      return html;
    }

    const replacement = `<script>
(function () {
  var port = window.__GRADIO__SERVER_PORT__ || 7860;
  var host = window.location.hostname || "127.0.0.1";
  var base = window.location.protocol + "//" + host + ":" + port;
  function getJson(path, fallback) {
    try {
      var xhr = new XMLHttpRequest();
      xhr.open("GET", base + path, false);
      xhr.send(null);
      if (xhr.status >= 200 && xhr.status < 300 && xhr.responseText) {
        return JSON.parse(xhr.responseText);
      }
    } catch (e) {}
    return fallback;
  }
  window.gradio_config = getJson("/config", {});
  window.gradio_api_info = getJson("/info", {
    named_endpoints: {},
    unnamed_endpoints: {}
  });
})();
</script>`;

    return html.replace(unresolvedConfigPattern, replacement);
  }
};

const deepmergeEsmShimPlugin = {
  name: "deepmerge-esm-shim",
  enforce: "pre",
  resolveId(source) {
    if (source === "deepmerge") {
      return deepmergeShimPath;
    }
    return null;
  }
};

export default {
  plugins: [gradioTemplateGlobalsPlugin, deepmergeEsmShimPlugin],
  svelte: {
    preprocess: [],
  },
  build: {
    target: "modules",
  },
  optimizeDeps: {},
};